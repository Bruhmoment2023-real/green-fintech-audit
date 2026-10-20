import requests,re
H={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)'}
r=requests.get('https://digitalcommons.mtu.edu/michigantech-p2/2887',headers=H,timeout=60)
print(re.findall(r'href="([^"]*viewcontent[^"]*)"',r.text)[:3])
for u in re.findall(r'href="([^"]*viewcontent[^"]*)"',r.text)[:1]:
    d=requests.get(u,headers=H,timeout=60); print(d.status_code,d.content[:4],len(d.content))
    if d.content[:4]==b'%PDF': open('E:/Research-Staging/10-green-fintech-audit/pdfs/review15.pdf','wb').write(d.content)
for n,u in [(1,'http://ira.lib.polyu.edu.hk/bitstream/10397/106178/1/sustainability-15-14683.pdf'),(1,'https://ira.lib.polyu.edu.hk/bitstream/10397/106178/1/sustainability-15-14683.pdf')]:
    try:
        d=requests.get(u,headers=H,timeout=60); print(n,d.status_code,d.content[:4],len(d.content))
        if d.content[:4]==b'%PDF': open(f'E:/Research-Staging/10-green-fintech-audit/pdfs/review{n:02d}.pdf','wb').write(d.content); break
    except Exception as e: print(e)
