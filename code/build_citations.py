"""Builds depth/citations/references.bib and references.ris from Crossref's own BibTeX/RIS transforms (no hand-typed fields).
DOI sources: the 15 reviews, the methodological papers, Sean's 24 May reference list entries that resolved (title similarity >= 0.95),
and the ten Table-4 papers. Unresolved items are listed in README.md."""
import sys, os, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dois = {}
def add(d, why): dois.setdefault(d.lower(), set()).add(why)
for r in csv.DictReader(open('../data/reviews15_meta.csv', encoding='utf-8')): add(r['doi'], 'one of the 15 reviews')
for d, w in [('10.1186/s13643-023-02410-2', 'BIBLIO'), ('10.5195/jmla.2021.962', 'PRISMA-S'), ('10.1136/bmj.n71', 'PRISMA 2020'), ('10.1016/j.jbusres.2021.04.070', 'Donthu 2021'),
             ('10.1007/s11192-023-04765-8', 'Farooq 2023 (metadata only)'), ('10.1002/jrsm.1378', 'Gusenbauer and Haddaway 2020'), ('10.1007/s11192-018-2958-5', 'Gusenbauer 2019'),
             ('10.1162/qss_a_00019', 'Baas 2020'), ('10.1177/1094428114562629', 'Zupic and Cater'), ('10.1007/s11192-015-1645-z', 'Ellegaard and Wallin'),
             ('10.1016/j.heliyon.2023.e16780', 'Koo and Lin 2023 (PRIBA)'), ('10.1162/qss.a.12', 'Ng et al. 2025 GLOBAL scoping review (abstract only)'), ('10.1016/j.joi.2017.08.007', 'Aria and Cuccurullo 2017 (cited in manuscript text, not in its list; not opened)')]: add(d, w)
unres = []
for r in csv.DictReader(open('../results/repair/reference_check_crossref.csv', encoding='utf-8')):
    if float(r['title_similarity']) >= 0.95 and r['best_doi']: add(r['best_doi'], f"manuscript reference {r['ref']}")
    else: unres.append((r['ref'], r['cited'][:110], r['best_doi'], r['title_similarity']))
for r in csv.DictReader(open('../results/repair/table4_comparison.csv', encoding='utf-8')): add(r['doi'], f"export Table 4 rank {r['rank']}")
bib, ris, fail = [], [], []
for d in sorted(dois):
    s1, b = get('https://api.crossref.org/works/' + d + '/transform/application/x-bibtex', as_json=False)
    s2, r = get('https://api.crossref.org/works/' + d + '/transform/application/x-research-info-systems', as_json=False)
    if s1 == 200 and b.strip().startswith('@'):
        b = b.strip(); key = re.match(r'@\w+\{([^,]+),', b).group(1)
        b = b[:-1].rstrip() + ',\n  note = {' + '; '.join(sorted(dois[d])) + '; metadata from Crossref}\n}' if b.endswith('}') else b
        bib.append(b)
    else: fail.append((d, s1))
    if s2 == 200 and 'TY  -' in r: ris.append(r.strip())
os.makedirs('../depth/citations', exist_ok=True)
open('../depth/citations/references.bib', 'w', encoding='utf-8').write('\n\n'.join(bib) + '\n')
open('../depth/citations/references.ris', 'w', encoding='utf-8').write('\n\n'.join(ris) + '\n')
open('../depth/citations/README.md', 'w', encoding='utf-8').write(f"""# Citation library (pack 10)
- `references.bib` ({len(bib)} entries) and `references.ris` ({len(ris)} entries): built from Crossref's BibTeX and RIS transforms by `code/build_citations.py`; each BibTeX entry carries a `note` saying why it is in the pack. {len(dois)} unique DOIs requested, {len(fail)} could not be fetched: {fail}.
- Scope: the 15 reviews, six methodological sources, the manuscript's references that resolved in Crossref with an exact title match, and the ten most-cited papers from the Scopus export. Sources I did not open are marked in the `note` field of the files where I knew it (Farooq 2023, Aria and Cuccurullo 2017); the reading notes say which sources were opened in full.
- Not resolvable in Crossref (not in the library; see `results/repair/reference_verdicts.csv`): {len(unres)} manuscript entries with no exact title match: {[u[0] for u in unres]}.
- Import into Zotero: File > Import and choose `references.ris` (or `references.bib`). Check the tags and notes after import; titles from Crossref sometimes keep HTML entities.
""")
print(len(bib), len(ris), len(dois), fail, [u[0] for u in unres])
