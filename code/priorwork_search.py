import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from netcache import get
Q=['reporting quality of bibliometric studies','reproducibility of bibliometric analyses search strategy reporting','adherence to reporting guidelines bibliometric reviews','quality assessment of bibliometric studies search string database reporting',
 'BIBLIO reporting guideline bibliometric adherence','bibliometric review database selection contamination book series metadata','replicability of bibliometric studies Scopus Web of Science data cleaning','methodological quality bibliometric reviews systematic review of bibliometric studies',
 'green finance bibliometric reviews comparison','fintech bibliometric reviews critical assessment']
out={}
for q in Q:
    s,j=get('https://api.crossref.org/works',params={'query.bibliographic':q,'rows':8,'filter':'from-pub-date:2012-01-01','select':'DOI,title,issued,container-title,author,type'})
    items=[(i['DOI'],(i.get('title') or [''])[0][:110],(i.get('issued',{}).get('date-parts') or [[None]])[0][0],(i.get('container-title') or [''])[0][:30]) for i in j['message']['items']] if s==200 else []
    out[q]=items; print('##',q); [print('  ',x) for x in items]
s,j=get('http://export.arxiv.org/api/query',params={'search_query':'all:bibliometric AND (all:reproducibility OR all:reporting)','max_results':8},as_json=False)
import re
print('## arXiv'); [print('  ',t.strip()[:110]) for t in re.findall(r'<title>(.*?)</title>',j if isinstance(j,str) else '',re.S)[1:9]]
