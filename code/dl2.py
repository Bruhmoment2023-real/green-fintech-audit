import requests
OUT='E:/Research-Staging/10-green-fintech-audit/pdfs/'
T={1:['http://ira.lib.polyu.edu.hk/bitstream/10397/106178/1/sustainability-15-14683.pdf'],
4:['https://repository.uel.ac.uk/download/4d07ab6106d31482bb5c5ec7b1fcdb3c2ec570c9e9f448d99b8a1f0993e60410/353360/The%20Role%20of%20Technology%20in%20Promoting%20Green%20Finance.pdf'],
9:['https://www.econstor.eu/bitstream/10419/321294/1/admsci-15-00150.pdf'],
10:['https://www.mdpi.com/1911-8074/18/8/420/htm'],
15:['https://digitalcommons.mtu.edu/michigantech-p2/2887'],
3:['https://iris.univpm.it/retrieve/handle/11566/335455'] }
for n,us in T.items():
  for u in us:
    try:
        r=requests.get(u,headers={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)'},timeout=60)
        ok=r.content[:4]==b'%PDF'
        print(n,r.status_code,ok,len(r.content),r.headers.get('content-type'))
        if ok: open(f'{OUT}review{n:02d}.pdf','wb').write(r.content)
        elif n in(10,3,15): print(r.text[:300].replace('\n',' '))
    except Exception as e: print(n,'ERR',e)
