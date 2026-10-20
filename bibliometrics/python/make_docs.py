"""Compose figures/captions.md and search-protocol.md from the JSON/CSV the pipeline wrote.
Usage: python make_docs.py
(README.md, scopus-queries.md and gap-analysis.md are written by hand and are not touched.)
"""
import glob
import json
import os
import re

from bm_common import BASE, CLEAN, FIG, RAW, load_config

CFG = load_config()
TERMS = CFG.get("terms", {})


def sub(s):
    for _ in range(3):
        for k, v in TERMS.items():
            s = s.replace("{" + k + "}", v)
    return s


def jload(name, default=None):
    p = os.path.join(CLEAN, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else (default if default is not None else {})


# ------------------------------------------------------------ captions
caps = []
order = CFG.get("caption_order") or sorted(glob.glob(os.path.join(FIG, "captions_*.json")))
for fn in order:
    fn = fn if os.path.isabs(fn) else os.path.join(FIG, fn)
    if os.path.exists(fn):
        caps += json.load(open(fn, encoding="utf-8"))
out = ["# Figure captions", "",
       f"{len(caps)} figures. Each entry: what it shows, the data and settings that produced it, and one caution.",
       "PNG files are 220 dpi. Scripts: `R/02_bibliometrix.R` (files starting with a letter code and a number, e.g. R02_),",
       "`python/figures_py.py` (P..), `python/vosviewer_export.py` (V_..), plus any task-specific script named in the entry.", ""]
for c in caps:
    f = c["file"]
    exts = [e for e in (".png", ".svg", ".html") if os.path.exists(os.path.join(FIG, f + e))]
    name = f if os.path.exists(os.path.join(FIG, f)) else f + (exts[0] if exts else ".png")
    also = [f + e for e in exts[1:]] if not os.path.exists(os.path.join(FIG, f)) else []
    missing = "" if (exts or os.path.exists(os.path.join(FIG, f))) else "  **(file not produced - see README limits)**"
    out += [f"## {name}{missing}", f"- **Title:** {c['title']}", f"- **Shows:** {c['what']}",
            f"- **Data and settings:** {c['how']}", f"- **Caution:** {c['caution']}"]
    if also:
        out.append(f"- **Also saved as:** {', '.join(also)}")
    out.append("")
open(os.path.join(FIG, "captions.md"), "w", encoding="utf-8").write("\n".join(out))
print("captions:", len(caps))

# ------------------------------------------------------------ search protocol
sc, p1, p2, cov = jload("search_counts.json"), jload("prisma_stage1.json"), jload("prisma_stage2.json"), jload("coverage.json")
if not sc:
    raise SystemExit("no search_counts.json - protocol not rebuilt")
log = open(os.path.join(BASE, "data", "fetch-log.txt"), encoding="utf-8").read().splitlines()
date0 = log[0][:10] if log else "unknown"
L = [f"# Search protocol - {CFG['name']}", "",
     f"- **Date of search:** {date0} (UTC). Years covered: {CFG['year_min']}-{CFG['year_max']} ({CFG['year_max']} incomplete).",
     "- **Who screened:** rule-based screening by the regular expressions below, followed by a hand check of titles by the mapping agent (an AI assistant), not by a human reviewer. Sean should re-screen the core set himself before citing counts.",
     "- **No API keys, no logins.** Every response is cached in `data/raw/`.", ""]
L += ["## 1. Databases and what each was used for", ""]
L += [f"- {x}" for x in CFG.get("protocol_databases", [])]
L += ["", "## 2. Exact search strings and hits", ""]
names = {"semantic_scholar": "Semantic Scholar bulk search (title + abstract; `+` = AND, `|` = OR; year filter %d-%d)" % (CFG["year_min"], CFG["year_max"]),
         "crossref": "Crossref `query.bibliographic` (relevance-ranked free text, no Boolean; top results taken per string, then screened locally)",
         "acl_anthology": "ACL Anthology full BibTeX export with abstracts (screened locally with the rules in section 3)",
         "arxiv": "arXiv API (`abs:` = abstract field)", "dblp": "DBLP search API", "openalex": "OpenAlex"}
for db, qs in sc.items():
    L += [f"### {names.get(db, db)}", "", "| Tag | Sub-literature | Query | Hits reported | Records taken |", "|---|---|---|---|---|"]
    for tag, q in qs.items():
        code = tag[0] if tag[0] in CFG["sublits"] else ""
        lab = CFG["sublits"].get(code, {}).get("label", "-")
        extra = f" **({q['status']})**" if q.get("status") else ""
        L.append(f"| {tag} | {lab} | `{q['query'].replace('|', chr(92) + '|')}`{extra} | {q.get('total_reported') if q.get('total_reported') is not None else 'n/a'} | {q.get('fetched')} |")
    L.append("")
L += ["## 3. Inclusion rules (applied to title + abstract, case-insensitive)", "",
      "A record is included if it matches **at least one** sub-literature rule. Within a rule every numbered group must match.", ""]
for code, sl in CFG["sublits"].items():
    L.append(f"**{code}. {sl['label']}**")
    alts = sl.get("rule_any") or [sl["rule"]]
    for i, alt in enumerate(alts):
        if len(alts) > 1:
            L.append(f"- Alternative {i + 1} (any alternative is enough):")
        for j, g in enumerate(alt, 1):
            L.append(f"  {j}. `{sub(g[2:])}` (must match in the **title**)" if g.startswith("T:") else f"  {j}. `{sub(g)}`")
    L.append("")
L += ["## 4. Exclusion rules", "", f"- Publication year outside {CFG['year_min']}-{CFG['year_max']}.",
      "- No sub-literature rule matched on title + abstract (the database search engines match more loosely than the rules)."]
if CFG.get("exclude_title_regex"):
    L.append(f"- Title rules: {CFG.get('exclude_note', '')}")
    for g in CFG["exclude_title_regex"]:
        L.append(f"  - `{sub(g)}`")
for g in CFG.get("exclude_text_regex", []):
    L.append(f"- Text rule (title or abstract): `{sub(g)}`")
L += ["- Hand screen: records listed in `data/clean/excluded_manual.csv`, each with its reason.",
      "- Versions: a preprint and its published version are one record (merged by Semantic Scholar paper ID, DOI, arXiv ID, ACL ID, then by normalised title + first-author surname).", ""]
L += ["## 5. Snowballing (one round)", ""]
if p2:
    L += [f"- Central papers: the {len(p2.get('central_papers', []))} most locally cited documents after the first screen, plus named seed papers.",
          f"- Backward (their references not yet in the corpus): {p2.get('backward_candidates')} candidates.",
          f"- Forward (papers citing them, Semantic Scholar citations endpoint, capped per paper): {p2.get('forward_candidates')} candidates.",
          f"- Screened with the same rules: {p2.get('snowball_unique_candidates')} unique candidates, {p2.get('snowball_excluded_by_rule')} excluded, **{p2.get('snowball_added')} added**.", ""]
else:
    L += ["- Not run for this corpus (see README).", ""]
L += ["## 6. PRISMA-style counts", "", "| Step | Records |", "|---|---|"]
for k, v in (p1.get("records_identified_per_source") or {}).items():
    L.append(f"| Identified: {k.replace('_', ' ')} | {v} |")
L += [f"| **Identified, all sources** | **{p1.get('records_identified_total')}** |",
      f"| Duplicates removed (same ID or same title across sources and queries) | {p1.get('duplicates_removed_stage1')} |",
      f"| Unique records screened | {p1.get('unique_after_merge')} |",
      f"| Excluded by rule (off-topic, year, front matter, modality) | {p1.get('excluded_by_rule')} |"]
for k, v in (p1.get("excluded_reasons") or {}).items():
    L.append(f"| &nbsp;&nbsp;&nbsp;- {k} | {v} |")
L += [f"| Passed the rules | {p1.get('included_before_version_merge')} |",
      f"| Further version duplicates merged after ID resolution | {p1.get('version_duplicates_merged_by_s2_or_title')} |",
      f"| Named seed papers added although no search found them | {p1.get('seeds_forced_in')} |",
      f"| Corpus after first screen | {p1.get('after_screen')} |"]
if p2:
    L.append(f"| Added by snowballing | {p2.get('snowball_added')} |")
L += [f"| Removed in hand screen | {cov.get('manual_exclusions')} |",
      f"| **Final corpus** | **{cov.get('final_corpus')}** |", ""]
L += ["## 7. Coverage of the final corpus", "", "| Field | Documents | Share |", "|---|---|---|"]
n = cov.get("final_corpus") or 1
for k in ("with_abstract", "with_reference_list", "with_openalex_record", "with_institution", "with_country", "with_openalex_keywords",
          "with_doi", "with_arxiv_id", "with_acl_id", "with_dblp_key", "preprint_only", "records_with_preprint_and_published_version_merged"):
    if k in cov:
        L.append(f"| {k.replace('_', ' ')} | {cov[k]} | {100 * cov[k] / n:.1f}% |")
L += ["", f"- Reference links: {cov.get('reference_links')} in total, {cov.get('reference_links_in_corpus')} point to another corpus document.",
      f"- By sub-literature (a document can match several): {cov.get('by_sublit_nonexclusive')}",
      f"- By document type: {cov.get('by_doc_type')}", "", "## 8. Limits", ""]
L += [f"- {x}" for x in CFG.get("protocol_limits", [])]
open(os.path.join(BASE, "search-protocol.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("search-protocol.md written")
