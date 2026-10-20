import sys, json, csv, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get
R = [
 (1,'Kwong, Kwok, Wong 2023','10.3390/su152014683'),
 (2,'Dar, Badwan, Kumar 2024','10.1108/IMEFM-01-2024-0018'),
 (3,'Lucarelli, Mazzocchini, Severini 2024','10.1504/IJGE.2024.141407'),
 (4,'Saeedi, Ashraf 2024','10.3390/jrfm17100472'),
 (5,'Kozar, Wodnicka 2024','10.1016/j.procs.2024.09.643'),
 (6,'Sethi, Mahadik 2024','10.18267/j.cebr.368'),
 (7,'Aggarwal, Joshi, Gupta, Kaushik 2024','10.2139/ssrn.5042215'),
 (8,'Bansal et al. 2025','10.1016/j.ribaf.2024.102682'),
 (9,'Zournatzidou 2025','10.3390/admsci15040150'),
 (10,'Fotova Cikovic et al. 2025','10.3390/jrfm18080420'),
 (11,'Magableh et al. 2025','10.1108/JSTPM-02-2025-0033'),
 (12,'Kozar, Warwas 2025','10.1016/j.procs.2025.09.560'),
 (13,'Jaiswal, Satyanisth 2025','10.1002/sd.70611'),
 (14,'Hassan et al. 2026','10.1002/bsd2.70349'),
 (15,'Karim et al. 2026','10.1016/j.sftr.2026.102074')]
out=[]
for n,lab,doi in R:
    s,cr=get('https://api.crossref.org/works/'+doi)
    m=cr['message'] if s==200 else {}
    s2,oa=get('https://api.openalex.org/works/doi:'+doi, params={'select':'id,title,publication_year,primary_location,best_oa_location,open_access,locations,cited_by_count,type'})
    oam=oa if s2==200 else {}
    locs=[(l.get('landing_page_url'),l.get('pdf_url'),l.get('version'),l.get('license'),(l.get('source') or {}).get('display_name')) for l in oam.get('locations',[])]
    out.append(dict(n=n,label=lab,doi=doi,cr_status=s,title=(m.get('title') or [''])[0],container=(m.get('container-title') or [''])[0],
        cr_type=m.get('type'),year=(m.get('issued',{}).get('date-parts') or [[None]])[0][0],
        authors='; '.join(f"{a.get('family','')}, {a.get('given','')}" for a in m.get('author',[])),
        license=';'.join(l['URL'] for l in m.get('license',[])[:2]),
        oa_status=(oam.get('open_access') or {}).get('oa_status'),oa_url=(oam.get('open_access') or {}).get('oa_url'),
        best_pdf=((oam.get('best_oa_location') or {}).get('pdf_url')),best_land=((oam.get('best_oa_location') or {}).get('landing_page_url')),
        n_loc=len(locs), locs=json.dumps(locs)[:800], openalex_cites=oam.get('cited_by_count'), n_refs_crossref=m.get('references-count')))
os.makedirs('../data',exist_ok=True)
with open('../data/reviews15_meta.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for o in out: print(o['n'],o['cr_status'],o['year'],o['container'][:40],'|',o['oa_status'],'|',o['best_pdf'] or o['best_land'],'| refs',o['n_refs_crossref'])
