"""Corpus pipeline: discover -> screen -> snowball -> build master table.

Usage:  python pipeline.py discover|screen|snowball|build|all
Reads ../config.json. Caches every response under ../data/raw/. Writes ../data/clean/.
Sources (all free, no key): Semantic Scholar bulk search + batch (backbone: merges preprint and
published versions, supplies reference lists), arXiv API, ACL Anthology BibTeX export, Crossref,
DBLP (attempted), OpenAlex single-work lookups (affiliations, countries, topics, keywords).
"""
import csv
import gzip
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

from bm_common import (BASE, CLEAN, RAW, TOOLS, MAIL, OAStore, SESSION, arxiv_from_doi, au_short,
                       ascii_upper, cached_fetch, load_config, log, norm_doi, norm_title, qhash,
                       s2_batch, s2_bulk, s2_citations, S2_LIGHT)

CFG = load_config()
TERMS = CFG.get("terms", {})
YMIN, YMAX = CFG["year_min"], CFG["year_max"]


def sub(s):
    for _ in range(3):
        for k, v in TERMS.items():
            s = s.replace("{" + k + "}", v)
    return s


class Group:
    """One AND-group of a rule. A pattern written with the prefix 'T:' must match in the title."""
    def __init__(self, pat):
        self.title_only = pat.startswith("T:")
        self.rx = re.compile(sub(pat[2:] if self.title_only else pat), re.I)

    def search(self, text, title=None):
        return self.rx.search(title if (self.title_only and title is not None) else text)


def compiled_rules():
    out = {}
    for code, sl in CFG["sublits"].items():
        alts = sl.get("rule_any") or [sl["rule"]]
        out[code] = [[Group(g) for g in alt] for alt in alts]
    return out


RULES = compiled_rules()
EXCL = [re.compile(sub(x), re.I) for x in CFG.get("exclude_title_regex", [])]
EXCL_ALL = [re.compile(sub(x), re.I) for x in CFG.get("exclude_text_regex", [])]
KEEP_IF = set(CFG.get("exclude_unless_sublit", ["B", "C"]))


def screen_text(title, abstract):
    """Returns (sublit codes, reason). Empty list = excluded by rule."""
    title = re.sub(r"\(\s*preprint\s*\)", " ", title or "", flags=re.I)   # publisher suffix, not content
    text = f"{title or ''} . {abstract or ''}"
    codes = [c for c, alts in RULES.items() if any(all(g.search(text, title or "") for g in alt) for alt in alts)]
    if not codes:
        return [], "no sub-literature rule matched"
    t = title or ""
    if EXCL and EXCL[0].search(t.strip()):
        return [], "E1 front matter / non-paper"
    for rx in EXCL[1:]:
        if rx.search(t) and not (set(codes) & KEEP_IF):
            return [], "E2 out-of-scope modality or topic (title)"
    for rx in EXCL_ALL:
        if rx.search(text):
            return [], "E3 out-of-scope topic (text)"
    return codes, ""


def jl_write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def jl_read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def from_s2(p, src, tag):
    ext = p.get("externalIds") or {}
    return {"s2id": p.get("paperId"), "doi": norm_doi(ext.get("DOI")), "arxiv": ext.get("ArXiv") or "",
            "acl": ext.get("ACL") or "", "title": p.get("title") or "", "abstract": p.get("abstract") or "",
            "year": p.get("year"), "venue": p.get("venue") or "",
            "authors": [a.get("name") for a in (p.get("authors") or []) if a.get("name")],
            "cit": p.get("citationCount"), "src": src, "q": tag}


# ------------------------------------------------------------------ discover
def discover_s2():
    rows, counts = [], {}
    for code, sl in CFG["sublits"].items():
        for i, q in enumerate(sl.get("s2_queries", [])):
            q2 = sub(q)
            total, recs = s2_bulk(q2, year=f"{YMIN}-{YMAX}", fos=CFG.get("s2_fields_of_study"),
                                  cap=CFG.get("s2_cap", 6000), tag=f"{code}{i}")
            log(f"[s2] {code}{i}: total={total} fetched={len(recs)}")
            counts[f"{code}{i}"] = {"query": q2, "total_reported": total, "fetched": len(recs)}
            rows += [from_s2(p, "semantic_scholar", code) for p in recs]
    jl_write(os.path.join(RAW, "candidates_s2.jsonl"), rows)
    return counts


def discover_arxiv():
    rows, counts = [], {}
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for code, sl in CFG["sublits"].items():
        for i, q in enumerate(sl.get("arxiv_queries", [])):
            n_q, start, per = 0, 0, 200
            total = None
            while start < CFG.get("arxiv_cap", 1000):
                txt = cached_fetch("http://export.arxiv.org/api/query", f"arxiv/{code}{i}_{qhash(q)}_s{start}.xml.gz",
                                   params={"search_query": q, "start": start, "max_results": per,
                                           "sortBy": "relevance"},
                                   host="arxiv", min_gap=6.0, retries=6, as_json=False, backoff=15)
                if not txt:
                    break
                try:
                    root = ET.fromstring(txt)
                except Exception:
                    log("[arxiv] XML parse failed", code, i, start)
                    break
                tr = root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults")
                total = int(tr.text) if tr is not None else total
                ents = root.findall("a:entry", ns)
                for e in ents:
                    aid = e.find("a:id", ns).text.rsplit("/abs/", 1)[-1]
                    aid = re.sub(r"v\d+$", "", aid)
                    doi_el = e.find("{http://arxiv.org/schemas/atom}doi")
                    rows.append({"s2id": "", "doi": norm_doi(doi_el.text) if doi_el is not None else "",
                                 "arxiv": aid, "acl": "",
                                 "title": re.sub(r"\s+", " ", e.find("a:title", ns).text or "").strip(),
                                 "abstract": re.sub(r"\s+", " ", e.find("a:summary", ns).text or "").strip(),
                                 "year": int(e.find("a:published", ns).text[:4]), "venue": "arXiv.org",
                                 "authors": [x.find("a:name", ns).text for x in e.findall("a:author", ns)],
                                 "cit": None, "src": "arxiv", "q": code})
                n_q += len(ents)
                start += per
                if len(ents) < per:
                    break
            log(f"[arxiv] {code}{i}: total={total} fetched={n_q}")
            counts[f"{code}{i}"] = {"query": q, "total_reported": total, "fetched": n_q}
    sj = CFG.get("sibling_arxiv_json")
    if sj and os.path.exists(sj):
        d = json.load(open(sj, encoding="utf-8"))
        for x in d:
            rows.append({"s2id": "", "doi": "", "arxiv": re.sub(r"v\d+$", "", x["id"]), "acl": "",
                         "title": x.get("title", ""), "abstract": x.get("summary", ""),
                         "year": int(x.get("published", "0000")[:4] or 0), "venue": "arXiv.org",
                         "authors": x.get("authors", []), "cit": None, "src": "arxiv_sibling_search", "q": ""})
        counts["sibling_file"] = {"query": "records already found by the paper's own agent (read-only)",
                                  "total_reported": len(d), "fetched": len(d)}
    sd = CFG.get("sibling_s2_json_dir")
    if sd and os.path.isdir(sd):
        nsib = 0
        for fn in sorted(os.listdir(sd)):
            if fn.startswith("s2_") and fn.endswith(".json"):
                try:
                    for p in json.load(open(os.path.join(sd, fn), encoding="utf-8")).get("data", []):
                        r = from_s2(p, "sibling_prior_work_search", "")
                        rows.append(r)
                        nsib += 1
                except Exception:
                    pass
        counts["sibling_s2_files"] = {"query": "Semantic Scholar hits already cached by the paper's own agent (read-only)",
                                      "total_reported": nsib, "fetched": nsib}
    jl_write(os.path.join(RAW, "candidates_arxiv.jsonl"), rows)
    return counts


def acl_entries():
    """Yield dicts from the ACL Anthology full BibTeX export with abstracts (shared cache in _tools)."""
    cdir = os.path.join(TOOLS, "cache", "acl")
    os.makedirs(cdir, exist_ok=True)
    path = os.path.join(cdir, "anthology+abstracts.bib.gz")
    if not os.path.exists(path):
        log("[acl] downloading anthology+abstracts.bib.gz")
        r = SESSION.get("https://aclanthology.org/anthology+abstracts.bib.gz", timeout=600, stream=True)
        r.raise_for_status()
        with open(path + ".part", "wb") as f:
            for ch in r.iter_content(1 << 20):
                f.write(ch)
        os.replace(path + ".part", path)
    fld = re.compile(r'^\s*(\w+)\s*=\s*(.*)$')
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        ent, key, buf = None, None, []
        for line in f:
            if line.startswith("@"):
                if ent is not None:
                    if key:
                        ent[key] = " ".join(buf)
                    yield ent
                m = re.match(r"@(\w+)\{(.*),\s*$", line)
                ent = {"_type": m.group(1).lower() if m else "", "_key": m.group(2) if m else ""}
                key, buf = None, []
                continue
            if ent is None:
                continue
            m = fld.match(line)
            if m and (line.startswith("    ") and not line.startswith("     ")):
                if key:
                    ent[key] = " ".join(buf)
                key, buf = m.group(1).lower(), [m.group(2).strip()]
            elif key:
                buf.append(line.strip())
        if ent is not None:
            if key:
                ent[key] = " ".join(buf)
            yield ent


def clean_bib(v):
    v = (v or "").strip().rstrip(",").strip()
    if v.startswith('"') and v.endswith('"'):
        v = v[1:-1]
    v = re.sub(r"[{}]", "", v)
    v = v.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    return re.sub(r"\s+", " ", v).strip()


def discover_acl():
    rows, n_all = [], 0
    for e in acl_entries():
        n_all += 1
        if e["_type"] == "proceedings":
            continue
        title, abst = clean_bib(e.get("title")), clean_bib(e.get("abstract"))
        try:
            year = int(clean_bib(e.get("year"))[:4])
        except Exception:
            continue
        if not (YMIN <= year <= YMAX):
            continue
        codes, _ = screen_text(title, abst)
        if not codes:
            continue
        url = clean_bib(e.get("url"))
        m = re.search(r"aclanthology\.org/([^/]+)/?$", url)
        authors = [re.sub(r"\s+", " ", " ".join(reversed([p.strip() for p in a.split(",", 1)]))).strip()
                   for a in re.split(r"\s+and\s+", clean_bib(e.get("author"))) if a.strip()]
        rows.append({"s2id": "", "doi": norm_doi(clean_bib(e.get("doi"))), "arxiv": "",
                     "acl": m.group(1) if m else "", "title": title, "abstract": abst, "year": year,
                     "venue": clean_bib(e.get("booktitle") or e.get("journal")), "authors": authors,
                     "cit": None, "src": "acl_anthology", "q": ";".join(codes)})
    log(f"[acl] scanned {n_all} entries, {len(rows)} pass the screening rules")
    jl_write(os.path.join(RAW, "candidates_acl.jsonl"), rows)
    return {"anthology": {"query": "local regex screen of the full ACL Anthology BibTeX export (same rules as screening)",
                          "total_reported": n_all, "fetched": len(rows)}}


def discover_crossref():
    rows, counts = [], {}
    for code, sl in CFG["sublits"].items():
        for i, q in enumerate(sl.get("crossref_queries", [])):
            n_q, total = 0, None
            for off in range(0, CFG.get("crossref_cap", 600), 200):
                d = cached_fetch("https://api.crossref.org/works", f"crossref/{code}{i}_{qhash(q)}_o{off}.json.gz",
                                 params={"query.bibliographic": q, "rows": 200, "offset": off, "mailto": MAIL,
                                         "filter": f"from-pub-date:{YMIN},until-pub-date:{YMAX}" + CFG.get("crossref_filter", ""),
                                         "select": "DOI,title,abstract,issued,container-title,type,author,is-referenced-by-count"},
                                 host="crossref", min_gap=1.5, retries=5)
                if not d:
                    break
                total = d["message"].get("total-results")
                items = d["message"].get("items", [])
                for it in items:
                    title = " ".join(it.get("title") or [])
                    abst = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
                    try:
                        year = it["issued"]["date-parts"][0][0]
                    except Exception:
                        year = None
                    rows.append({"s2id": "", "doi": norm_doi(it.get("DOI")), "arxiv": arxiv_from_doi(it.get("DOI")),
                                 "acl": "", "title": re.sub(r"\s+", " ", title).strip(),
                                 "abstract": re.sub(r"\s+", " ", abst).strip(), "year": year,
                                 "venue": " ".join(it.get("container-title") or []),
                                 "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip()
                                             for a in it.get("author", [])],
                                 "cit": it.get("is-referenced-by-count"), "src": "crossref", "q": code,
                                 "cr_type": it.get("type")})
                n_q += len(items)
                if len(items) < 200:
                    break
            log(f"[crossref] {code}{i}: total={total} fetched(top by relevance)={n_q}")
            counts[f"{code}{i}"] = {"query": q, "total_reported": total, "fetched": n_q}
    jl_write(os.path.join(RAW, "candidates_crossref.jsonl"), rows)
    return counts


def discover_dblp():
    """DBLP public search API. Recorded honestly if it refuses automated clients."""
    q = CFG.get("dblp_probe", "romanized hindi")
    try:
        r = SESSION.get("https://dblp.org/search/publ/api", params={"q": q, "format": "json", "h": 5}, timeout=40)
        ok = r.status_code == 200 and r.text.lstrip().startswith("{")
        note = "ok" if ok else f"HTTP {r.status_code}; body starts: {r.text[:90]!r}"
    except Exception as e:
        ok, note = False, repr(e)[:150]
    log("[dblp] probe:", note)
    return {"probe": {"query": q, "total_reported": None, "fetched": 0, "status": note, "usable": ok}}


def discover():
    counts = {"semantic_scholar": discover_s2(), "crossref": discover_crossref()}
    if CFG.get("acl"):
        counts["acl_anthology"] = discover_acl()
    counts["arxiv"] = discover_arxiv()
    counts["dblp"] = discover_dblp()
    json.dump(counts, open(os.path.join(CLEAN, "search_counts.json"), "w", encoding="utf-8"), indent=1)


# ------------------------------------------------------------------ screen
class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def cand_keys(c):
    ks = []
    if c.get("s2id"):
        ks.append("s2:" + c["s2id"])
    if c.get("doi"):
        ks.append("doi:" + c["doi"])
        ax = arxiv_from_doi(c["doi"])
        if ax:
            ks.append("arxiv:" + ax)
    if c.get("arxiv"):
        ks.append("arxiv:" + re.sub(r"v\d+$", "", c["arxiv"]).lower())
    if c.get("acl"):
        ks.append("acl:" + c["acl"].lower())
    nt = norm_title(c.get("title"))
    if len(nt) >= 25:
        ks.append("t:" + nt)
    return ks


def merge_group(recs):
    m = {"s2id": "", "doi": "", "arxiv": "", "acl": "", "title": "", "abstract": "", "year": None, "venue": "",
         "authors": [], "cit": None, "src": set(), "q": set()}
    dois = []
    for r in recs:
        for k in ("s2id", "arxiv", "acl"):
            if r.get(k) and not m[k]:
                m[k] = r[k]
        if r.get("doi"):
            dois.append(r["doi"])
        if len(r.get("title") or "") > len(m["title"]) and not m["title"]:
            m["title"] = r["title"]
        if len(r.get("abstract") or "") > len(m["abstract"]):
            m["abstract"] = r["abstract"]
        if r.get("year") and (m["year"] is None or r["src"] == "semantic_scholar"):
            m["year"] = r["year"]
        if r.get("venue") and (not m["venue"] or r["src"] == "semantic_scholar"):
            m["venue"] = r["venue"]
        if len(r.get("authors") or []) > len(m["authors"]):
            m["authors"] = r["authors"]
        if r.get("cit") is not None:
            m["cit"] = max(m["cit"] or 0, r["cit"])
        m["src"].add(r["src"])
        for q in (r.get("q") or "").split(";"):
            if q:
                m["q"].add(q)
    pub = [d for d in dois if not d.startswith("10.48550/")]
    m["doi"] = (pub or dois or [""])[0]
    if not m["arxiv"]:
        for d in dois:
            if arxiv_from_doi(d):
                m["arxiv"] = arxiv_from_doi(d)
    m["src"], m["q"] = sorted(m["src"]), sorted(m["q"])
    return m


def group_candidates(cands):
    uf = UF()
    for i, c in enumerate(cands):
        ks = cand_keys(c)
        uf.find(("i", i))
        for k in ks:
            uf.union(("i", i), k)
    groups = defaultdict(list)
    for i, c in enumerate(cands):
        groups[uf.find(("i", i))].append(c)
    return [merge_group(g) for g in groups.values()]


def lookup_id(m):
    if m.get("s2id"):
        return m["s2id"]
    if m.get("arxiv"):
        return "ARXIV:" + m["arxiv"]
    if m.get("acl"):
        return "ACL:" + m["acl"]
    if m.get("doi"):
        return "DOI:" + m["doi"]
    return None


def fill_abstracts(merged, oa):
    # Records that have no abstract in any source. To keep the load on the shared OpenAlex address low,
    # a Crossref-only record (found by loose free-text ranking) is looked up only if its title already
    # matches the core-concept group of at least one rule; records found by a Boolean search are always tried.
    core = [alt[0] for alts in RULES.values() for alt in alts]
    need = [m for m in merged if not m["abstract"] and (m["doi"] or m["arxiv"])
            and (set(m["src"]) - {"crossref"} or any(g.search(m["title"]) for g in core))
            and not screen_text(m["title"], "")[0]]
    keys = ["doi:" + (m["doi"] or "10.48550/arxiv." + m["arxiv"]) for m in need]
    got = oa.fetch_many(keys, label="openalex abstract fill")
    n = 0
    for m, k in zip(need, keys):
        r = got.get(k)
        if r and r.get("abstract"):
            m["abstract"] = r["abstract"]
            n += 1
    log(f"[screen] abstracts filled from OpenAlex: {n} of {len(need)} records that lacked one")
    return n


def apply_screen(merged, stage):
    inc, exc = [], []
    for m in merged:
        y = m.get("year")
        if y and not (YMIN <= int(y) <= YMAX):
            exc.append((m, "outside year range"))
            continue
        codes, why = screen_text(m["title"], m["abstract"])
        if codes:
            m["sublits"] = codes
            inc.append(m)
        else:
            exc.append((m, why))
    log(f"[screen:{stage}] included {len(inc)}, excluded {len(exc)}")
    return inc, exc


def s2_full_to_rec(p, m=None):
    r = from_s2(p, "semantic_scholar", "")
    r["pub_date"] = p.get("publicationDate") or ""
    r["pub_types"] = p.get("publicationTypes") or []
    r["dblp"] = (p.get("externalIds") or {}).get("DBLP") or ""
    r["ref_count"] = p.get("referenceCount") or 0
    r["oa_pdf"] = (p.get("openAccessPdf") or {}).get("url") or ""
    r["fos"] = p.get("fieldsOfStudy") or []
    r["journal"] = (p.get("journal") or {}).get("name") or ""
    pv = p.get("publicationVenue") or {}
    r["venue_type"] = pv.get("type") or ""
    r["venue_name"] = pv.get("name") or r["venue"]
    r["author_ids"] = [a.get("authorId") or "" for a in (p.get("authors") or [])]
    r["s2_affils"] = [";".join(a.get("affiliations") or []) for a in (p.get("authors") or [])]
    refs = []
    for x in p.get("references") or []:
        ext = x.get("externalIds") or {}
        refs.append({"id": x.get("paperId") or "", "title": x.get("title") or "", "year": x.get("year"),
                     "venue": x.get("venue") or "", "doi": norm_doi(ext.get("DOI")),
                     "arxiv": ext.get("ArXiv") or "", "acl": ext.get("ACL") or "",
                     "fa": ((x.get("authors") or [{}])[0] or {}).get("name") or ""})
    r["refs"] = refs
    if m:
        for k in ("doi", "arxiv", "acl"):
            if not r.get(k) and m.get(k):
                r[k] = m[k]
        if len(m.get("abstract") or "") > len(r.get("abstract") or ""):
            r["abstract"] = m["abstract"]
        r["src"], r["q"] = m["src"], m["q"]
        r["sublits"] = m.get("sublits", [])
        if not r["title"]:
            r["title"] = m["title"]
    return r


def resolve_full(included, tag="full"):
    """Fetch full S2 records (with reference lists) for included candidates. Returns list of recs."""
    ids = [lookup_id(m) for m in included]
    got = s2_batch([i for i in ids if i], tag=tag)
    out, missing = {}, 0
    for m, i in zip(included, ids):
        p = got.get(i) if i else None
        if p is None and i and m.get("doi") and not i.startswith("DOI:"):
            p = None
        if p is None:
            missing += 1
            r = dict(m)
            r.update({"s2id": m.get("s2id") or "", "refs": [], "ref_count": 0, "pub_date": "", "pub_types": [],
                      "dblp": "", "oa_pdf": "", "fos": [], "journal": "", "venue_type": "", "venue_name": m["venue"],
                      "author_ids": [], "s2_affils": [], "not_in_s2": True})
            key = "x:" + (m.get("doi") or m.get("arxiv") or m.get("acl") or norm_title(m["title"]))
            if key in out:
                continue
            out[key] = r
            continue
        r = s2_full_to_rec(p, m)
        key = "s2:" + r["s2id"]
        if key in out:      # two candidate groups resolved to one S2 paper (preprint + published)
            o = out[key]
            o["src"] = sorted(set(o["src"]) | set(r["src"]))
            o["q"] = sorted(set(o["q"]) | set(r["q"]))
            o["sublits"] = sorted(set(o["sublits"]) | set(r["sublits"]))
            o["merged_versions"] = o.get("merged_versions", 1) + 1
            continue
        out[key] = r
    log(f"[resolve:{tag}] {len(included)} candidates -> {len(out)} unique records; {missing} not found in Semantic Scholar")
    return list(out.values())


def title_dedup(recs):
    """Second pass: same normalised title + same first-author surname -> keep the richer record."""
    best, removed = {}, 0
    for r in recs:
        fa = au_short((r.get("authors") or [""])[0]).split(" ")[0]
        k = (norm_title(r["title"]), fa)
        if len(k[0]) < 25:
            k = (k[0], fa, r.get("s2id") or r.get("doi") or id(r))
        if k in best:
            o = best[k]
            removed += 1
            keep, drop = (o, r) if (len(o.get("refs", [])), o.get("cit") or 0) >= (len(r.get("refs", [])), r.get("cit") or 0) else (r, o)
            for f in ("doi", "arxiv", "acl"):
                if not keep.get(f) and drop.get(f):
                    keep[f] = drop[f]
            if keep.get("doi", "").startswith("10.48550/") and drop.get("doi") and not drop["doi"].startswith("10.48550/"):
                keep["doi"] = drop["doi"]
            keep["src"] = sorted(set(keep["src"]) | set(drop["src"]))
            keep["sublits"] = sorted(set(keep.get("sublits", [])) | set(drop.get("sublits", [])))
            keep["merged_versions"] = keep.get("merged_versions", 1) + drop.get("merged_versions", 1)
            keep["cit"] = max(keep.get("cit") or 0, drop.get("cit") or 0)
            best[k] = keep
        else:
            best[k] = r
    return list(best.values()), removed


def screen():
    cands = []
    per_src = Counter()
    for fn in sorted(os.listdir(RAW)):
        if fn.startswith("candidates_") and fn.endswith(".jsonl"):
            rows = jl_read(os.path.join(RAW, fn))
            cands += rows
            for r in rows:
                per_src[r["src"]] += 1
    seeds = CFG.get("seeds", [])
    merged = group_candidates(cands)
    log(f"[screen] {len(cands)} records from all sources -> {len(merged)} unique after key/title merge")
    oa = OAStore()
    fill_abstracts(merged, oa)
    inc, exc = apply_screen(merged, "main")
    recs = resolve_full(inc, tag="full")
    # re-screen with the (possibly longer) S2 abstract is unnecessary: rules already matched.
    # seeds: force-include papers named by the paper's own planning documents
    have = {r.get("arxiv", "").lower() for r in recs} | {r.get("doi", "") for r in recs}
    seed_missing = [s for s in seeds if s.split(":", 1)[1].lower() not in have]
    n_seed_forced = 0
    if seed_missing:
        got = s2_batch(seed_missing, tag="seed")
        for s in seed_missing:
            p = got.get(s)
            if p:
                r = s2_full_to_rec(p)
                r["src"], r["q"] = ["seed_named_in_planning_docs"], []
                r["sublits"] = screen_text(r["title"], r["abstract"])[0] or ["seed"]
                r["forced_seed"] = True
                if not any(x.get("s2id") == r["s2id"] for x in recs):
                    recs.append(r)
                    n_seed_forced += 1
            else:
                log("[seed] not found in Semantic Scholar:", s)
    recs, n_title_dups = title_dedup(recs)
    jl_write(os.path.join(CLEAN, "stage_screened.jsonl"), recs)
    with open(os.path.join(CLEAN, "excluded_by_rule.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "year", "doi", "arxiv", "sources", "reason"])
        for m, why in exc:
            w.writerow([m["title"], m.get("year"), m.get("doi"), m.get("arxiv"), ";".join(m["src"]), why])
    st = {"records_identified_per_source": dict(per_src), "records_identified_total": len(cands),
          "unique_after_merge": len(merged), "duplicates_removed_stage1": len(cands) - len(merged),
          "excluded_by_rule": len(exc), "excluded_reasons": dict(Counter(w for _, w in exc)),
          "included_before_version_merge": len(inc),
          "version_duplicates_merged_by_s2_or_title": len(inc) - (len(recs) - n_seed_forced),
          "seeds_forced_in": n_seed_forced, "after_screen": len(recs),
          "not_in_semantic_scholar": sum(1 for r in recs if r.get("not_in_s2"))}
    json.dump(st, open(os.path.join(CLEAN, "prisma_stage1.json"), "w"), indent=1)
    log(json.dumps(st))


# ------------------------------------------------------------------ snowball
def local_cites(recs):
    ids = {r["s2id"] for r in recs if r.get("s2id")}
    lc = Counter()
    for r in recs:
        for x in {x["id"] for x in r.get("refs", []) if x["id"]}:
            if x in ids and x != r.get("s2id"):
                lc[x] += 1
    return lc


def snowball():
    recs = jl_read(os.path.join(CLEAN, "stage_screened.jsonl"))
    lc = local_cites(recs)
    by_id = {r["s2id"]: r for r in recs if r.get("s2id")}
    n = CFG.get("snowball_n_central", 25)
    central = [i for i, _ in lc.most_common(n)]
    for r in recs:
        if r.get("forced_seed") and r.get("s2id") and r["s2id"] not in central and len(central) < n + 8:
            central.append(r["s2id"])
    have = set(by_id)
    back, fwd = {}, {}
    for cid in central:
        for x in by_id[cid].get("refs", []):
            if x["id"] and x["id"] not in have:
                back[x["id"]] = x
        cits = s2_citations(cid, cap=CFG.get("snowball_forward_cap", 2000))
        log(f"[snowball] {by_id[cid]['title'][:60]!r}: local cites={lc[cid]}, forward fetched={len(cits)}")
        for p in cits:
            if p.get("paperId") and p["paperId"] not in have:
                fwd[p["paperId"]] = p
    log(f"[snowball] backward candidates {len(back)}, forward candidates {len(fwd)}")
    # backward refs have no abstract yet: fetch light records
    light = s2_batch(list(back), fields=S2_LIGHT, chunk=200, tag="sb_light")
    cands = []
    for pid, p in light.items():
        if p:
            cands.append(from_s2(p, "snowball_backward", ""))
    for pid, p in fwd.items():
        c = from_s2(p, "snowball_forward", "")
        cands.append(c)
    merged = group_candidates(cands)
    oa = OAStore()
    fill_abstracts(merged, oa)
    inc, exc = apply_screen(merged, "snowball")
    new = resolve_full(inc, tag="full") if inc else []
    new = [r for r in new if r.get("s2id") not in have]
    for r in new:
        r["snowball"] = True
    allrecs, n_dup = title_dedup(recs + new)
    jl_write(os.path.join(CLEAN, "stage_snowballed.jsonl"), allrecs)
    st = {"central_papers": [{"s2id": c, "title": by_id[c]["title"], "local_citations": lc[c]} for c in central],
          "backward_candidates": len(back), "forward_candidates": len(fwd),
          "snowball_unique_candidates": len(merged), "snowball_excluded_by_rule": len(exc),
          "snowball_added": len(allrecs) - len(recs), "after_snowball": len(allrecs)}
    json.dump(st, open(os.path.join(CLEAN, "prisma_stage2.json"), "w"), indent=1)
    log(json.dumps({k: v for k, v in st.items() if k != "central_papers"}))


# ------------------------------------------------------------------ build
PRIORITY = CFG.get("primary_sublit_priority", ["C", "B", "D", "A"])


def build():
    path = os.path.join(CLEAN, "stage_snowballed.jsonl")
    recs = jl_read(path if os.path.exists(path) else os.path.join(CLEAN, "stage_screened.jsonl"))
    # manual exclusions (hand screen): data/clean/manual_exclusions.csv with columns id,reason
    man = {}
    mp = os.path.join(CLEAN, "manual_exclusions.csv")
    if os.path.exists(mp):
        for row in csv.DictReader(open(mp, encoding="utf-8")):
            man[row["id"]] = row["reason"]
    kept, removed = [], []
    for r in recs:
        rid = r.get("s2id") or ("x:" + (r.get("doi") or r.get("arxiv") or r.get("acl") or norm_title(r["title"])[:60]))
        r["id"] = rid
        if rid in man and not r.get("forced_seed"):
            removed.append((r, man[rid]))
        else:
            kept.append(r)
    recs = kept
    oa = OAStore()
    keys = {}
    for r in recs:
        ks = []
        if r.get("doi"):
            ks.append("doi:" + r["doi"])
        if r.get("arxiv") and not (r.get("doi") or "").startswith("10.48550/"):
            ks.append("doi:10.48550/arxiv." + r["arxiv"].lower())
        keys[r["id"]] = ks
    oa.fetch_many([k for ks in keys.values() for k in ks], label="openalex enrich")
    lc = local_cites(recs)
    ids = {r["s2id"] for r in recs if r.get("s2id")}
    rows, edges = [], []
    for r in recs:
        oas = [oa.idx.get(k) for k in keys[r["id"]]]
        oas = [o for o in oas if o]
        best = None
        for o in oas:   # prefer the version that carries institutions
            if any(a.get("institutions") for a in o.get("authorships", [])):
                best = o
                break
        best = best or (oas[0] if oas else None)
        insts, countries, fa_country, corr_country = [], [], "", ""
        kw, topic, subfield, field, oa_type, oa_id, oa_cit, oa_src, is_oa, oa_url, lang = [], "", "", "", "", "", None, "", "", "", ""
        au_inst, affil_pairs, rp = [], [], ""
        if best:
            for j, a in enumerate(best.get("authorships", [])):
                ins = [i.get("display_name") for i in a.get("institutions", []) if i.get("display_name")]
                cs = [c for c in (a.get("countries") or []) if c]
                au_aff = [f"{i.get('display_name')} [{i.get('country_code') or ''}]" for i in a.get("institutions", [])
                          if i.get("display_name")]
                affil_pairs += au_aff
                if j == 0 or (a.get("is_corresponding") and not rp):
                    rp = au_aff[0] if au_aff else rp
                insts += ins
                countries += cs
                au_inst.append("|".join(ins))
                if j == 0 and cs:
                    fa_country = cs[0]
                if a.get("is_corresponding") and cs and not corr_country:
                    corr_country = cs[0]
            kw = [k.get("display_name") for k in best.get("keywords", []) if k.get("display_name")]
            pt = best.get("primary_topic") or {}
            topic = pt.get("display_name") or ""
            subfield = (pt.get("subfield") or {}).get("display_name") or ""
            field = (pt.get("field") or {}).get("display_name") or ""
            oa_type, oa_id = best.get("type") or "", (best.get("id") or "").rsplit("/", 1)[-1]
            oa_cit = max([o.get("cited_by_count") or 0 for o in oas])
            oa_src = ((best.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            oacc = best.get("open_access") or {}
            is_oa, oa_url = oacc.get("is_oa"), oacc.get("oa_url") or ""
            lang = best.get("language") or ""
        sl = [s for s in r.get("sublits", []) if s in CFG["sublits"]]
        primary = next((p for p in PRIORITY if p in sl), sl[0] if sl else "seed")
        venue = r.get("venue_name") or r.get("venue") or r.get("journal") or oa_src or ""
        if not venue and r.get("arxiv"):
            venue = "arXiv.org"
        pt = [t.lower() for t in (r.get("pub_types") or [])]
        if "review" in pt:
            doc_type = "review"
        elif venue.lower().startswith("arxiv") or (not r.get("doi") and r.get("arxiv")) or oa_type == "preprint" and not r.get("acl"):
            doc_type = "preprint"
        elif "conference" in pt or r.get("acl") or r.get("venue_type") == "conference":
            doc_type = "conference paper"
        elif "journalarticle" in pt or r.get("venue_type") == "journal":
            doc_type = "article"
        else:
            doc_type = oa_type or "other"
        url = ("https://arxiv.org/abs/" + r["arxiv"]) if r.get("arxiv") else (
            "https://aclanthology.org/" + r["acl"] if r.get("acl") else ("https://doi.org/" + r["doi"] if r.get("doi") else ""))
        pdf = ("https://arxiv.org/pdf/" + r["arxiv"]) if r.get("arxiv") else (
            f"https://aclanthology.org/{r['acl']}.pdf" if r.get("acl") else (r.get("oa_pdf") or oa_url or ""))
        refs_in = sum(1 for x in r.get("refs", []) if x["id"] in ids)
        rows.append({
            "id": r["id"], "title": r["title"], "abstract": r.get("abstract") or "", "year": r.get("year") or "",
            "pub_date": r.get("pub_date") or "", "venue": venue, "doc_type": doc_type,
            "authors": "; ".join(r.get("authors") or []), "author_ids": "; ".join(r.get("author_ids") or []),
            "n_authors": len(r.get("authors") or []), "doi": r.get("doi") or "", "arxiv_id": r.get("arxiv") or "",
            "acl_id": r.get("acl") or "", "dblp_key": r.get("dblp") or "", "url": url, "oa_pdf_url": pdf,
            "cited_by": r.get("cit") if r.get("cit") is not None else (oa_cit or 0),
            "cited_by_openalex": oa_cit if oa_cit is not None else "",
            "ref_count_reported": r.get("ref_count") or 0, "refs_listed": len(r.get("refs", [])),
            "refs_in_corpus": refs_in, "local_citations": lc.get(r.get("s2id"), 0),
            "sublits": ";".join(sl), "primary_sublit": primary, "found_in": ";".join(r.get("src") or []),
            "merged_versions": r.get("merged_versions", 1),
            "snowball": int(bool(r.get("snowball"))), "forced_seed": int(bool(r.get("forced_seed"))),
            "in_semantic_scholar": int(not r.get("not_in_s2")), "openalex_id": oa_id, "openalex_type": oa_type,
            "institutions": "; ".join(dict.fromkeys(insts)), "author_institutions": "; ".join(au_inst),
            "affil_pairs": "; ".join(affil_pairs), "reprint_affil": rp,
            "countries": ";".join(dict.fromkeys(countries)), "author_countries_all": ";".join(countries),
            "first_author_country": fa_country, "corresponding_country": corr_country or fa_country,
            "openalex_keywords": "; ".join(kw), "openalex_topic": topic, "openalex_subfield": subfield,
            "openalex_field": field, "is_oa": is_oa if is_oa is not None else "", "language": lang,
        })
        for x in r.get("refs", []):
            edges.append({"citing": r["id"], "cited": x["id"], "cited_title": x["title"], "cited_year": x["year"] or "",
                          "cited_first_author": x["fa"], "cited_venue": x["venue"], "cited_doi": x["doi"],
                          "cited_arxiv": x["arxiv"], "cited_acl": x["acl"], "in_corpus": int(x["id"] in ids)})
    def so_abbr(v):
        v = re.sub(r"[,;.]", " ", ascii_upper(v or ""))
        v = re.sub(r"\s+", " ", v).strip()
        if v.startswith("ARXIV"):
            v = "ARXIV"
        return v[:60].strip() or "NO SOURCE"
    seen_sr, sr_of = Counter(), {}
    for x in rows:
        fa = au_short(x["authors"].split(";")[0]) or "ANONYMOUS"
        base = f"{fa}, {x['year'] or 'NA'}, {so_abbr(x['venue'])}"
        x["AU"] = ";".join(a for a in (au_short(n) for n in x["authors"].split(";")) if a)
        x["SO"] = so_abbr(x["venue"])
        seen_sr[base] += 1
        x["SR"] = base if seen_sr[base] == 1 else f"{base}-{chr(96 + min(seen_sr[base], 26))}"
        sr_of[x["id"]] = x["SR"] + (f", DOI {x['doi'].upper()}" if x["doi"] else "")
    cr_of = {}
    for e in edges:
        cid = e["cited"]
        if cid in sr_of:
            e["cr"] = sr_of[cid]
            continue
        k = cid or norm_title(e["cited_title"])
        if k not in cr_of:
            if not e["cited_year"] or not (e["cited_first_author"] or e["cited_title"]):
                cr_of[k] = ""
            else:
                fa = au_short(e["cited_first_author"]) or "ANONYMOUS"
                cr_of[k] = f"{fa}, {e['cited_year']}, {so_abbr(e['cited_venue'])}" + (
                    f", DOI {e['cited_doi'].upper()}" if e["cited_doi"] else "")
        e["cr"] = cr_of[k]
    rows.sort(key=lambda x: (-(x["local_citations"] or 0), -(x["cited_by"] or 0)))
    with open(os.path.join(CLEAN, "master.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(CLEAN, "references.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(edges[0].keys()))
        w.writeheader()
        w.writerows(edges)
    with open(os.path.join(CLEAN, "excluded_manual.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "year", "reason"])
        for r, why in removed:
            w.writerow([r["id"], r["title"], r.get("year"), why])
    n = len(rows)
    cov = {"final_corpus": n, "manual_exclusions": len(removed),
           "with_abstract": sum(1 for r in rows if r["abstract"]),
           "with_reference_list": sum(1 for r in rows if r["refs_listed"] > 0),
           "with_openalex_record": sum(1 for r in rows if r["openalex_id"]),
           "with_institution": sum(1 for r in rows if r["institutions"]),
           "with_country": sum(1 for r in rows if r["countries"]),
           "with_openalex_keywords": sum(1 for r in rows if r["openalex_keywords"]),
           "with_doi": sum(1 for r in rows if r["doi"]), "with_arxiv_id": sum(1 for r in rows if r["arxiv_id"]),
           "with_acl_id": sum(1 for r in rows if r["acl_id"]), "with_dblp_key": sum(1 for r in rows if r["dblp_key"]),
           "preprint_only": sum(1 for r in rows if r["doc_type"] == "preprint"),
           "records_with_preprint_and_published_version_merged": sum(1 for r in rows if r["arxiv_id"] and (r["acl_id"] or (r["doi"] and not r["doi"].startswith("10.48550/")))),
           "reference_links": len(edges), "reference_links_in_corpus": sum(e["in_corpus"] for e in edges),
           "by_primary_sublit": dict(Counter(r["primary_sublit"] for r in rows)),
           "by_sublit_nonexclusive": dict(Counter(s for r in rows for s in r["sublits"].split(";") if s)),
           "by_doc_type": dict(Counter(r["doc_type"] for r in rows)),
           "date_built_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    json.dump(cov, open(os.path.join(CLEAN, "coverage.json"), "w"), indent=1)
    log(json.dumps(cov))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage in ("discover", "all"):
        discover()
    if stage in ("screen", "all"):
        screen()
    if stage in ("snowball", "all"):
        snowball()
    if stage in ("build", "all"):
        build()
