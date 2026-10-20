import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from netcache import get
OUT='E:/Research-Staging/10-green-fintech-audit/pdfs/'
T={1:'https://www.mdpi.com/2071-1050/15/20/14683/pdf?version=1696930840',
4:'https://www.mdpi.com/1911-8074/17/10/472/pdf?version=1729257695',
5:'https://doi.org/10.1016/j.procs.2024.09.643',
6:'https://cebr.vse.cz/doi/10.18267/j.cebr.368.pdf',
8:'https://doi.org/10.1016/j.ribaf.2024.102682',
9:'https://www.mdpi.com/2076-3387/15/4/150/pdf?version=1745056824',
10:'https://www.mdpi.com/1911-8074/18/8/420/pdf?version=1754012710',
12:'https://doi.org/10.1016/j.procs.2025.09.560',
15:'https://www.sciencedirect.com/science/article/pii/S2666188826004314/pdf',
3:'https://hdl.handle.net/11566/335455',
7:'https://doi.org/10.2139/ssrn.5042215'}
for n,u in T.items():
    import requests
    try:
        r=requests.get(u,headers={'User-Agent':'Mozilla/5.0 (research; open-access fetch)'},timeout=60,allow_redirects=True)
        ok=r.content[:4]==b'%PDF'
        print(n,r.status_code,ok,len(r.content),r.url[:90])
        if ok: open(f'{OUT}review{n:02d}.pdf','wb').write(r.content)
    except Exception as e: print(n,'ERR',e)
