import pandas as pd, os, difflib
os.chdir(os.path.dirname(os.path.abspath(__file__)))
ms=[(1,'The impact of fintech innovation on green growth in China: Mediating effect',2022,'Resources Policy',512),
(2,'Nexus between green finance, fintech, and high-quality economic development: Empirical evidence from China',2021,'Resources Policy',386),
(3,'FinTech and sustainability: Do they affect each other?',2021,'Sustainability',292),
(4,'The drivers of environmental sustainability in BRICS economies: Do green finance and fintech matter?',2023,'Sustainable Dev.',204),
(5,'Green finance, fintech, and environmental sustainability: Fresh policy insights from BRICS nations',2023,'Finance Res. Lett.',178),
(6,'The role of fintech in promoting green finance and profitability: Evidence from China',2023,'Resources Policy',139),
(7,'Striving for the United Nations (UN) SDGs in presence of FinTech and green finance',2023,'Sustainable Dev.',109),
(8,'The fourth industrial revolution and environmental efficiency: The role of green finance and FinTech',2022,'Resources Policy',109),
(9,'Empirical evidence of fintech and green environment: Using the green finance index',2024,'Resources Policy',101),
(10,'Analysis of the carbon emission reduction effect of FinTech and its transmission mechanism',2023,'Resources Policy',96)]
src=pd.read_csv('../results/repair/table4_corrected_top12.csv',dtype=str)
src['cit']=src['cit'].astype(float)
norm={'Sustainable Dev.':'Sustainable Development','Finance Res. Lett.':'Finance Research Letters','Sustainability':'Sustainability (Switzerland)'}
rows=[]
for i,(n,t,y,s,c) in enumerate(ms):
    sims=[difflib.SequenceMatcher(None,t.lower(),x.lower()).ratio() for x in src['Title']]
    e=src.iloc[max(range(len(sims)),key=lambda k:sims[k])]
    sim=difflib.SequenceMatcher(None,t.lower(),e['Title'].lower()).ratio()
    src_ok=norm.get(s,s)==e['Source title']
    rows.append(dict(rank=n,ms_title=t,export_title=e['Title'],title_similarity=round(sim,2),title_exact=(t.lower()==e['Title'].lower()),ms_year=y,export_year=e['Year'],year_ok=str(y)==e['Year'],
      ms_source=s,export_source=e['Source title'],source_ok=src_ok,ms_cites=c,export_cites=int(e['cit']),cites_ok=c==int(e['cit']),doi=e['DOI']))
r=pd.DataFrame(rows); r.to_csv('../results/repair/table4_comparison.csv',index=False)
print(r[['rank','title_similarity','title_exact','year_ok','source_ok','cites_ok']].to_string())
print('wrong sources',(~r.source_ok).sum(),'| titles not identical',(~r.title_exact).sum(),'| cites ok',r.cites_ok.sum(),'| years ok',r.year_ok.sum())
