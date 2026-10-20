import sys,os,csv,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from netcache import get
out={}
for r in csv.DictReader(open('../data/reviews15_meta.csv',encoding='utf-8')):
    s,j=get('https://api.openalex.org/works/doi:'+r['doi'],params={'select':'abstract_inverted_index,title'})
    a=''
    if s==200 and j.get('abstract_inverted_index'):
        pos={}
        for w,ps in j['abstract_inverted_index'].items():
            for p in ps: pos[p]=w
        a=' '.join(pos[k] for k in sorted(pos))
    s2,k=get('https://api.semanticscholar.org/graph/v1/paper/DOI:'+r['doi'],params={'fields':'abstract'})
    a2=(k.get('abstract') if isinstance(k,dict) else '') or ''
    out[r['n']]={'doi':r['doi'],'openalex':a,'s2':a2}
    print(r['n'],len(a),len(a2))
json.dump(out,open('../data/reviews15_abstracts.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
