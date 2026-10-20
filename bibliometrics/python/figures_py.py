"""Python figures: interactive citation network, key-paper timeline, year x sub-literature stack,
coded heat map (config "heatmap"), and a main-path (key-route) view of the direct citation network.

Usage: python figures_py.py
Reads data/clean/master.csv and references.csv; writes figures/P*.png|svg|html, tables/P*.csv and
figures/captions_P.json.
"""
import json
import os
import re
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from bm_common import BASE, CLEAN, FIG, TAB, load_config

CFG = load_config()
PAL = ["#1b6ca8", "#d1495b", "#2e933c", "#edae49", "#6a4c93", "#00798c", "#8d6e63", "#e76f51"]
plt.rcParams.update({"font.size": 10, "axes.titlesize": 13, "axes.titleweight": "bold", "figure.dpi": 100,
                     "savefig.dpi": 220, "axes.spines.top": False, "axes.spines.right": False})
CAPS = []


def cap(file, title, what, how, caution):
    CAPS.append({"file": file, "title": title, "what": what, "how": how, "caution": caution})


def save(fig, name, svg=False):
    fig.savefig(os.path.join(FIG, name + ".png"), bbox_inches="tight", facecolor="white")
    if svg:
        fig.savefig(os.path.join(FIG, name + ".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


m = pd.read_csv(os.path.join(CLEAN, "master.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
for c in ("year", "cited_by", "local_citations", "refs_listed"):
    m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0).astype(int)
refs = pd.read_csv(os.path.join(CLEAN, "references.csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
N = len(m)
SUBL = {k: v["label"] for k, v in CFG["sublits"].items()}
SUBL.setdefault("seed", "Named seed paper outside the rules")
SUBL.setdefault("Z", "Other / none of the coded themes")
COL = {k: PAL[i % len(PAL)] for i, k in enumerate(SUBL)}
SRC = f"Corpus: {N} documents, {m.year[m.year > 0].min()}-{m.year.max()}."
by_id = m.set_index("id")


def short(row, n=38):
    fa = (row["authors"].split(";")[0].strip().split(" ") or ["?"])[-1]
    t = row["title"]
    t = t if len(t) <= n else t[:n - 1].rstrip() + "…"
    return f"{fa} {row['year']}: {t}"


# ---------------------------------------------------------------- direct citation graph
ids = set(m.id)
E = refs[(refs.in_corpus == "1") & refs.cited.isin(ids) & refs.citing.isin(ids) & (refs.citing != refs.cited)][["citing", "cited"]].drop_duplicates()
G = nx.DiGraph()
G.add_nodes_from(m.id)
G.add_edges_from(zip(E.cited, E.citing))          # edge direction: cited (older) -> citing (newer) = knowledge flow
print("citation graph:", G.number_of_nodes(), "nodes,", G.number_of_edges(), "edges")

# ---------------------------------------------------------------- P1 interactive + static citation network
top_n = min(300, N)
core = list(m.sort_values(["local_citations", "cited_by"], ascending=False).head(top_n).id)
H = G.subgraph(core).copy()
H.remove_nodes_from([n for n in list(H) if H.degree(n) == 0])
try:
    from pyvis.network import Network
    net = Network(height="900px", width="100%", directed=True, bgcolor="#ffffff", font_color="#222", cdn_resources="in_line",
                  heading="")
    for n in H:
        r = by_id.loc[n]
        net.add_node(n, label=short(r, 26), title=f"{r['title']}<br>{r['authors'][:120]}<br>{r['venue']} ({r['year']})<br>"
                     f"local citations: {r['local_citations']} | global: {r['cited_by']}<br>sub-literature: {SUBL.get(r['primary_sublit'], r['primary_sublit'])}<br>{r['url']}",
                     size=6 + 3.2 * np.sqrt(r["local_citations"]), color=COL.get(r["primary_sublit"], "#999"))
    for u, v in H.edges():
        net.add_edge(u, v, color="#bbbbbb", width=0.5)
    net.barnes_hut(gravity=-6000, spring_length=120, damping=0.5)
    net.set_options('{"physics":{"stabilization":{"iterations":250}},"edges":{"arrows":{"to":{"enabled":true,"scaleFactor":0.4}},"smooth":false},"interaction":{"hover":true,"tooltipDelay":100}}')
    html = net.generate_html()
    legend = "".join(f'<span style="display:inline-block;width:12px;height:12px;background:{COL[k]};margin:0 4px 0 14px"></span>{k}: {v}' for k, v in SUBL.items() if k in set(m.primary_sublit))
    head = (f'<div style="font-family:sans-serif;padding:10px 14px"><b>Direct citation network of the {H.number_of_nodes()} most locally cited documents</b> '
            f'({SRC}) Arrow = cited paper &rarr; citing paper. Node size = citations from inside the corpus. Hover for details; drag and zoom.<br>{legend}</div>')
    html = html.replace("<body>", "<body>" + head, 1)
    open(os.path.join(FIG, "P01_citation_network.html"), "w", encoding="utf-8").write(html)
except Exception as e:
    print("pyvis failed:", e)
fig, ax = plt.subplots(figsize=(13, 10))
K = H.to_undirected()
comp = max(nx.connected_components(K), key=len) if K.number_of_nodes() else set()
K = K.subgraph(comp)
pos = nx.spring_layout(K, k=1.6 / np.sqrt(max(K.number_of_nodes(), 1)), seed=7, iterations=200)
nx.draw_networkx_edges(K, pos, ax=ax, alpha=0.15, width=0.5, edge_color="#555")
for k_, lab in SUBL.items():
    nodes = [n for n in K if by_id.loc[n, "primary_sublit"] == k_]
    if nodes:
        ax.scatter([pos[n][0] for n in nodes], [pos[n][1] for n in nodes], s=[18 + 14 * by_id.loc[n, "local_citations"] for n in nodes],
                   c=COL[k_], alpha=0.85, label=f"{k_}: {lab}", edgecolors="white", linewidths=0.4)
for n in sorted(K, key=lambda x: -by_id.loc[x, "local_citations"])[:28]:
    ax.annotate(short(by_id.loc[n], 30), pos[n], fontsize=6.5, ha="center", va="bottom")
ax.set_title(f"Direct citation network: largest connected component of the {top_n} most locally cited documents")
ax.set_xlabel("Force-directed layout, x (no unit)"); ax.set_ylabel("Force-directed layout, y (no unit)")
ax.set_xticks([]); ax.set_yticks([])
lg = ax.legend(title="Primary sub-literature (node size = local citations)", loc="lower left", fontsize=8, frameon=True)
for h in lg.legend_handles:
    h.set_sizes([60])
fig.text(0.01, 0.01, SRC, fontsize=7, color="grey")
save(fig, "P01_citation_network")
cap("P01_citation_network", "Direct citation network (PNG, and interactive HTML of the same name)",
    "Corpus documents as nodes, citations between them as links; colour = sub-literature, size = citations received from inside the corpus.",
    f"{SRC} Top {top_n} documents by local citations; {H.number_of_nodes()} are connected ({K.number_of_nodes()} in the largest component). Reference lists from Semantic Scholar/OpenAlex; networkx spring layout seed 7; pyvis for the HTML.",
    "Distances come from a force-directed layout and have no scale; papers without a reference list in the database look isolated even if they cite the field.")

# ---------------------------------------------------------------- P2 timeline of key papers
key = m.sort_values(["local_citations", "cited_by"], ascending=False).head(30).copy()
seedrows = m[(m.get("forced_seed", "0") == "1") & ~m.id.isin(key.id)]
key = pd.concat([key, seedrows.head(6)])
key["date"] = pd.to_datetime(key.pub_date.where(key.pub_date != "", key.year.astype(str) + "-07-01"), errors="coerce")
key = key.sort_values("date").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(15, 9))
lanes = 12
for i, r in key.iterrows():
    y = (i % lanes) + 1
    ax.plot([r.date, r.date], [0, y], color="#cccccc", lw=0.7, zorder=1)
    ax.scatter(r.date, y, s=30 + 9 * r.local_citations, color=COL.get(r.primary_sublit, "#999"), zorder=3, edgecolors="white")
    ax.annotate(short(r, 44) + f"  [{r.local_citations}]", (r.date, y), xytext=(6, 3), textcoords="offset points", fontsize=7)
ax.axhline(0, color="#333", lw=1)
ax.set_yticks([]); ax.set_ylabel("Stacking lane (no meaning; avoids label overlap)")
ax.set_xlabel("Publication date (first public version in the database)")
ax.set_title("Timeline of the field's key papers: the 30 most locally cited documents plus named seed papers")
hs = [plt.Line2D([], [], marker="o", ls="", color=COL[k], label=f"{k}: {v}") for k, v in SUBL.items() if k in set(key.primary_sublit)]
ax.legend(handles=hs, title="Primary sub-literature; [n] = citations from inside the corpus", loc="upper left", fontsize=8)
ax.set_xlim(key.date.min() - pd.Timedelta(days=120), key.date.max() + pd.Timedelta(days=700))
fig.text(0.01, 0.01, SRC, fontsize=7, color="grey")
save(fig, "P02_key_paper_timeline", svg=True)
key[["id", "title", "authors", "year", "pub_date", "venue", "local_citations", "cited_by", "primary_sublit", "url"]].to_csv(
    os.path.join(TAB, "P02_key_papers.csv"), index=False, encoding="utf-8-sig")
cap("P02_key_paper_timeline", "Timeline of key papers", "The 30 most locally cited documents (and any named seed papers) placed at their publication date.",
    f"{SRC} Ranked by citations from other corpus documents; date = Semantic Scholar publication date (mid-year if only the year is known).",
    "'Key' means most cited inside this corpus; very recent papers (2025-26) cannot have accumulated citations yet and are under-represented.")

# ---------------------------------------------------------------- P3 year x sub-literature stack
ys = m[m.year > 0]
piv = ys.pivot_table(index="year", columns="primary_sublit", values="id", aggfunc="count", fill_value=0)
piv = piv.reindex(range(int(piv.index.min()), int(piv.index.max()) + 1), fill_value=0)
piv.to_csv(os.path.join(TAB, "P03_year_by_sublit_exclusive.csv"), encoding="utf-8-sig")
nonex = defaultdict(Counter)
for _, r in ys.iterrows():
    for s in r.sublits.split(";"):
        if s:
            nonex[r.year][s] += 1
pd.DataFrame(nonex).T.sort_index().fillna(0).astype(int).to_csv(os.path.join(TAB, "P03_year_by_sublit_nonexclusive.csv"), encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(11, 6.5))
bottom = np.zeros(len(piv))
for k_ in [k for k in SUBL if k in piv.columns]:
    ax.bar(piv.index, piv[k_], bottom=bottom, color=COL[k_], label=f"{k_}: {SUBL[k_]} (n={int(piv[k_].sum())})", width=0.8)
    bottom += piv[k_].values
for x, t in zip(piv.index, bottom):
    ax.text(x, t + max(bottom) * 0.01, int(t), ha="center", fontsize=8)
ax.set_xticks(list(piv.index)); ax.tick_params(axis="x", rotation=45)
ax.set_xlabel("Publication year"); ax.set_ylabel("Documents in corpus")
ax.set_title("Publications by year and sub-literature")
ax.legend(title="Primary sub-literature (each document counted once; priority " + " > ".join(CFG.get("primary_sublit_priority", ["C", "B", "D", "A"])) + ")", fontsize=8, loc="upper left")
fig.text(0.01, -0.02, SRC + f" {m.year.max()} is an incomplete year.", fontsize=7, color="grey")
save(fig, "P03_publications_by_year_and_subfield", svg=True)
cap("P03_publications_by_year_and_subfield", "Publications by year and sub-literature", "Stacked annual counts, each document assigned to one sub-literature.",
    f"{SRC} Sub-literature assigned by the keyword rules in search-protocol.md; a document matching several rules is counted under the first in the stated priority order (non-exclusive counts in tables/P03_year_by_sublit_nonexclusive.csv).",
    "The split depends on the priority order and on the wording of the rules; the latest year is incomplete.")

# ---------------------------------------------------------------- P4 coded heat map
hm = CFG.get("heatmap")
if hm:
    text = (m.title + " . " + m.abstract)
    R = {k: re.compile(v, re.I) for k, v in hm["rows"].items()}
    C = {k: re.compile(v, re.I) for k, v in hm["cols"].items()}
    rhit = {k: text.apply(lambda t: bool(rx.search(t))) for k, rx in R.items()}
    chit = {k: text.apply(lambda t: bool(rx.search(t))) for k, rx in C.items()}
    mat = pd.DataFrame({c: {r: int((rhit[r] & chit[c]).sum()) for r in R} for c in C})
    mat["(any task)"] = [int(rhit[r].sum()) for r in R]
    tot = pd.Series({c: int(chit[c].sum()) for c in C}); tot["(any task)"] = N
    mat.loc["(any language)"] = tot
    mat.to_csv(os.path.join(TAB, "P04_heatmap_counts.csv"), encoding="utf-8-sig")
    body = mat.drop(index="(any language)").drop(columns="(any task)")
    order = body.sum(axis=1).sort_values(ascending=False).index
    body = body.loc[order]
    fig, ax = plt.subplots(figsize=(1.0 * len(C) + 4.5, 0.42 * len(R) + 3))
    im = ax.imshow(np.log1p(body.values), cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(body.columns))); ax.set_xticklabels(body.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(body.index))); ax.set_yticklabels([f"{r} (n={int(mat.loc[r, '(any task)'])})" for r in body.index])
    for i in range(body.shape[0]):
        for j in range(body.shape[1]):
            v = int(body.values[i, j])
            ax.text(j, i, v if v else "·", ha="center", va="center", fontsize=8, color="white" if v > body.values.max() * 0.35 else "#222")
    ax.set_xlabel(hm.get("col_title", "Task")); ax.set_ylabel(hm.get("row_title", "Language"))
    ax.set_title(hm.get("title", "Coverage heat map"))
    cb = fig.colorbar(im, ax=ax, shrink=0.7); cb.set_label("Documents (colour on log scale; number = count)")
    ticks = [0, 1, 5, 20, 50, 100, 200, 400]
    ticks = [t for t in ticks if t <= body.values.max()]
    cb.set_ticks(np.log1p(ticks)); cb.set_ticklabels(ticks)
    fig.text(0.01, -0.02, SRC + " A document is counted in every cell whose language term and task term both occur in its title or abstract.", fontsize=7, color="grey")
    save(fig, "P04_coverage_heatmap", svg=True)
    cap("P04_coverage_heatmap", hm.get("title", "Coverage heat map"),
        "Number of corpus documents whose title or abstract mentions both the row term and the column term.",
        f"{SRC} Coding by regular expressions listed in config.json -> heatmap (title + abstract; {int((m.abstract != '').sum())} documents have an abstract). Cells are not exclusive.",
        hm.get("caution", "Mention is not coverage: a paper that lists a language among twenty counts the same as one devoted to it, and languages named only in the full text are missed."))

# ---------------------------------------------------------------- P5 main path (key-route, SPC)
D = nx.DiGraph()
yr = by_id["year"].to_dict()
for u, v in G.edges():                # u cited by v ; keep only edges going forward in time
    if yr.get(u, 0) and yr.get(v, 0) and yr[u] <= yr[v]:
        D.add_edge(u, v)
while True:                           # break any remaining cycles (same-year mutual citations)
    try:
        cyc = nx.find_cycle(D)
        D.remove_edge(*min(cyc, key=lambda e: by_id.loc[e[0], "local_citations"])[:2])
    except nx.NetworkXNoCycle:
        break
if D.number_of_edges() >= 30:
    topo = list(nx.topological_sort(D))
    nminus = {n: 1 if D.in_degree(n) == 0 else 0 for n in D}
    for n in topo:
        for s in D.successors(n):
            nminus[s] += nminus[n]
    nplus = {n: 1 if D.out_degree(n) == 0 else 0 for n in D}
    for n in reversed(topo):
        for p in D.predecessors(n):
            nplus[p] += nplus[n]
    spc = {(u, v): nminus[u] * nplus[v] for u, v in D.edges()}
    nx.set_edge_attributes(D, spc, "spc")
    k_routes = int(CFG.get("main_path_key_routes", 8))
    keys = sorted(spc, key=spc.get, reverse=True)[:k_routes]
    path_edges = set()
    for (u, v) in keys:
        path_edges.add((u, v))
        cur = v
        while D.out_degree(cur):
            nxt = max(D.successors(cur), key=lambda s: spc[(cur, s)])
            path_edges.add((cur, nxt)); cur = nxt
        cur = u
        while D.in_degree(cur):
            prv = max(D.predecessors(cur), key=lambda p: spc[(p, cur)])
            path_edges.add((prv, cur)); cur = prv
    MP = nx.DiGraph(); MP.add_edges_from(path_edges)
    rows = []
    for n in MP:
        r = by_id.loc[n]
        rows.append({"id": n, "label": short(r, 60), "title": r["title"], "year": r["year"], "pub_date": r["pub_date"], "venue": r["venue"],
                     "primary_sublit": r["primary_sublit"], "local_citations": r["local_citations"], "url": r["url"],
                     "max_spc_through_node": max([spc[e] for e in path_edges if n in e])})
    mp = pd.DataFrame(rows).sort_values(["year", "pub_date"])
    mp.to_csv(os.path.join(TAB, "P05_main_path_nodes.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame([{"from_cited": u, "to_citing": v, "spc": spc[(u, v)], "key_route": int((u, v) in keys)} for u, v in path_edges]).sort_values("spc", ascending=False).to_csv(
        os.path.join(TAB, "P05_main_path_edges.csv"), index=False, encoding="utf-8-sig")
    # layout: x = date, y = spread within year
    mp["date"] = pd.to_datetime(mp.pub_date.where(mp.pub_date != "", mp.year.astype(str) + "-07-01"), errors="coerce")
    mp = mp.sort_values("date").reset_index(drop=True)
    xs = {r.id: i for i, r in mp.iterrows()}
    lane = {}
    for i, r in mp.iterrows():
        lane[r.id] = i % 2
    fig, ax = plt.subplots(figsize=(14, max(7, 0.42 * len(mp) + 2)))
    ypos = {r.id: len(mp) - i for i, r in mp.iterrows()}
    xpos = {r.id: r.date for _, r in mp.iterrows()}
    mx = max(spc[e] for e in path_edges)
    for (u, v) in path_edges:
        ax.annotate("", xy=(xpos[v], ypos[v]), xytext=(xpos[u], ypos[u]),
                    arrowprops=dict(arrowstyle="-|>", color=PAL[1] if (u, v) in keys else "#888", lw=0.6 + 2.6 * spc[(u, v)] / mx, alpha=0.75,
                                    connectionstyle="arc3,rad=0.15"))
    for _, r in mp.iterrows():
        ax.scatter(r.date, ypos[r.id], s=40 + 8 * r.local_citations, color=COL.get(r.primary_sublit, "#999"), zorder=3, edgecolors="white")
        ax.annotate(r.label, (r.date, ypos[r.id]), xytext=(9, -3), textcoords="offset points", fontsize=7.5)
    ax.set_yticks([]); ax.set_ylabel("Order along the path (earliest at top)")
    ax.set_xlabel("Publication date")
    ax.set_xlim(mp.date.min() - pd.Timedelta(days=150), mp.date.max() + pd.Timedelta(days=int((mp.date.max() - mp.date.min()).days * 0.55) + 400))
    ax.set_title(f"Main path through the direct citation network (key-route search, {k_routes} key routes, search path count weights)")
    hs = [plt.Line2D([], [], marker="o", ls="", color=COL[k], label=f"{k}: {v}") for k, v in SUBL.items() if k in set(mp.primary_sublit)]
    hs += [plt.Line2D([], [], color=PAL[1], lw=2.5, label="Key route (highest search path count)"), plt.Line2D([], [], color="#888", lw=1.2, label="Extension of a key route")]
    ax.legend(handles=hs, loc="lower left", fontsize=8, title="Node colour = sub-literature; arrow = cited -> citing; width = search path count")
    fig.text(0.01, 0.005, SRC + f" Acyclic citation graph: {D.number_of_nodes()} documents, {D.number_of_edges()} links.", fontsize=7, color="grey")
    save(fig, "P05_main_path", svg=True)
    cap("P05_main_path", "Main path (key-route) through the direct citation network",
        "The chain(s) of papers that carry the most citation 'traffic' from the earliest to the latest documents in the corpus.",
        f"{SRC} Direct citations between corpus documents made acyclic (links running backwards in time dropped, {D.number_of_edges()} links kept); search path count (SPC) weight per link; global key-route search from the {k_routes} highest-SPC links, extended forwards and backwards along the highest-SPC neighbour. Tables: tables/P05_main_path_nodes.csv and _edges.csv.",
        "A main path is one summary of the citation structure, driven by where reference lists are available; it is not a ranking of quality and it omits whole branches of the field.")
else:
    print("main path skipped: fewer than 30 usable citation links")

json.dump(CAPS, open(os.path.join(FIG, "captions_P.json"), "w", encoding="utf-8"), indent=1)
print("python figures done:", len(CAPS))
