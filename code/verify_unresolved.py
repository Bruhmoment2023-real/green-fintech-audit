"""Second, stricter check of the references that did not resolve in the first Crossref pass:
exact-title queries on Crossref (query.title) and Semantic Scholar title-match, plus direct DOI probes
built from the cited volume/article number. Output: results/repair/reference_unresolved_probe.json"""
import sys, os, json, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get

T = {
 'R13 Khan, Yu, Sharif, Golpira (2022) ESPR 29(20) 29730-29745': 'Determinants of economic growth and environmental sustainability: A bibliometric analysis',
 'R14 Li, Du, Long (2023) JCP 382, 135245': 'Dynamic analysis of global green finance research: A bibliometric review',
 'R15 Xu, Chen, Zhao (2024) FRL 59, 104563': 'Evolution and future trends of green finance research: A bibliometric analysis',
 'R17 Singh, Singh, Karmakar (2023) LPP': 'Application of bibliometric analysis in research evaluation: A review of methods and tools',
 'R9 Al Doghan, Chong (2023) IJOQM 29(2) 296-315': 'Fintech adoption and environmental sustainability: Mediating role of green finance, investment and innovation',
}
DOIPROBES = {
 'R14 Li (JCP 382, 135245)': ['10.1016/j.jclepro.2022.135245', '10.1016/j.jclepro.2023.135245'],
 'R15 Xu (FRL 59, 104563)': ['10.1016/j.frl.2023.104563', '10.1016/j.frl.2024.104563'],
}
out = {}
for k, title in T.items():
    s, r = get('https://api.crossref.org/works', params={'query.title': title, 'rows': 5, 'select': 'DOI,title,author,issued,container-title'})
    hits = []
    for it in (r['message']['items'] if s == 200 else []):
        t = (it.get('title') or [''])[0]
        hits.append(dict(doi=it['DOI'], title=t, sim=round(difflib.SequenceMatcher(None, title.lower(), t.lower()).ratio(), 3),
                         year=(it.get('issued', {}).get('date-parts') or [[None]])[0][0],
                         container=(it.get('container-title') or [''])[0], first=(it.get('author') or [{}])[0].get('family')))
    s2, j = get('https://api.semanticscholar.org/graph/v1/paper/search/match', params={'query': title, 'fields': 'title,year,venue,externalIds'})
    out[k] = dict(cited_title=title, crossref_title_query=hits, s2_match_status=s2, s2_match=(j if isinstance(j, dict) else str(j)[:200]))
    print(k, '| best crossref sim', max([h['sim'] for h in hits] or [0]), '| s2', s2, str(j)[:160], flush=True)
for k, dois in DOIPROBES.items():
    for d in dois:
        s, r = get('https://api.crossref.org/works/' + d)
        info = None
        if s == 200:
            m = r['message']; info = dict(title=(m.get('title') or [''])[0], container=(m.get('container-title') or [''])[0], year=(m.get('issued', {}).get('date-parts') or [[None]])[0][0])
        out.setdefault('doi_probes', {})[d] = dict(status=s, record=info)
        print('DOI probe', d, s, info, flush=True)
json.dump(out, open('../results/repair/reference_unresolved_probe.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
