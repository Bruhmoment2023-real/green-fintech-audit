"""Wider-sample abstract-level reporting check. Reads (never writes) the Phase-2 corpus bibliometrics/data/clean/master.csv.
Selects review-type records (bibliometric / systematic / literature / scoping review, science mapping) and codes what their ABSTRACT states:
A1 database named, A2 number of records/documents analysed, A3 search period or date range, A4 software named, A5 PRISMA/protocol named.
Abstract-level only: a missing item may still be reported in the full text. Output results/wide_sample_abstract_coding.csv + summary."""
import pandas as pd, re, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
m = pd.read_csv('../bibliometrics/data/clean/master.csv', dtype=str, encoding='utf-8-sig')
rev = re.compile(r'bibliometric|scientometric|systematic (literature )?(review|survey)|literature review|scoping review|science mapping|systematic mapping|meta-analy|review of the literature|literature survey|integrative review|state of the art', re.I)
topic = re.compile(r'fintech|financial technolog|digital financ|green financ|sustainable financ|climate financ|esg|green bond|green credit|carbon|sustainab', re.I)
def in_title(r): return bool(rev.search(r['title'] or ''))
sel = m[m.apply(lambda r: bool(isinstance(r['abstract'], str) and (in_title(r) or rev.search(r['abstract'][:600] or '')) and topic.search((r['title'] or '') + ' ' + r['abstract'])), axis=1)].copy()
sel = sel[sel['doc_type'].isin(['article', 'review']) | sel['doc_type'].isna()]
dbs = re.compile(r'\b(scopus|web of science|wos|clarivate|google scholar|dimensions|pubmed|econlit|proquest|science ?direct|ebsco|openalex|crossref|lens\.org)\b', re.I)
nrec = re.compile(r'\b(\d{2,5}|[0-9],[0-9]{3})\s+(?:\w+\s+){0,3}(papers|articles|documents|publications|studies|records|journal articles|peer-reviewed|items|works)\b', re.I)
period = re.compile(r'\b(19|20)\d{2}\s*(?:-|–|to|and|until|through)\s*(?:19|20)?\d{2}\b|\bbetween (19|20)\d{2}\b|\bsince (19|20)\d{2}\b|\bfrom (19|20)\d{2}\b', re.I)
sw = re.compile(r'vos ?viewer|bibliometrix|biblioshiny|citespace|r package|rstudio|python|nvivo|gephi|citnet|wordstat|leximancer|scimat|publish or perish|atlas\.ti|endnote|zotero|rayyan|revman', re.I)
pr = re.compile(r'prisma|spar-4-slr|tccm|adO\b|protocol|kitchenham|tranfield', re.I)
sel['A1_database'] = sel['abstract'].str.contains(dbs); sel['A2_n_records'] = sel['abstract'].str.contains(nrec)
sel['A3_period'] = sel['abstract'].str.contains(period); sel['A4_software'] = sel['abstract'].str.contains(sw); sel['A5_protocol'] = sel['abstract'].str.contains(pr)
sel['is_bibliometric'] = (sel['title'] + ' ' + sel['abstract']).str.contains(r'bibliometric|scientometric|science mapping|vosviewer|bibliometrix', case=False)
out = sel[['id', 'title', 'year', 'venue', 'doi', 'primary_sublit', 'is_bibliometric', 'A1_database', 'A2_n_records', 'A3_period', 'A4_software', 'A5_protocol']]
out.to_csv('../results/wide_sample_abstract_coding.csv', index=False)
def summ(df): return {k: [int(df[k].sum()), len(df), round(100 * df[k].mean(), 1)] for k in ['A1_database', 'A2_n_records', 'A3_period', 'A4_software', 'A5_protocol']}
res = {'all_review_type_records': summ(sel), 'bibliometric_only': summ(sel[sel.is_bibliometric]), 'n_all': len(sel), 'n_bibliometric': int(sel.is_bibliometric.sum())}
json.dump(res, open('../results/wide_sample_summary.json', 'w'), indent=1); print(json.dumps(res, indent=1))
