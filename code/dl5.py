import requests,re,time
H={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)'}
for u in ['https://digitalcommons.mtu.edu/michigantech-p2/2887','https://digitalcommons.mtu.edu/cgi/viewcontent.cgi?article=3886&context=michigantech-p2']:
  for i in range(3):
    try:
        r=requests.get(u,headers=H,timeout=40); print(u[-40:],r.status_code,len(r.content),r.content[:4]); 
        for m in re.findall(r'(https?://[^"\']*viewcontent[^"\']*)',r.text)[:3]: print(m)
        break
    except Exception as e: print('err',str(e)[:60]); time.sleep(3)
