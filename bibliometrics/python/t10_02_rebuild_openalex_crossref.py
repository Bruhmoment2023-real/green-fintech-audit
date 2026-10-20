"""Task 10, step 2: rebuild the Scopus search on free databases and compare record by record.

Scopus search (reconstructed): TITLE-ABS-KEY ( fintech AND "green finance" ), 2021-2026, articles + reviews.
Every one of the 168 valid Scopus records satisfies that string; the export itself does not store the string.

Because keyless OpenAlex *search* requests were out of budget on the pull date (see README), the OpenAlex corpus is
built in two documented steps: (1) candidate DOIs are discovered with Semantic Scholar's Boolean title+abstract
search, Crossref free-text search and the Scopus export itself; (2) each candidate's OpenAlex record is fetched by
DOI (free single-work lookup) and the SAME search string is applied to OpenAlex's own title + abstract.
If data/raw/openalex_search/ exists (true OpenAlex search, run after the budget reset by openalex_search.py), its
hits are merged in and the two routes are compared in tables/T02_openalex_search_validation.csv.

Usage: python t10_02_rebuild_openalex_crossref.py
"""
import csv
import glob
import gzip
import json
import os
import re
from collections import Counter

import pandas as pd

from bm_common import (BASE, CLEAN, MAIL, RAW, TAB, OAStore, au_short, ascii_upper, cached_fetch, invert_abstract,
                       load_config, log, norm_doi, norm_title, qhash, s2_bulk)

CFG = load_config()
FT = re.compile(r"\bfin-?tech\w*", re.I)
FT_WIDE = re.compile(r"\bfin-?tech\w*|\bfinancial technolog\w*", re.I)
GF = re.compile(r"\bgreen financ(e|es|ing)\b", re.I)
Y0, Y1 = 2021, 2026
SCOPUS_EXPORT_DATE = "2026-03-22"     # timestamp of the export file; the export does not record its own search date

sc = pd.read_csv(os.path.join(CLEAN, "scopus_168.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
flags = pd.read_csv(os.path.join(TAB, "T01_scopus_record_flags.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
sc["doi"] = sc["DOI"].map(norm_doi)
contaminated = set(flags[flags.CONTAMINATED == "True"].DOI.map(norm_doi))
scopus_dois = set(sc.doi) - {""}

# ------------------------------------------------------------------ 1 discovery
cand = {}          # doi -> {sources}
counts = {"semantic_scholar": {}, "crossref": {}}
S2Q = ['fintech + "green finance"',
       '(fintech | "fin-tech" | "financial technology" | "financial technologies") + ("green finance" | "green financing")']
s2rows = {}
for i, q in enumerate(S2Q):
    total, recs = s2_bulk(q, year=f"{Y0}-{Y1}", cap=5000, tag=f"gf{i}")
    counts["semantic_scholar"][f"S{i}"] = {"query": q, "total_reported": total, "fetched": len(recs)}
    log(f"[s2] {q}: {total}")
    for p in recs:
        d = norm_doi((p.get("externalIds") or {}).get("DOI"))
        s2rows[p["paperId"]] = p
        if d:
            cand.setdefault(d, set()).add("semantic_scholar")
CRQ = ["fintech green finance", "financial technology green finance", "green fintech", "fintech green finance carbon emissions",
       "fintech green finance sustainable development", "fintech green finance natural resources", "digital finance green finance fintech",
       "fintech green finance bibliometric review"]
cr_items = {}
for i, q in enumerate(CRQ):
    n_q, total = 0, None
    for off in range(0, 1000, 200):
        d = cached_fetch("https://api.crossref.org/works", f"crossref/gf{i}_{qhash(q)}_o{off}.json.gz",
                         params={"query.bibliographic": q, "rows": 200, "offset": off, "mailto": MAIL,
                                 "filter": f"from-pub-date:{Y0},until-pub-date:{Y1}",
                                 "select": "DOI,title,abstract,issued,container-title,type,author,is-referenced-by-count"},
                         host="crossref", min_gap=1.5)
        if not d:
            break
        total = d["message"].get("total-results")
        items = d["message"].get("items", [])
        for it in items:
            cr_items[norm_doi(it.get("DOI"))] = it
        n_q += len(items)
        if len(items) < 200:
            break
    counts["crossref"][f"C{i}"] = {"query": q, "total_reported": total, "fetched": n_q}
    log(f"[crossref] {q}: total {total}, taken {n_q}")


def cr_text(it):
    return " ".join(it.get("title") or []) + " . " + re.sub(r"<[^>]+>", " ", it.get("abstract") or "")


n_cr_pref = 0
for d, it in cr_items.items():
    t = cr_text(it)
    if FT_WIDE.search(t) or GF.search(t):       # loose prefilter: either term in Crossref's own metadata
        cand.setdefault(d, set()).add("crossref")
        n_cr_pref += 1
for d in scopus_dois:
    cand.setdefault(d, set()).add("scopus_export")
log(f"[discover] candidate DOIs: {len(cand)} (crossref prefiltered {n_cr_pref} of {len(cr_items)})")

# Crossref lookups for the Scopus DOIs themselves (is the record in Crossref, does it carry an abstract?)
cr_scopus = {}
for d in sorted(scopus_dois):
    it = cr_items.get(d)
    if it is None:
        r = cached_fetch("https://api.crossref.org/works/" + d, f"crossref_doi/{qhash(d)}.json.gz", params={"mailto": MAIL},
                         host="crossref", min_gap=0.6, retries=3)
        it = (r or {}).get("message")
    cr_scopus[d] = it

# ------------------------------------------------------------------ 2 OpenAlex records by DOI
oa = OAStore()
oa.fetch_many(["doi:" + d for d in cand], label="openalex by doi")
true_hits = {}
for fn in glob.glob(os.path.join(RAW, "openalex_search", "*.json.gz")):
    tag = os.path.basename(fn).rsplit("_p", 1)[0]
    for w in json.load(gzip.open(fn, "rt", encoding="utf-8"))["results"]:
        w["abstract"] = invert_abstract(w.pop("abstract_inverted_index", None))
        true_hits.setdefault(w["id"], (tag, w))

recs = {}
for d, srcs in cand.items():
    w = oa.idx.get("doi:" + d)
    if w:
        o = recs.setdefault(w["id"], {"w": w, "found_by": set(), "dois": set()})
        o["found_by"] |= srcs
        o["dois"].add(d)
for wid, (tag, w) in true_hits.items():
    o = recs.setdefault(wid, {"w": w, "found_by": set(), "dois": set()})
    o["found_by"].add("openalex_search:" + tag)
    if w.get("doi"):
        o["dois"].add(norm_doi(w["doi"]))


def oa_flags(w):
    text = (w.get("title") or "") + " . " + (w.get("abstract") or "")
    return bool(FT.search(text)), bool(GF.search(text))


rows = []
for wid, o in recs.items():
    w = o["w"]
    ft, gf = oa_flags(w)
    src = ((w.get("primary_location") or {}).get("source") or {})
    doi = norm_doi(w.get("doi")) or (sorted(o["dois"])[0] if o["dois"] else "")
    rows.append({"openalex_id": wid.rsplit("/", 1)[-1], "doi": doi, "all_dois": ";".join(sorted(o["dois"])), "title": w.get("title") or "",
                 "year": w.get("publication_year"), "pub_date": w.get("publication_date") or "", "type": w.get("type") or "",
                 "language": w.get("language") or "", "source": src.get("display_name") or "", "source_type": src.get("type") or "",
                 "cited_by": w.get("cited_by_count") or 0, "has_abstract": bool(w.get("abstract")),
                 "n_refs": len(w.get("referenced_works") or []), "ft_in_TA": ft, "gf_in_TA": gf, "found_by": ";".join(sorted(o["found_by"])),
                 "in_scopus_168": bool(o["dois"] & scopus_dois), "in_scopus_contaminated": bool(o["dois"] & contaminated)})
A = pd.DataFrame(rows)
A["string_match"] = A.ft_in_TA & A.gf_in_TA
A["type_ok"] = A.type.isin(["article", "review"])
A["year_ok"] = A.year.between(Y0, Y1)
A["lang_ok"] = A.language.isin(["en", ""])
A["in_openalex_corpus"] = A.string_match & A.type_ok & A.year_ok & A.lang_ok
A.to_csv(os.path.join(CLEAN, "openalex_all_fetched.csv"), index=False, encoding="utf-8-sig")
corpus_ids = set(A[A.in_openalex_corpus].openalex_id)
log(f"[openalex] fetched {len(A)} works; string match {int(A.string_match.sum())}; corpus (article/review, {Y0}-{Y1}, English) {len(corpus_ids)}")

# title-level duplicates inside the OpenAlex corpus (preprint + journal version, or double-indexed records)
C = A[A.in_openalex_corpus].copy()
C["nt"] = C.title.map(norm_title)
C = C.sort_values(["in_scopus_168", "cited_by", "n_refs"], ascending=False)
dups = C[C.duplicated("nt", keep="first")]
C = C.drop_duplicates("nt", keep="first")
dups.to_csv(os.path.join(CLEAN, "openalex_title_duplicates_removed.csv"), index=False, encoding="utf-8-sig")
log(f"[openalex] title duplicates removed: {len(dups)} -> corpus {len(C)}")
corpus_ids = set(C.openalex_id)

# ------------------------------------------------------------------ 3 record-by-record comparison (DOI)
oa_by_doi = {}
for _, r in A.iterrows():
    for d in r.all_dois.split(";"):
        if d:
            oa_by_doi[d] = r
comp = []
for _, r in sc.iterrows():
    d = r.doi
    o = oa_by_doi.get(d)
    it = cr_scopus.get(d)
    crt = cr_text(it) if it else ""
    if o is None:
        reason = "no OpenAlex record for this DOI"
    elif o.openalex_id in corpus_ids:
        reason = "in both"
    elif not o.has_abstract and not (o.ft_in_TA and o.gf_in_TA):
        reason = "OpenAlex has no abstract, terms not in title"
    elif not o.string_match:
        reason = "terms only in Scopus keywords, not in OpenAlex title+abstract"
    elif not o.type_ok:
        reason = f"OpenAlex document type is '{o.type}'"
    elif not o.year_ok:
        reason = f"OpenAlex year is {o.year}"
    elif not o.lang_ok:
        reason = f"OpenAlex language is '{o.language}'"
    else:
        reason = "duplicate title in OpenAlex (other version kept)"
    comp.append({"doi": d, "title": r["Title"], "scopus_year": r["Year"], "scopus_source": r["Source title"], "scopus_type": r["Document Type"],
                 "scopus_contaminated": d in contaminated, "openalex_record_exists": o is not None,
                 "openalex_id": o.openalex_id if o is not None else "", "openalex_type": o.type if o is not None else "",
                 "openalex_year": o.year if o is not None else "", "openalex_has_abstract": bool(o.has_abstract) if o is not None else False,
                 "openalex_string_match": bool(o.string_match) if o is not None else False,
                 "in_openalex_corpus": o is not None and o.openalex_id in corpus_ids, "why_missing_from_openalex_corpus": "" if reason == "in both" else reason,
                 "crossref_record_exists": it is not None, "crossref_has_abstract": bool(it and it.get("abstract")),
                 "crossref_type": (it or {}).get("type", ""), "crossref_string_match": bool(FT.search(crt) and GF.search(crt)),
                 "scopus_cited_by": r["Cited by"], "openalex_cited_by": o.cited_by if o is not None else "",
                 "crossref_cited_by": (it or {}).get("is-referenced-by-count", "")})
comp = pd.DataFrame(comp)
comp.to_csv(os.path.join(TAB, "T02_scopus_records_in_other_databases.csv"), index=False, encoding="utf-8-sig")

only_oa = C[~C.in_scopus_168].copy()
only_oa["after_scopus_export_date"] = only_oa.pub_date > SCOPUS_EXPORT_DATE


def why_only(r):
    if r.after_scopus_export_date:
        return "published after the Scopus export date"
    if r.source_type in ("repository",) or re.search(r"ssrn|preprint|research square|arxiv|zenodo", r.source, re.I):
        return "preprint or repository record (not indexed by Scopus)"
    if not r.source:
        return "no source recorded in OpenAlex"
    return "journal record before the export date: source not in Scopus, or Scopus search missed it (cannot be told apart without Scopus access)"


only_oa["likely_reason_not_in_scopus_export"] = only_oa.apply(why_only, axis=1)
only_oa.drop(columns=["nt"]).to_csv(os.path.join(TAB, "T02_openalex_only_records.csv"), index=False, encoding="utf-8-sig")

# Crossref corpus: what a Crossref-only search could have built
crc = []
for d, it in cr_items.items():
    t = cr_text(it)
    try:
        y = it["issued"]["date-parts"][0][0]
    except Exception:
        y = None
    if FT.search(t) and GF.search(t) and y and Y0 <= y <= Y1 and it.get("type") in ("journal-article",):
        crc.append({"doi": d, "title": " ".join(it.get("title") or []), "year": y, "source": " ".join(it.get("container-title") or []),
                    "type": it.get("type"), "has_abstract": bool(it.get("abstract")), "cited_by": it.get("is-referenced-by-count"),
                    "in_scopus_168": d in scopus_dois, "in_openalex_corpus": (d in oa_by_doi and oa_by_doi[d].openalex_id in corpus_ids)})
crc = pd.DataFrame(crc)
crc.to_csv(os.path.join(CLEAN, "crossref_corpus.csv"), index=False, encoding="utf-8-sig")

clean_dois = scopus_dois - contaminated
oa_dois = set()
for _, r in C.iterrows():
    oa_dois |= {d for d in r.all_dois.split(";") if d}
cr_dois = set(crc.doi) if len(crc) else set()
S = [("Scopus export, valid records", len(sc)), ("Scopus, contaminated records (rule in T01)", len(contaminated)),
     ("Scopus, cleaned corpus", len(sc) - len(contaminated)),
     ("OpenAlex works fetched (all candidates)", len(A)), ("OpenAlex works matching the string in title+abstract", int(A.string_match.sum())),
     ("OpenAlex corpus (article/review, 2021-2026, English, title-deduplicated)", len(C)),
     ("OpenAlex corpus restricted to publication date <= Scopus export date", int((C.pub_date <= SCOPUS_EXPORT_DATE).sum())),
     ("Crossref corpus (journal-article, string in Crossref title+abstract)", len(crc)),
     ("Scopus 168 with an OpenAlex record (by DOI)", int(comp.openalex_record_exists.sum())),
     ("Scopus 168 with an abstract in OpenAlex", int(comp.openalex_has_abstract.sum())),
     ("Scopus 168 in the OpenAlex corpus", int(comp.in_openalex_corpus.sum())),
     ("Scopus cleaned 155 in the OpenAlex corpus", int(comp[~comp.scopus_contaminated].in_openalex_corpus.sum())),
     ("Scopus contaminated 13 in the OpenAlex corpus", int(comp[comp.scopus_contaminated].in_openalex_corpus.sum())),
     ("OpenAlex corpus records not in the Scopus export", len(only_oa)),
     ("  of which published after the export date", int(only_oa.after_scopus_export_date.sum())),
     ("Scopus 168 with a Crossref record", int(comp.crossref_record_exists.sum())),
     ("Scopus 168 with an abstract in Crossref", int(comp.crossref_has_abstract.sum())),
     ("Scopus 168 findable by the string in Crossref's own title+abstract", int(comp.crossref_string_match.sum())),
     ("Jaccard overlap, Scopus cleaned vs OpenAlex corpus (DOI)", round(len(clean_dois & oa_dois) / max(1, len(clean_dois | set(C.doi))), 3))]
for k, v in Counter(comp[~comp.in_openalex_corpus].why_missing_from_openalex_corpus).most_common():
    S.append((f"Scopus-only reason: {k}", v))
for k, v in Counter(only_oa.likely_reason_not_in_scopus_export).most_common():
    S.append((f"OpenAlex-only reason: {k}", v))
pd.DataFrame(S, columns=["item", "value"]).to_csv(os.path.join(TAB, "T02_overlap_summary.csv"), index=False, encoding="utf-8-sig")
for s in S:
    print(s[0], "=", s[1])

# validation of the emulated search against the true OpenAlex search, when the latter exists
if true_hits:
    T = A[A.found_by.str.contains("openalex_search")]
    emu = A[A.found_by.str.contains("semantic_scholar|crossref|scopus_export")]
    V = [("true OpenAlex search hits (all pages fetched)", len(T)),
         ("true hits that also satisfy the local string rule", int(T.string_match.sum())),
         ("true hits already found by the emulated route", int(T.found_by.str.contains("semantic_scholar|crossref|scopus_export").sum())),
         ("string-matching works found ONLY by the true search", int((T.string_match & ~T.found_by.str.contains("semantic_scholar|crossref|scopus_export")).sum())),
         ("string-matching works found ONLY by the emulated route", int((emu.string_match & ~emu.found_by.str.contains("openalex_search")).sum()))]
    pd.DataFrame(V, columns=["item", "value"]).to_csv(os.path.join(TAB, "T02_openalex_search_validation.csv"), index=False, encoding="utf-8-sig")
    for v in V:
        print("VALIDATION", v)
json.dump(counts, open(os.path.join(CLEAN, "search_counts.json"), "w"), indent=1)

# ------------------------------------------------------------------ 4 master.csv + references.csv for the OpenAlex corpus
THEMES = CFG.get("sublits", {})
TR = {k: re.compile(v["rule"][0], re.I) for k, v in THEMES.items()}
PRIORITY = CFG.get("primary_sublit_priority", list(THEMES))


def so_abbr(v):
    v = re.sub(r"[,;.]", " ", ascii_upper(v or ""))
    return re.sub(r"\s+", " ", v).strip()[:60].strip() or "NO SOURCE"


works = {wid: recs["https://openalex.org/" + wid]["w"] for wid in corpus_ids}
refcount = Counter()
for w in works.values():
    for x in set(w.get("referenced_works") or []):
        refcount[x.rsplit("/", 1)[-1]] += 1
need = [k for k, v in refcount.items() if v >= 2 and k not in works]
log(f"[refs] {len(refcount)} unique cited works; resolving {len(need)} cited at least twice")
refstore = OAStore("refs")
refstore.fetch_many(need, select="id,doi,title,publication_year,authorships,primary_location", label="openalex refs")

master, edges = [], []
for wid, w in works.items():
    insts, countries, affil_pairs, rp, fa_country, corr = [], [], [], "", "", ""
    names = []
    for j, a in enumerate(w.get("authorships", [])):
        names.append((a.get("author") or {}).get("display_name") or "")
        cs = [c for c in (a.get("countries") or []) if c]
        au_aff = [f"{i.get('display_name')} [{i.get('country_code') or ''}]" for i in a.get("institutions", []) if i.get("display_name")]
        insts += [i.get("display_name") for i in a.get("institutions", []) if i.get("display_name")]
        countries += cs
        affil_pairs += au_aff
        if j == 0:
            fa_country = cs[0] if cs else ""
            rp = au_aff[0] if au_aff else ""
        if a.get("is_corresponding") and cs and not corr:
            corr = cs[0]
            rp = au_aff[0] if au_aff else rp
    names = [n for n in names if n]
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    text = (w.get("title") or "") + " . " + (w.get("abstract") or "")
    sl = [k for k, rx in TR.items() if rx.search(text)]
    primary = next((p for p in PRIORITY if p in sl), "Z")
    doi = norm_doi(w.get("doi"))
    oacc = w.get("open_access") or {}
    pt = w.get("primary_topic") or {}
    row = A[A.openalex_id == wid].iloc[0]
    master.append({"id": wid, "title": w.get("title") or "", "abstract": w.get("abstract") or "", "year": w.get("publication_year"),
                   "pub_date": w.get("publication_date") or "", "venue": src, "doc_type": w.get("type") or "",
                   "authors": "; ".join(names), "author_ids": "", "n_authors": len(names), "doi": doi, "arxiv_id": "", "acl_id": "", "dblp_key": "",
                   "url": ("https://doi.org/" + doi) if doi else w["id"], "oa_pdf_url": oacc.get("oa_url") or "",
                   "cited_by": w.get("cited_by_count") or 0, "cited_by_openalex": w.get("cited_by_count") or 0,
                   "ref_count_reported": len(w.get("referenced_works") or []), "refs_listed": len(w.get("referenced_works") or []),
                   "refs_in_corpus": 0, "local_citations": 0, "sublits": ";".join(sl), "primary_sublit": primary,
                   "found_in": row.found_by, "merged_versions": 1, "snowball": 0, "forced_seed": 0, "in_semantic_scholar": "",
                   "openalex_id": wid, "openalex_type": w.get("type") or "", "institutions": "; ".join(dict.fromkeys(insts)),
                   "author_institutions": "", "affil_pairs": "; ".join(affil_pairs), "reprint_affil": rp,
                   "countries": ";".join(dict.fromkeys(countries)), "author_countries_all": ";".join(countries),
                   "first_author_country": fa_country, "corresponding_country": corr or fa_country,
                   "openalex_keywords": "; ".join(k.get("display_name") for k in w.get("keywords", []) if k.get("display_name")),
                   "openalex_topic": pt.get("display_name") or "", "openalex_subfield": (pt.get("subfield") or {}).get("display_name") or "",
                   "openalex_field": (pt.get("field") or {}).get("display_name") or "", "is_oa": oacc.get("is_oa"), "language": w.get("language") or "",
                   "in_scopus_168": bool(row.in_scopus_168)})
seen, sr_of = Counter(), {}
for x in master:
    fa = au_short(x["authors"].split(";")[0]) or "ANONYMOUS"
    base = f"{fa}, {x['year'] or 'NA'}, {so_abbr(x['venue'])}"
    x["AU"] = ";".join(a for a in (au_short(n) for n in x["authors"].split(";")) if a)
    x["SO"] = so_abbr(x["venue"])
    seen[base] += 1
    x["SR"] = base if seen[base] == 1 else f"{base}-{chr(96 + min(seen[base], 26))}"
    sr_of[x["id"]] = x["SR"] + (f", DOI {x['doi'].upper()}" if x["doi"] else "")
lc = Counter()
for wid, w in works.items():
    for x in dict.fromkeys(w.get("referenced_works") or []):
        rid = x.rsplit("/", 1)[-1]
        e = {"citing": wid, "cited": rid, "cited_title": "", "cited_year": "", "cited_first_author": "", "cited_venue": "", "cited_doi": "",
             "cited_arxiv": "", "cited_acl": "", "in_corpus": int(rid in works), "cr": ""}
        if rid in works:
            e["cr"] = sr_of[rid]
            cw = works[rid]
            lc[rid] += 1
        else:
            cw = refstore.idx.get(rid)
        if cw:
            fa_ = ((cw.get("authorships") or [{}])[0].get("author") or {}).get("display_name") or ""
            ven = ((cw.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            e.update({"cited_title": cw.get("title") or "", "cited_year": cw.get("publication_year") or "", "cited_first_author": fa_,
                      "cited_venue": ven, "cited_doi": norm_doi(cw.get("doi"))})
            if not e["cr"] and e["cited_year"]:
                e["cr"] = f"{au_short(fa_) or 'ANONYMOUS'}, {e['cited_year']}, {so_abbr(ven)}" + (f", DOI {e['cited_doi'].upper()}" if e["cited_doi"] else "")
        edges.append(e)
for x in master:
    x["local_citations"] = lc.get(x["id"], 0)
    x["refs_in_corpus"] = sum(1 for e in edges if e["citing"] == x["id"] and e["in_corpus"]) if x["refs_listed"] else 0
master.sort(key=lambda x: (-x["local_citations"], -x["cited_by"]))
with open(os.path.join(CLEAN, "master.csv"), "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=list(master[0].keys()))
    wr.writeheader()
    wr.writerows(master)
with open(os.path.join(CLEAN, "references.csv"), "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=list(edges[0].keys()))
    wr.writeheader()
    wr.writerows(edges)
n = len(master)
cov = {"final_corpus": n, "manual_exclusions": 0, "with_abstract": sum(1 for r in master if r["abstract"]),
       "with_reference_list": sum(1 for r in master if r["refs_listed"] > 0), "with_openalex_record": n,
       "with_institution": sum(1 for r in master if r["institutions"]), "with_country": sum(1 for r in master if r["countries"]),
       "with_openalex_keywords": sum(1 for r in master if r["openalex_keywords"]), "with_doi": sum(1 for r in master if r["doi"]),
       "reference_links": len(edges), "reference_links_in_corpus": sum(e["in_corpus"] for e in edges),
       "reference_links_with_resolved_metadata": sum(1 for e in edges if e["cr"]),
       "by_primary_sublit": dict(Counter(r["primary_sublit"] for r in master)), "by_doc_type": dict(Counter(r["doc_type"] for r in master))}
json.dump(cov, open(os.path.join(CLEAN, "coverage.json"), "w"), indent=1)
log(json.dumps(cov))
