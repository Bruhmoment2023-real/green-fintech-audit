"""Evidence table of the most relevant papers + open-access PDF download for the core set.

Usage: python evidence.py            -> writes evidence-table.csv (draft columns coded from the abstract)
       python evidence.py pdfs       -> also downloads legal open copies of the core papers into pdfs/
Relevance = weighted keyword rules in config.json -> "relevance" (title counts double) + local citations.
The 'main finding' cell is a sentence copied verbatim from the abstract - nothing is paraphrased or invented.
'method' and 'relation to the paper' come from data/clean/evidence_notes.csv (written after reading each abstract).
"""
import csv
import math
import os
import re
import sys
import time

import pandas as pd

from bm_common import BASE, CLEAN, SESSION, load_config, log

CFG = load_config()
m = pd.read_csv(os.path.join(CLEAN, "master.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
m["lc"] = pd.to_numeric(m.local_citations, errors="coerce").fillna(0)
m["gc"] = pd.to_numeric(m.cited_by, errors="coerce").fillna(0)
REL = [(re.compile(x["re"], re.I), x["w"]) for x in CFG.get("relevance", [])]
N_TABLE = int(CFG.get("evidence_n", 50))
N_PDF = int(CFG.get("pdf_n", 28))


def score(r):
    s = 0.0
    for rx, w in REL:
        if rx.search(r.title):
            s += 2 * w
        elif rx.search(r.abstract):
            s += w
    return s + 1.5 * math.log1p(r.lc) + 0.3 * math.log1p(r.gc)


m["relevance"] = m.apply(score, axis=1)
if "forced_seed" in m.columns:
    m.loc[m.forced_seed == "1", "relevance"] += float(CFG.get("seed_bonus", 4))
top = m.sort_values("relevance", ascending=False).head(N_TABLE).copy()

CUES = re.compile(r"\b(we find|we found|we show|we observe|we demonstrate|results? (show|indicate|reveal|suggest|demonstrate)|"
                  r"our (results|findings|experiments|analysis|evaluation)|findings|reveals?|outperform\w*|achiev\w*|improv\w*|"
                  r"degrad\w*|drop\w*|gap|significant\w*|accuracy|f1|bleu|percent|%|consistently|substantial\w*|"
                  r"struggle\w*|underperform\w*|increase\w*|decrease\w*|decline\w*|rose|fell)\b", re.I)


def finding(abst):
    if not abst:
        return ""
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", abst.strip())
    best, bs = "", 0
    for i, s in enumerate(sents):
        if len(s) < 40:
            continue
        sc = len(CUES.findall(s)) + (0.5 if re.search(r"\d", s) else 0) + (0.3 if i >= len(sents) / 2 else 0)
        if sc > bs:
            best, bs = s, sc
    best = best or sents[-1]
    return best if len(best) <= 420 else best[:417] + "..."


TYPES = [("survey / review", r"\b(survey|review|overview of the|systematic(ally)? review|scoping review|meta-analysis|bibliometric)\b"),
         ("position / perspective", r"\b(position paper|perspective|we argue|viewpoint|commentary|opinion)\b"),
         ("shared task", r"\bshared task\b"),
         ("benchmark / dataset", r"\b(benchmark|dataset|corpus|test ?set|resource)\b"),
         ("empirical evaluation", r"\b(evaluat\w+|we (study|analy[sz]e|investigate|examine|measure)|empirical|interrupted time series|regression|difference-in-differences)\b"),
         ("method / model", r"\b(we propose|we present|we introduce|novel|approach|framework|method|model)\b")]


def study_type(t, a):
    for name, rx in TYPES:
        if re.search(rx, t, re.I):
            return name
    for name, rx in TYPES:
        if re.search(rx, a[:600], re.I):
            return name
    return "other"


def tags(text, d):
    out = [k for k, rx in d.items() if re.search(rx, text, re.I)]
    return "; ".join(out)


LANG = (CFG.get("heatmap") or {}).get("rows", {}) if CFG.get("evidence_data_from") != "data_terms" else CFG.get("data_terms", {})
if CFG.get("data_terms"):
    LANG = CFG["data_terms"]
MODELS = CFG.get("model_terms", {})
notes = {}
np_ = os.path.join(CLEAN, "evidence_notes.csv")
if os.path.exists(np_):
    for row in csv.DictReader(open(np_, encoding="utf-8-sig")):
        notes[row["id"]] = row

rows = []
for r in top.itertuples():
    text = r.title + " . " + r.abstract
    n = notes.get(r.id, {})
    authors = [a.strip() for a in r.authors.split(";") if a.strip()]
    au = ", ".join(authors[:6]) + (" et al." if len(authors) > 6 else "")
    rows.append({
        "rank": len(rows) + 1, "relevance_score": round(r.relevance, 2),
        "citation": f"{au} ({r.year}). {r.title}. {r.venue}.",
        "doi_or_arxiv": ("https://doi.org/" + r.doi) if r.doi and not r.doi.startswith("10.48550") else (
            "https://arxiv.org/abs/" + r.arxiv_id if r.arxiv_id else ("https://doi.org/" + r.doi if r.doi else r.url)),
        "open_access_link": r.oa_pdf_url,
        "study_type": n.get("study_type") or study_type(r.title, r.abstract),
        CFG.get("evidence_data_label", "languages_or_data"): n.get("data") or tags(text, LANG),
        CFG.get("evidence_models_label", "models_named_in_abstract"): n.get("models") or tags(text, MODELS),
        "method": n.get("method", ""),
        "main_finding_verbatim_from_abstract": finding(r.abstract),
        "read_status": n.get("read_status") or ("abstract read" if r.abstract else "title only - no abstract available"),
        "relation_to_this_paper": n.get("relation", ""),
        "sub_literature": r.sublits, "local_citations": int(r.lc), "global_citations": int(r.gc), "id": r.id,
    })
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(BASE, "evidence-table.csv"), index=False, encoding="utf-8-sig")
top[["id", "title", "year", "venue", "authors", "abstract", "sublits", "lc", "gc", "relevance", "url"]].to_csv(
    os.path.join(CLEAN, "evidence_candidates_with_abstracts.csv"), index=False, encoding="utf-8-sig")
print("evidence table rows:", len(ev))

if len(sys.argv) > 1 and sys.argv[1] == "pdfs":
    pdir = os.path.join(BASE, "pdfs")
    os.makedirs(pdir, exist_ok=True)
    logrows, total = [], 0
    budget = 300 * 1024 * 1024
    order = list(top.head(N_PDF).itertuples())
    for i, r in enumerate(order, 1):
        fa = re.sub(r"[^A-Za-z]", "", (r.authors.split(";")[0].strip().split(" ") or ["x"])[-1])[:20] or "anon"
        slug = re.sub(r"[^a-z0-9]+", "-", r.title.lower())[:50].strip("-")
        fn = f"{i:02d}_{fa}_{r.year}_{slug}.pdf"
        path = os.path.join(pdir, fn)
        cands = []
        if r.arxiv_id:
            cands.append(("arXiv", "https://arxiv.org/pdf/" + r.arxiv_id))
        if r.acl_id:
            cands.append(("ACL Anthology", f"https://aclanthology.org/{r.acl_id}.pdf"))
        if r.oa_pdf_url and "arxiv.org" not in r.oa_pdf_url and "aclanthology" not in r.oa_pdf_url:
            cands.append(("publisher/repository OA link from database", r.oa_pdf_url))
        if os.path.exists(path):
            total += os.path.getsize(path)
            logrows.append([i, r.title, fn, "already present", "", os.path.getsize(path)])
            continue
        status, used = "no legal open copy found", ""
        for src, url in cands:
            if total > budget:
                status = "skipped: folder size budget reached"
                break
            try:
                time.sleep(4 if "arxiv" in url else 1.5)
                resp = SESSION.get(url, timeout=90, allow_redirects=True)
                if resp.status_code == 200 and resp.content[:5] == b"%PDF-" and len(resp.content) < 40 * 1024 * 1024:
                    open(path, "wb").write(resp.content)
                    total += len(resp.content)
                    status, used = "downloaded", f"{src}: {url}"
                    break
                status = f"failed ({src}: HTTP {resp.status_code}, not a PDF or too large)"
            except Exception as e:
                status = f"failed ({src}: {repr(e)[:80]})"
        logrows.append([i, r.title, fn if status == "downloaded" else "", status, used, os.path.getsize(path) if os.path.exists(path) else 0])
        print(i, status, r.title[:60])
    with open(os.path.join(pdir, "pdf-download-log.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["rank", "title", "file", "status", "source", "bytes"])
        w.writerows(logrows)
    log(f"[pdfs] {sum(1 for x in logrows if x[3] in ('downloaded', 'already present'))} of {len(logrows)} core papers saved, {total/1e6:.1f} MB")
