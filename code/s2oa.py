import sys,os,csv
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from netcache import get
for r in csv.DictReader(open('../data/reviews15_meta.csv',encoding='utf-8')):
    s,j=get('https://api.semanticscholar.org/graph/v1/paper/DOI:'+r['doi'],params={'fields':'title,openAccessPdf,externalIds,abstract'})
    print(r['n'],s,(j.get('openAccessPdf') if isinstance(j,dict) else j) , bool(isinstance(j,dict) and j.get('abstract')))
