import requests,csv,json
H={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)','Accept':'application/json'}
for r in csv.DictReader(open('../data/reviews15_meta.csv',encoding='utf-8')):
    if int(r['n']) in (1,4,6,9,10): continue
    try:
        x=requests.get('https://api.openaire.eu/search/publications',params={'doi':r['doi'],'format':'json'},headers=H,timeout=60)
        j=x.json(); res=j['response']['results']
        urls=set()
        if res:
            for it in (res['result'] if isinstance(res['result'],list) else [res['result']]):
                inst=it['metadata']['oaf:entity']['oaf:result'].get('children',{}).get('instance',[])
                inst=inst if isinstance(inst,list) else [inst]
                for i in inst:
                    w=i.get('webresource'); w=w if isinstance(w,list) else [w] if w else []
                    for ww in w: urls.add((i.get('accessright',{}).get('@classid'),ww.get('url',{}).get('$')))
        print(r['n'],x.status_code,sorted(urls,key=str)[:6])
    except Exception as e: print(r['n'],'ERR',str(e)[:80])
