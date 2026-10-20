"""Shared helpers for the bibliometric mapping pipeline (identical copy in each paper folder).

Every network response is cached under data/raw/ so nothing is fetched twice.
No API keys are used anywhere. Polite identification via User-Agent / mailto only.
"""
import gzip
import hashlib
import json
import os
import re
import sys
import threading
import time
import unicodedata

import requests

MAIL = ""   # deliberately empty: no personal identifier in any request (brief rule)
UA = f"bibliomap/0.1 (student literature mapping)"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                      # ...\bibliometrics
RAW = os.path.join(BASE, "data", "raw")
CLEAN = os.path.join(BASE, "data", "clean")
FIG = os.path.join(BASE, "figures")
TAB = os.path.join(BASE, "tables")
TOOLS = os.path.join(os.path.dirname(os.path.dirname(BASE)), "_tools")
for _d in (RAW, CLEAN, FIG, TAB):
    os.makedirs(_d, exist_ok=True)

if not os.path.exists("D:\\"):
    sys.exit("D: is not mounted - stopping (never fall back to C:).")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})
_last_call = {}
_lock = threading.Lock()


def load_config():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def qhash(*parts):
    return hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(os.path.join(BASE, "data", "fetch-log.txt"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%SZ ", time.gmtime()) + msg + "\n")


def throttle(host, min_gap):
    """Global per-host minimum gap between calls."""
    with _lock:
        now = time.time()
        wait = _last_call.get(host, 0) + min_gap - now
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.time()


def cached_fetch(url, cache_file, params=None, host="x", min_gap=1.0, retries=6,
                 method="GET", body=None, as_json=True, timeout=90, backoff=4.0):
    """GET/POST with on-disk cache (gz). Returns parsed JSON (or text), or None on failure/404."""
    path = os.path.join(RAW, cache_file)
    if os.path.exists(path):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            txt = f.read()
        return json.loads(txt) if as_json else txt
    os.makedirs(os.path.dirname(path), exist_ok=True)
    err = None
    for attempt in range(retries):
        throttle(host, min_gap)
        try:
            if method == "POST":
                r = SESSION.post(url, params=params, json=body, timeout=timeout)
            else:
                r = SESSION.get(url, params=params, timeout=timeout)
        except Exception as e:  # network error
            err = repr(e)[:150]
            time.sleep(backoff * (attempt + 1))
            continue
        if r.status_code == 200:
            txt = r.text
            if as_json:
                try:
                    data = json.loads(txt)
                except Exception:
                    err = "non-JSON 200 response"
                    time.sleep(backoff)
                    continue
            with gzip.open(path, "wt", encoding="utf-8") as f:
                f.write(txt)
            return data if as_json else txt
        if r.status_code == 404:
            return None
        err = f"HTTP {r.status_code}: {r.text[:120]}"
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff * (attempt + 1))
            continue
        break
    log(f"FAILED {host} {cache_file}: {err}")
    return None


# ---------- text helpers ----------
def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def norm_doi(d):
    if not d:
        return ""
    d = str(d).strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


def arxiv_from_doi(d):
    m = re.match(r"10\.48550/arxiv\.(.+)$", norm_doi(d))
    return m.group(1) if m else ""


def invert_abstract(inv):
    if not inv:
        return ""
    pos = []
    for w, idxs in inv.items():
        for i in idxs:
            pos.append((i, w))
    return " ".join(w for _, w in sorted(pos))


def ascii_upper(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().upper()


def au_short(name):
    """'Raj Dabre' -> 'DABRE R' (Web-of-Science style short author)."""
    name = ascii_upper(name).replace(",", " ").replace(";", " ")
    parts = [p for p in re.split(r"\s+", name) if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    last = parts[-1]
    if last in ("JR", "JR.", "II", "III") and len(parts) > 2:
        last = parts[-2]
        parts = parts[:-1]
    initials = "".join(p[0] for p in parts[:-1] if p[0].isalpha())
    return re.sub(r"[^A-Z\- ']", "", last) + " " + initials


# ---------- OpenAlex singleton store (singleton lookups cost 0 credits without a key) ----------
class OAStore:
    """Append-only JSONL cache of OpenAlex single-work lookups, keyed by 'doi:...' or 'W...'."""
    DROP = ("related_works", "counts_by_year", "mesh", "sustainable_development_goals",
            "sustainable_development_goals_aurora", "concepts", "abstract_inverted_index",
            "citation_normalized_percentile", "cited_by_percentile_year", "awards", "funders",
            "content_urls", "apc_list", "apc_paid", "institutions", "study_designs")

    def __init__(self, name="works"):
        d = os.path.join(RAW, "openalex")
        os.makedirs(d, exist_ok=True)
        self.path = os.path.join(d, f"{name}.jsonl")
        self.idx = {}
        self.wlock = threading.Lock()
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        o = json.loads(line)
                        self.idx[o["key"]] = o["rec"]
                    except Exception:
                        pass

    def fetch(self, key, select=None):
        """key = 'doi:10.x/y' or 'W123'. Returns trimmed record or None (cached either way)."""
        if key in self.idx:
            return self.idx[key]
        url = "https://api.openalex.org/works/" + key
        params = {}
        if select:
            params["select"] = select
        rec = None
        status = None
        import random
        for attempt in range(40):
            throttle("openalex", 0.2)
            try:
                r = SESSION.get(url, params=params, timeout=60)
            except Exception:
                time.sleep(3 * (attempt + 1))
                continue
            status = r.status_code
            if status == 200:
                try:
                    rec = r.json()
                except Exception:
                    rec = None
                break
            if status == 404:
                break
            if status == 429:
                msg = r.text[:200]
                if "budget" in msg.lower():
                    log("OpenAlex budget refusal on singleton:", msg)
                    return None          # do not cache; budget issue
                # the 10 requests/second ceiling is shared by every process on this network address
                time.sleep(0.6 + random.random() * 1.2)
                continue
            time.sleep(3 * (min(attempt, 4) + 1))
        if status not in (200, 404):
            return None
        if rec is not None:
            rec["abstract"] = invert_abstract(rec.get("abstract_inverted_index"))
            for k in self.DROP:
                rec.pop(k, None)
        with self.wlock:
            self.idx[key] = rec
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "rec": rec}, ensure_ascii=False) + "\n")
        return rec

    def fetch_many(self, keys, select=None, threads=4, label="openalex"):
        from concurrent.futures import ThreadPoolExecutor
        todo = [k for k in dict.fromkeys(keys) if k not in self.idx]
        log(f"[{label}] {len(keys)} keys, {len(todo)} to fetch")
        done = [0]

        def work(k):
            self.fetch(k, select)
            done[0] += 1
            if done[0] % 500 == 0:
                log(f"[{label}] {done[0]}/{len(todo)}")
        if todo:
            with ThreadPoolExecutor(threads) as ex:
                list(ex.map(work, todo))
        return {k: self.idx.get(k) for k in keys}


# ---------- Semantic Scholar ----------
S2 = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = ("title,abstract,year,venue,publicationVenue,publicationTypes,publicationDate,externalIds,"
             "citationCount,referenceCount,authors.name,authors.authorId,authors.affiliations,openAccessPdf,"
             "fieldsOfStudy,journal,"
             "references.paperId,references.title,references.year,references.venue,references.authors,"
             "references.externalIds")
S2_LIGHT = ("title,abstract,year,venue,publicationTypes,publicationDate,externalIds,citationCount,"
            "referenceCount,authors.name,authors.authorId,openAccessPdf,fieldsOfStudy,journal")


def s2_bulk(query, year=None, fos=None, cap=3000, sort=None, tag="q"):
    """Semantic Scholar bulk search (title+abstract boolean query). Returns (total, records)."""
    out, token, page, total = [], None, 0, None
    while True:
        params = {"query": query, "fields": S2_LIGHT}
        if year:
            params["year"] = year
        if fos:
            params["fieldsOfStudy"] = fos
        if sort:
            params["sort"] = sort
        if token:
            params["token"] = token
        d = cached_fetch(S2 + "/paper/search/bulk", f"s2/bulk_{tag}_{qhash(query, year, fos, sort)}_p{page}.json.gz",
                         params=params, host="s2", min_gap=3.0, retries=8, backoff=6)
        if d is None:
            break
        total = d.get("total", total)
        out.extend(d.get("data") or [])
        token = d.get("token")
        page += 1
        if not token or len(out) >= cap:
            break
    return total, out[:cap]


def s2_batch(ids, fields=S2_FIELDS, chunk=40, tag="full"):
    """POST /paper/batch. ids like 'DOI:..', 'ARXIV:..', 'ACL:..', or S2 paperId. Returns dict id->rec."""
    res = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        d = cached_fetch(S2 + "/paper/batch", f"s2/batch_{tag}_{qhash(*part)}.json.gz",
                         params={"fields": fields}, host="s2", min_gap=3.0, retries=10,
                         method="POST", body={"ids": part}, backoff=8, timeout=180)
        if d is None:
            # try smaller pieces once
            if len(part) > 5:
                res.update(s2_batch(part, fields, chunk=max(5, len(part) // 4), tag=tag))
            continue
        for k, v in zip(part, d):
            res[k] = v
        if (i // chunk) % 10 == 0:
            log(f"[s2 batch {tag}] {min(i + chunk, len(ids))}/{len(ids)}")
    return res


def s2_citations(pid, cap=3000):
    out, offset = [], 0
    while offset < cap:
        d = cached_fetch(S2 + f"/paper/{pid}/citations", f"s2/cit_{qhash(pid)}_{offset}.json.gz",
                         params={"fields": "title,year,externalIds,citationCount,abstract", "limit": 1000,
                                 "offset": offset},
                         host="s2", min_gap=3.0, retries=10, backoff=8)
        if d is None:
            break
        rows = [x.get("citingPaper") for x in d.get("data") or [] if x.get("citingPaper")]
        out.extend(rows)
        if d.get("next") is None or not rows:
            break
        offset = d["next"]
    return out


def s2_key(rec):
    """Preferred lookup keys for a candidate record."""
    if rec.get("s2id"):
        return rec["s2id"]
    if rec.get("arxiv"):
        return "ARXIV:" + re.sub(r"v\d+$", "", rec["arxiv"])
    if rec.get("acl"):
        return "ACL:" + rec["acl"]
    if rec.get("doi"):
        return "DOI:" + rec["doi"]
    return None
