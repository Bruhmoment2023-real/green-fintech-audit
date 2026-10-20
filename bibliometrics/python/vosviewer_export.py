"""Export VOSviewer-ready map + network files (tab-separated) built directly from the master table.

Networks: co-citation of cited references, co-authorship, keyword co-occurrence, direct citation,
bibliographic coupling of documents. Open in VOSviewer: Create... is NOT needed - use
File > Open... > "VOSviewer map file" + "VOSviewer network file" and pick the pair with the same prefix.

Usage: python vosviewer_export.py [render]
With "render", VOSviewer.exe is started once per network with -save_screenshot_png (its window opens
briefly; the process this script started is closed again as soon as the image exists).
"""
import os
import subprocess
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd
from scipy import sparse

from bm_common import BASE, CLEAN, FIG, TOOLS, au_short, load_config

OUT = os.path.join(BASE, "vosviewer")
os.makedirs(OUT, exist_ok=True)
CFG = load_config()
MAXN = int(CFG.get("vos_max_nodes", 400))

m = pd.read_csv(os.path.join(CLEAN, "master.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
refs = pd.read_csv(os.path.join(CLEAN, "references.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
m["year_n"] = pd.to_numeric(m.year, errors="coerce")
m["cit_n"] = pd.to_numeric(m.cited_by, errors="coerce").fillna(0)
doc_ix = {d: i for i, d in enumerate(m.id)}
summary = []


def clean(s):
    return str(s).replace("\t", " ").replace("\n", " ").replace('"', "'").strip()


def write_pair(prefix, items, labels, pairs, weights=None, scores=None, extra=None, desc=""):
    """items: list of keys; pairs: dict (i,j)->strength with i<j as item indices."""
    cols = ["id", "label"]
    data = {"id": range(1, len(items) + 1), "label": [clean(l) for l in labels]}
    for k, v in (weights or {}).items():
        data[f"weight<{k}>"] = v
    for k, v in (scores or {}).items():
        data[f"score<{k}>"] = v
    for k, v in (extra or {}).items():
        data[k] = [clean(x) for x in v]
    pd.DataFrame(data).to_csv(os.path.join(OUT, f"{prefix}_map.txt"), sep="\t", index=False, encoding="utf-8")
    with open(os.path.join(OUT, f"{prefix}_network.txt"), "w", encoding="utf-8") as f:
        for (i, j), s in sorted(pairs.items()):
            f.write(f"{i + 1}\t{j + 1}\t{s:g}\n")
    summary.append({"network": prefix, "items": len(items), "links": len(pairs), "what": desc})
    print(prefix, len(items), "items", len(pairs), "links")


def cooc(rows, cols, n_rows, n_cols, min_strength=1):
    """rows/cols index arrays of an incidence matrix (documents x items) -> upper-triangle co-occurrence dict."""
    A = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_rows, n_cols))
    A.data[:] = 1
    C = (A.T @ A).tocoo()
    return {(int(i), int(j)): float(v) for i, j, v in zip(C.row, C.col, C.data) if i < j and v >= min_strength}


def pick(counter, max_n, min_count):
    thr = min_count
    while sum(1 for v in counter.values() if v >= thr) > max_n:
        thr += 1
    keep = [k for k, v in counter.most_common() if v >= thr]
    return keep, thr


# ---- 1 co-citation of references
r = refs[refs.cr != ""].copy()
r["key"] = r.cited.where(r.cited != "", r.cr)
r = r.drop_duplicates(["citing", "key"])
cnt = Counter(r.key)
keep, thr = pick(cnt, MAXN, 3)
if len(keep) >= 10:
    kix = {k: i for i, k in enumerate(keep)}
    rr = r[r.key.isin(kix)]
    info = rr.drop_duplicates("key").set_index("key")

    def lab(k):
        x = info.loc[k]
        fa = (x.cited_first_author.split(" ") or ["?"])[-1] if x.cited_first_author else "Anon"
        return f"{fa} ({x.cited_year})"
    pairs = cooc(rr.citing.map(doc_ix).values, rr.key.map(kix).values, len(m), len(keep), 2)
    write_pair("cocitation_references", keep, [lab(k) for k in keep], pairs,
               weights={"Citations in corpus": [cnt[k] for k in keep]},
               scores={"Pub. year": [info.loc[k].cited_year or "" for k in keep]},
               extra={"description": [info.loc[k].cited_title for k in keep],
                      "url": [("https://doi.org/" + info.loc[k].cited_doi) if info.loc[k].cited_doi else (
                          "https://arxiv.org/abs/" + info.loc[k].cited_arxiv if info.loc[k].cited_arxiv else "") for k in keep]},
               desc=f"cited references with >= {thr} citing corpus documents; link = times cited together (>= 2)")

# ---- 2 co-authorship
au_rows, au_names = [], []
for i, a in enumerate(m.authors):
    for n in dict.fromkeys(x.strip() for x in a.split(";") if x.strip()):
        au_rows.append(i)
        au_names.append(n)
aud = pd.DataFrame({"doc": au_rows, "name": au_names})
aud["key"] = aud.name.map(au_short)
cnt = Counter(aud.key)
keep, thr = pick(cnt, MAXN, 2)
if len(keep) >= 10:
    kix = {k: i for i, k in enumerate(keep)}
    aa = aud[aud.key.isin(kix)].drop_duplicates(["doc", "key"])
    disp = aa.groupby("key").name.agg(lambda s: s.value_counts().index[0])
    pairs = cooc(aa.doc.values, aa.key.map(kix).values, len(m), len(keep), 1)
    cit = aa.assign(c=aa.doc.map(lambda d: m.cit_n.iloc[d]), y=aa.doc.map(lambda d: m.year_n.iloc[d])).groupby("key").agg(c=("c", "sum"), y=("y", "mean"))
    write_pair("coauthorship_authors", keep, [disp[k] for k in keep], pairs,
               weights={"Documents": [cnt[k] for k in keep], "Citations": [int(cit.c[k]) for k in keep]},
               scores={"Avg. pub. year": [round(cit.y[k], 2) for k in keep]},
               desc=f"authors with >= {thr} corpus documents; link = co-authored documents")

# ---- 3 keyword co-occurrence
kwcol = "author_keywords" if ("author_keywords" in m.columns and (m.author_keywords != "").mean() > 0.5) else "openalex_keywords"
k_rows, k_vals = [], []
drop = {x.lower() for x in CFG.get("remove_keywords", [])}
for i, a in enumerate(m[kwcol]):
    for n in dict.fromkeys(x.strip().lower() for x in a.split(";") if x.strip()):
        if n not in drop:
            k_rows.append(i)
            k_vals.append(n)
kd = pd.DataFrame({"doc": k_rows, "key": k_vals})
cnt = Counter(kd.key)
keep, thr = pick(cnt, MAXN, 3)
if len(keep) >= 10:
    kix = {k: i for i, k in enumerate(keep)}
    kk = kd[kd.key.isin(kix)]
    pairs = cooc(kk.doc.values, kk.key.map(kix).values, len(m), len(keep), 1)
    agg = kk.assign(c=kk.doc.map(lambda d: m.cit_n.iloc[d]), y=kk.doc.map(lambda d: m.year_n.iloc[d])).groupby("key").agg(c=("c", "mean"), y=("y", "mean"))
    write_pair("keyword_cooccurrence", keep, keep, pairs, weights={"Occurrences": [cnt[k] for k in keep]},
               scores={"Avg. pub. year": [round(agg.y[k], 2) for k in keep], "Avg. citations": [round(agg.c[k], 2) for k in keep]},
               desc=f"{kwcol.replace('_', ' ')} with >= {thr} documents; link = documents carrying both")

# ---- 4 direct citation between corpus documents
m["lc"] = pd.to_numeric(m.local_citations, errors="coerce").fillna(0)
e = refs[(refs.in_corpus == "1") & (refs.citing != refs.cited)].drop_duplicates(["citing", "cited"])
deg = Counter(e.citing) + Counter(e.cited)
cand = m[m.id.map(lambda d: deg.get(d, 0) > 0)].sort_values("lc", ascending=False).head(MAXN)
if len(cand) >= 10:
    kix = {k: i for i, k in enumerate(cand.id)}
    ee = e[e.citing.isin(kix) & e.cited.isin(kix)]
    pairs = {}
    for a, b in zip(ee.citing.map(kix), ee.cited.map(kix)):
        pairs[(min(a, b), max(a, b))] = 1

    def dl(x):
        fa = (x.authors.split(";")[0].strip().split(" ") or ["?"])[-1]
        return f"{fa} ({x.year})"
    write_pair("direct_citation_documents", list(cand.id), [dl(x) for x in cand.itertuples()], pairs,
               weights={"Local citations": cand.lc.astype(int).tolist(), "Citations": cand.cit_n.astype(int).tolist()},
               scores={"Pub. year": cand.year.tolist()},
               extra={"description": cand.title.tolist(), "url": cand.url.tolist()},
               desc=f"{len(cand)} most locally cited corpus documents; link = one cites the other")

# ---- 5 bibliographic coupling (documents sharing references)
r2 = refs[refs.cr != ""].copy()
r2["key"] = r2.cited.where(r2.cited != "", r2.cr)
r2 = r2.drop_duplicates(["citing", "key"])
cand = m[m.id.isin(set(r2.citing))].sort_values("cit_n", ascending=False).head(MAXN)
if len(cand) >= 10:
    kix = {k: i for i, k in enumerate(cand.id)}
    rr = r2[r2.citing.isin(kix)]
    rix = {k: i for i, k in enumerate(rr.key.unique())}
    A = sparse.csr_matrix((np.ones(len(rr)), (rr.citing.map(kix).values, rr.key.map(rix).values)), shape=(len(cand), len(rix)))
    C = (A @ A.T).tocoo()
    pairs = {(int(i), int(j)): float(v) for i, j, v in zip(C.row, C.col, C.data) if i < j and v >= 3}
    write_pair("bibliographic_coupling_documents", list(cand.id),
               [f"{(x.authors.split(';')[0].strip().split(' ') or ['?'])[-1]} ({x.year})" for x in cand.itertuples()], pairs,
               weights={"Citations": cand.cit_n.astype(int).tolist(), "References": pd.to_numeric(cand.refs_listed).tolist()},
               scores={"Pub. year": cand.year.tolist()}, extra={"description": cand.title.tolist(), "url": cand.url.tolist()},
               desc=f"{len(cand)} most cited corpus documents with a reference list; link = shared references (>= 3)")

pd.DataFrame(summary).to_csv(os.path.join(OUT, "vosviewer_files.csv"), index=False)

# ---- optional: let VOSviewer itself lay out, cluster and screenshot each network
if len(sys.argv) > 1 and sys.argv[1] == "render":
    exe = os.path.join(TOOLS, "VOSviewer", "VOSviewer.exe")
    res = []
    for s in summary:
        p = s["network"]
        png = os.path.join(FIG, f"V_{p}_vosviewer.png")
        jsn = os.path.join(OUT, f"{p}_vosviewer.json")
        for x in (png, jsn):
            if os.path.exists(x):
                os.remove(x)
        cmd = [exe, "-map", os.path.join(OUT, f"{p}_map.txt"), "-network", os.path.join(OUT, f"{p}_network.txt"),
               "-largest_component", "-save_json", jsn, "-save_screenshot_png", png, "-white_background", "true"]
        try:
            pr = subprocess.Popen(cmd, cwd=os.path.dirname(exe))
        except Exception as ex:
            res.append((p, "could not start: " + repr(ex)[:100]))
            break
        t0 = time.time()
        ok = False
        while time.time() - t0 < 150:
            time.sleep(3)
            if os.path.exists(png) and os.path.getsize(png) > 5000:
                time.sleep(4)
                ok = True
                break
            if pr.poll() is not None:
                break
        try:   # close only the process tree this script started
            subprocess.run(["taskkill", "/PID", str(pr.pid), "/T", "/F"], capture_output=True)
        except Exception:
            pass
        res.append((p, "rendered" if ok else "no image produced within 150 s"))
        print("VOSviewer", p, res[-1][1])
    pd.DataFrame(res, columns=["network", "vosviewer_render"]).to_csv(os.path.join(OUT, "vosviewer_render_status.csv"), index=False)
