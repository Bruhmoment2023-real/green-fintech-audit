import sys,os
from pypdf import PdfReader
src='E:/Research-Staging/10-green-fintech-audit/pdfs/'; out='D:/Research-Publishing/10-green-fintech-audit/data/fulltext/'
for f in sorted(os.listdir(src)):
    if f.endswith('.pdf'):
        r=PdfReader(src+f); t=''
        for i,p in enumerate(r.pages): t+=f'\n\n=====PAGE {i+1}=====\n'+(p.extract_text() or '')
        open(out+f[:-4]+'.txt','w',encoding='utf-8').write(t); print(f,len(r.pages),len(t))
