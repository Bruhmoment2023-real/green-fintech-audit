import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get
qs=['Preliminary guideline for reporting bibliometric reviews of the biomedical literature BIBLIO',
 'PRISMA-S: an extension to the PRISMA statement for reporting literature searches in systematic reviews',
 'The PRISMA 2020 statement: an updated guideline for reporting systematic reviews',
 'An assessment of the quality of the search strategy: a case of bibliometric studies published in business and economics',
 'How to conduct a bibliometric analysis: An overview and guidelines',
 'Bibliometrics reporting guideline transparency reproducibility bibliometric studies checklist',
 'Which academic search systems are suitable for systematic reviews or meta-analyses? Evaluating retrieval qualities of Google Scholar, PubMed, and 26 other resources']
for q in qs:
    s,r=get('https://api.crossref.org/works',params={'query.bibliographic':q,'rows':4,'select':'DOI,title,author,issued,container-title'})
    print('##',q[:70])
    for it in r['message']['items']:
        print('  ',it['DOI'],'|',(it.get('title') or [''])[0][:90],'|',(it.get('container-title') or [''])[0][:35],'|',(it.get('issued',{}).get('date-parts') or [[None]])[0][0],'|',(it.get('author') or [{}])[0].get('family'))
