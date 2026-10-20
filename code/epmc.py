import requests,re,sys
H={'User-Agent':'ReproAuditResearch/1.0 (open-data audit)'}
def pmc(doi):
    r=requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',params={'query':f'DOI:{doi}','format':'json','resultType':'lite'},headers=H,timeout=60).json()
    return [(x.get('pmcid'),x.get('title')) for x in r['resultList']['result']]
for d in sys.argv[1:]:
    print(d,pmc(d))
