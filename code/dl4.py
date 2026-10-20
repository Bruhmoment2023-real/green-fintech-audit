import requests
H={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)'}
for n,u in [(4,'https://mdpi-res.com/d_attachment/jrfm/jrfm-17-00472/article_deploy/jrfm-17-00472.pdf'),(10,'https://mdpi-res.com/d_attachment/jrfm/jrfm-18-00420/article_deploy/jrfm-18-00420.pdf')]:
    d=requests.get(u,headers=H,timeout=60); print(n,d.status_code,d.content[:4],len(d.content))
    if d.content[:4]==b'%PDF': open(f'E:/Research-Staging/10-green-fintech-audit/pdfs/review{n:02d}.pdf','wb').write(d.content)
