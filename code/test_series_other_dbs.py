"""Test C: do the 15 'Review of Management Literature' records carry the same volume-level keywords in Crossref and OpenAlex as in Scopus?
Uses only free single-record lookups (Crossref /works/<doi>, OpenAlex /works/doi:<doi>). Output: results/series_other_databases.csv"""
import sys, os, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get
import pandas as pd
d = pd.read_csv('../data/scopus_export_flags.csv', dtype=str)
s = d[d['Source title'] == 'Review of Management Literature']
out = []
for _, r in s.iterrows():
    doi = r['DOI']
    row = dict(title=r['Title'][:90], doi=doi, scopus_author_keywords=str(r['Author Keywords'])[:80], scopus_has_abstract=isinstance(r['Abstract'], str) and len(r['Abstract']) > 40)
    if isinstance(doi, str):
        s1, cr = get('https://api.crossref.org/works/' + doi)
        m = cr['message'] if s1 == 200 else {}
        row.update(crossref_status=s1, crossref_type=m.get('type'), crossref_container=(m.get('container-title') or [''])[0], crossref_subject='; '.join(m.get('subject', [])), crossref_has_abstract=bool(m.get('abstract')))
        s2, oa = get('https://api.openalex.org/works/doi:' + doi, params={'select': 'id,keywords,topics,primary_location,type,abstract_inverted_index'})
        o = oa if s2 == 200 else {}
        kws = [k.get('display_name') for k in o.get('keywords', [])]
        src = ((o.get('primary_location') or {}).get('source') or {})
        row.update(openalex_status=s2, openalex_type=o.get('type'), openalex_source=src.get('display_name'), openalex_source_type=src.get('type'),
                   openalex_keywords='; '.join(kws), openalex_has_abstract=bool(o.get('abstract_inverted_index')),
                   openalex_topic=((o.get('topics') or [{}])[0] or {}).get('display_name'))
        vol_kw = re.compile(r'fintech|green finance|supply chain resilience|digital leadership|ai finance', re.I)
        row['openalex_keywords_contain_volume_terms'] = bool(vol_kw.search(row['openalex_keywords']))
        row['crossref_subject_contains_volume_terms'] = bool(vol_kw.search(row['crossref_subject']))
    out.append(row); print(row['title'][:50], '|', row.get('crossref_type'), '|', row.get('openalex_source_type'), '|', row.get('openalex_keywords', '')[:60], flush=True)
os.makedirs('../results', exist_ok=True)
keys = []
for r in out:
    for k in r:
        if k not in keys: keys.append(k)
w = csv.DictWriter(open('../results/series_other_databases.csv', 'w', newline='', encoding='utf-8'), fieldnames=keys); w.writeheader(); w.writerows(out)
