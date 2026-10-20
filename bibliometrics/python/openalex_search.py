"""OpenAlex list/search queries (title_and_abstract.search) for the strings in config.json -> "openalex_search".

Why this is separate: without an API key, OpenAlex list queries cost 10 credits each against a
1,000-credit daily budget shared by the whole network address (single-work lookups cost 0, which is
what the main pipeline uses). On the day of the pull that shared budget was already spent, so this
script is run right after the midnight-UTC reset, with a page cap so other users keep most of it.

Usage: python openalex_search.py [max_pages_total]
Optional: set OPENALEX_API_KEY in the environment (free key from openalex.org - needs a sign-up, so
it was NOT used for this pull) to lift the cap.
Output: data/raw/openalex_search/<tag>_p<N>.json.gz and data/clean/openalex_search_hits.csv
"""
import csv
import gzip
import json
import os
import sys
import time

from bm_common import BASE, CLEAN, MAIL, RAW, SESSION, invert_abstract, load_config, log, norm_doi

SELECT = ("id,doi,title,publication_year,publication_date,type,language,cited_by_count,primary_location,"
          "authorships,keywords,primary_topic,referenced_works,abstract_inverted_index,open_access,ids,biblio")


def run(max_pages):
    cfg = load_config()
    out_dir = os.path.join(RAW, "openalex_search")
    os.makedirs(out_dir, exist_ok=True)
    key = os.environ.get("OPENALEX_API_KEY")
    used, status = 0, {}
    for q in cfg.get("openalex_search", []):
        tag, cursor, page, n, total = q["tag"], "*", 0, 0, None
        while cursor:
            path = os.path.join(out_dir, f"{tag}_p{page}.json.gz")
            if os.path.exists(path):
                d = json.load(gzip.open(path, "rt", encoding="utf-8"))
            else:
                if used >= max_pages:
                    status[tag] = f"stopped at page cap after {n} of {total} records"
                    break
                flt = "title_and_abstract.search:" + q["search"] + ("," + q["filter"] if q.get("filter") else "")
                params = {"filter": flt, "per-page": 200, "page": page + 1, "select": SELECT, "mailto": MAIL}
                if key:
                    params["api_key"] = key
                r = SESSION.get("https://api.openalex.org/works", params=params, timeout=120)
                used += 1
                if r.status_code != 200:
                    status[tag] = f"HTTP {r.status_code}: {r.text[:160]}"
                    log("[openalex search]", tag, status[tag])
                    break
                d = r.json()
                with gzip.open(path, "wt", encoding="utf-8") as f:
                    f.write(r.text)
                time.sleep(0.3)
            total = d["meta"]["count"]
            n += len(d["results"])
            cursor = "more" if (d["results"] and n < total) else None  # page paging: cursor paging needs a key
            page += 1
        else:
            status[tag] = f"complete: {n} of {total} records"
        status.setdefault(tag, f"complete: {n} of {total} records")
        log("[openalex search]", tag, status[tag])
    # flatten everything cached so far
    rows, seen = [], set()
    for fn in sorted(os.listdir(out_dir)):
        tag = fn.rsplit("_p", 1)[0]
        d = json.load(gzip.open(os.path.join(out_dir, fn), "rt", encoding="utf-8"))
        for w in d["results"]:
            if (tag, w["id"]) in seen:
                continue
            seen.add((tag, w["id"]))
            src = ((w.get("primary_location") or {}).get("source") or {})
            rows.append({"tag": tag, "openalex_id": w["id"].rsplit("/", 1)[-1], "doi": norm_doi(w.get("doi")),
                         "title": w.get("title") or "", "year": w.get("publication_year"), "type": w.get("type"),
                         "source": src.get("display_name") or "", "cited_by": w.get("cited_by_count"),
                         "n_refs": len(w.get("referenced_works") or []),
                         "abstract": invert_abstract(w.get("abstract_inverted_index"))})
    if rows:
        with open(os.path.join(CLEAN, "openalex_search_hits.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    json.dump({"status": status, "pages_fetched_this_run": used, "rows": len(rows),
               "run_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())},
              open(os.path.join(CLEAN, "openalex_search_status.json"), "w"), indent=1)
    return used


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 15)
