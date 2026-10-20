import requests,re,sys,html
H={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)'}
def ft(pmcid,out):
    x=requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML',headers=H,timeout=90).text
    x=re.sub(r'</(p|title|tr|sec|label|caption)>','\n',x); x=re.sub(r'</t[dh]>',' | ',x); x=re.sub(r'<[^>]+>','',x)
    open(out,'w',encoding='utf-8').write(html.unescape(x)); print(out,len(x))
for p,o in [('PMC10722750','biblio'),('PMC8270366','prismas'),('PMC8005924','prisma2020')]:
    ft(p,f'../data/fulltext/guideline_{o}.txt')
