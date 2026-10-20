"""Phase 3 network analyses for pack 10, written to depth/network/ (the Phase-2 folder bibliometrics/ is only READ).
Input: a dated snapshot of bibliometrics/data/clean/master.csv and references.csv (the OpenAlex rebuild, 497 records, pulled by the Phase-2 agent).
1. Kleinberg burst detection on OpenAlex keywords by publication year (batch model, s=2, gamma=1).
2. Main-path analysis (search path count, global main path and key-route paths) on the direct-citation network inside the corpus.
Honest limits are written into the captions: the corpus covers 2021-2026 only, 2026 is a part year, and the in-corpus citation network is sparse."""
import os, math, shutil, json, collections, re, csv
import pandas as pd, numpy as np, networkx as nx
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
SRC = '../bibliometrics/data/clean/'; OUT = '../depth/network/'; os.makedirs(OUT + 'data', exist_ok=True); os.makedirs(OUT + 'figures', exist_ok=True)
for f in ('master.csv', 'references.csv'): shutil.copy(SRC + f, OUT + 'data/snapshot_' + f)
m = pd.read_csv(OUT + 'data/snapshot_master.csv', dtype=str, encoding='utf-8-sig'); m['year'] = m['year'].astype(int)
refs = pd.read_csv(OUT + 'data/snapshot_references.csv', dtype=str, encoding='utf-8-sig')
log = {'corpus_records': len(m), 'reference_rows': len(refs)}

# ---------- 1. Kleinberg bursts ----------
def kleinberg(r, d, s=2.0, gamma=1.0):
    """Two-state batch Kleinberg. r[t] = documents with the keyword in batch t, d[t] = all documents in batch t."""
    n = len(r); R, D = sum(r), sum(d)
    if R == 0: return []
    p0 = R / D; p1 = min(s * p0, 0.999)
    if p1 <= p0: return []
    def cost(state, t):
        p = p0 if state == 0 else p1
        rt, dt = r[t], d[t]
        return -(math.log(math.comb(dt, rt)) + rt * math.log(p) + (dt - rt) * math.log(1 - p))
    tau = gamma * math.log(max(n, 2))
    C = [[0, 0] for _ in range(n)]; B = [[0, 0] for _ in range(n)]
    C[0][0] = cost(0, 0); C[0][1] = tau + cost(1, 0)
    for t in range(1, n):
        for j in (0, 1):
            opts = [C[t - 1][i] + (tau if (j == 1 and i == 0) else 0) for i in (0, 1)]
            i = int(np.argmin(opts)); C[t][j] = opts[i] + cost(j, t); B[t][j] = i
    st = [0] * n; st[-1] = int(np.argmin(C[-1]))
    for t in range(n - 1, 0, -1): st[t - 1] = B[t][st[t]]
    bursts = []; t = 0
    while t < n:
        if st[t] == 1:
            e = t
            while e + 1 < n and st[e + 1] == 1: e += 1
            w = sum(cost(0, k) - cost(1, k) for k in range(t, e + 1))
            bursts.append((t, e, w)); t = e + 1
        else: t += 1
    return bursts
years = sorted(m['year'].unique()); d_t = [int((m['year'] == y).sum()) for y in years]
kwc = collections.Counter(); kw_year = collections.defaultdict(lambda: collections.Counter())
for _, r in m.iterrows():
    if isinstance(r['openalex_keywords'], str):
        for k in set(x.strip().lower() for x in r['openalex_keywords'].split(';') if x.strip()):
            kwc[k] += 1; kw_year[k][r['year']] += 1
rows = []
for k, n in kwc.items():
    if n < 8: continue
    r_t = [kw_year[k].get(y, 0) for y in years]
    for (a, b, w) in kleinberg(r_t, d_t):
        rows.append(dict(keyword=k, total=n, burst_start=years[a], burst_end=years[b], weight=round(w, 2), counts_by_year=json.dumps(dict(zip(map(int, years), r_t)))))
bd = pd.DataFrame(rows).sort_values('weight', ascending=False) if rows else pd.DataFrame(columns=['keyword'])
bd.to_csv(OUT + 'keyword_bursts.csv', index=False)
log.update(keywords_with_at_least_8_records=sum(1 for n in kwc.values() if n >= 8), bursts_found=len(bd), docs_per_year=dict(zip(map(int, years), d_t)))
if len(bd):
    top = bd.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6), dpi=200)
    for i, (_, r) in enumerate(top.iterrows()):
        ax.plot([years[0], years[-1]], [i, i], color='#d0d0d0', lw=6, solid_capstyle='butt')
        ax.plot([r['burst_start'] - 0.4, r['burst_end'] + 0.4], [i, i], color='#c0392b', lw=6, solid_capstyle='butt')
    ax.set_yticks(range(len(top))); ax.set_yticklabels([f"{k} (n={n})" for k, n in zip(top['keyword'], top['total'])], fontsize=8)
    ax.set_xticks(years); ax.set_xlabel('Publication year (2026 is a part year)'); ax.set_ylabel('OpenAlex keyword (records with it)')
    ax.set_title('Keyword bursts (Kleinberg, s=2, gamma=1): top 15 by burst weight, OpenAlex rebuild, 497 records', fontsize=10)
    ax.legend(handles=[plt.Line2D([0], [0], color='#d0d0d0', lw=6), plt.Line2D([0], [0], color='#c0392b', lw=6)], labels=['keyword present in window', 'burst interval'], loc='lower left', fontsize=8)
    plt.tight_layout(); plt.savefig(OUT + 'figures/N01_keyword_bursts.png'); plt.close()

# ---------- 2. Main path ----------
G = nx.DiGraph(); ids = set(m['openalex_id'].dropna().str.replace('https://openalex.org/', '', regex=False)) | set(m['id'])
m['oid'] = m['id']
inc = refs[refs['citing'].isin(ids) & refs['cited'].isin(ids)]
for _, r in inc.iterrows():
    if r['citing'] != r['cited']: G.add_edge(r['cited'], r['citing'])   # knowledge flows cited -> citing
yr = dict(zip(m['id'], m['year']))
# break cycles (same-year mutual citation): drop edges that go backwards in time, keep same-year edges by id order
for u, v in list(G.edges()):
    if yr[u] > yr[v] or (yr[u] == yr[v] and u >= v): G.remove_edge(u, v)
log.update(citation_edges_in_corpus=G.number_of_edges(), nodes_with_edges=G.number_of_nodes(), weakly_connected_components=nx.number_weakly_connected_components(G))
res = {}
if G.number_of_edges() >= 10:
    comp = max(nx.weakly_connected_components(G), key=len); H = G.subgraph(comp).copy()
    order = list(nx.topological_sort(H))
    nin = {n: 0 for n in H}; nout = {n: 0 for n in H}
    for n in order: nin[n] = 1 if H.in_degree(n) == 0 else sum(nin[p] for p in H.predecessors(n))
    for n in reversed(order): nout[n] = 1 if H.out_degree(n) == 0 else sum(nout[c] for c in H.successors(n))
    spc = {(u, v): nin[u] * nout[v] for u, v in H.edges()}
    # global main path: maximise the sum of SPC along a source-to-sink path
    best = {}; prev = {}
    for n in order:
        if H.in_degree(n) == 0: best[n] = 0; prev[n] = None
        else:
            p = max(H.predecessors(n), key=lambda q: best[q] + spc[(q, n)]); best[n] = best[p] + spc[(p, n)]; prev[n] = p
    sinks = [n for n in order if H.out_degree(n) == 0]; end = max(sinks, key=lambda n: best[n])
    path = []; n = end
    while n is not None: path.append(n); n = prev[n]
    path = path[::-1]
    # key-route main path: start from the top-5 edges by SPC, extend forward and backward along max-SPC edges
    top_edges = sorted(spc, key=spc.get, reverse=True)[:5]; kr = set()
    for (u, v) in top_edges:
        kr.add((u, v)); a = v
        while H.out_degree(a):
            b = max(H.successors(a), key=lambda c: spc[(a, c)]); kr.add((a, b)); a = b
        a = u
        while H.in_degree(a):
            b = max(H.predecessors(a), key=lambda c: spc[(c, a)]); kr.add((b, a)); a = b
    krn = set(x for e in kr for x in e)
    meta = m.set_index('id')
    def lab(n): r = meta.loc[n]; return f"{str(r['authors']).split(';')[0].split(',')[0].strip()} {r['year']}"
    tab = []
    for i, n in enumerate(path):
        r = meta.loc[n]; tab.append(dict(order=i + 1, id=n, year=r['year'], first_author=str(r['authors']).split(';')[0], title=r['title'], venue=r['venue'], doi=r['doi'], on_keyroute=n in krn))
    pd.DataFrame(tab).to_csv(OUT + 'main_path_papers.csv', index=False)
    pd.DataFrame([dict(id=n, year=yr[n], title=meta.loc[n]['title'], doi=meta.loc[n]['doi']) for n in sorted(krn, key=lambda x: yr[x])]).to_csv(OUT + 'key_route_papers.csv', index=False)
    res = dict(component_nodes=H.number_of_nodes(), component_edges=H.number_of_edges(), global_main_path_length=len(path), key_route_nodes=len(krn), max_spc=max(spc.values()))
    # figure: draw the key-route subgraph plus global path, x = year
    S = nx.DiGraph(); S.add_edges_from(kr); S.add_edges_from(zip(path[:-1], path[1:]))
    pos = {}; byyear = collections.defaultdict(list)
    for n in S: byyear[yr[n]].append(n)
    for y, ns in byyear.items():
        for i, n in enumerate(sorted(ns)): pos[n] = (y + (0.08 * (i % 3)), -i)
    fig, ax = plt.subplots(figsize=(11, 7), dpi=200)
    nx.draw_networkx_edges(S, pos, ax=ax, edge_color='#999999', arrows=True, arrowsize=8, width=1)
    gp = set(zip(path[:-1], path[1:])); nx.draw_networkx_edges(S, pos, edgelist=[e for e in S.edges() if e in gp], ax=ax, edge_color='#c0392b', width=2.4, arrows=True, arrowsize=10)
    nx.draw_networkx_nodes(S, pos, ax=ax, node_size=60, node_color=['#c0392b' if n in path else '#2c7fb8' for n in S])
    for n, (x, y) in pos.items(): ax.text(x + 0.02, y + 0.12, lab(n), fontsize=6)
    ax.set_xlabel('Publication year'); ax.set_ylabel('papers within a year (stacked)'); ax.set_yticks([]); ax.set_xticks(sorted(byyear))
    ax.set_title('Main-path analysis (search path count) of the in-corpus citation network: red = global main path, blue = other key-route papers', fontsize=9)
    plt.tight_layout(); plt.savefig(OUT + 'figures/N02_main_path.png'); plt.close()
log['main_path'] = res
json.dump(log, open(OUT + 'network_summary.json', 'w'), indent=1, default=str); print(json.dumps(log, indent=1, default=str))
