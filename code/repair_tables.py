import pandas as pd, re, collections, os, json
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
os.makedirs('../results/repair',exist_ok=True)
d=pd.read_csv('../data/scopus_export_flags.csv',dtype=str)
d['cit']=d['Cited by'].astype(float)
# --- hand-screening decisions (decisions by reading title/abstract; rule documented in repair-appendix)
ON_TOPIC_SERIES_TITLES=['Adoption of Green Banking and Finance: A Systematic Review and Future Research Directions',
 'Artificial Intelligence in Sustainable Finance: A Comprehensive Literature Review and an Integrative Framework']
def decision(r):
    if r['Source title']=='Review of Management Literature':
        if r['Title'] in ON_TOPIC_SERIES_TITLES: return 'include','on-topic chapter in contaminated series (green banking / AI in sustainable finance)'
        if r['Title'] in ('Prelims','Review of Management Literature'): return 'exclude','front matter / volume-level record, not a research paper'
        return 'exclude','off-topic chapter; matched only through volume-level keywords copied onto every record'
    if r['Title'].startswith('Funding sustainable shipping'): return 'borderline','sustainable-finance framework for shipping (Poseidon Principles) but no fintech element; kept in clean set, flagged'
    return 'include',''
dd=d.apply(decision,axis=1,result_type='expand'); d['decision']=dd[0]; d['reason']=dd[1]
d[['row','Authors','Title','Year','Source title','Document Type','Cited by','DOI','decision','reason']].to_csv('../results/repair/screening_decisions.csv',index=False)
print(d.decision.value_counts())
clean=d[d.decision!='exclude'].copy()
def kwc(df):
    c=collections.Counter()
    for k in df['Author Keywords'].dropna():
        for w in set(x.strip().lower() for x in k.split(';') if x.strip()): c[w]+=1
    return c
def ctry(df):
    c=collections.Counter()
    for a in df['Affiliations'].dropna():
        for x in set(p.split(',')[-1].strip() for p in a.split(';')): c[x]+=1
    return c
def auth(df):
    c=collections.Counter()
    for a in df['Authors'].dropna():
        for x in a.split(';'): c[x.strip()]+=1
    return c
def tab(df):
    return dict(documents=len(df),sources=df['Source title'].nunique(),mean_cites=round(df.cit.mean(),2),
      articles=int((df['Document Type']=='Article').sum()),reviews=int((df['Document Type']=='Review').sum()),
      docs_missing_type=int(df['Document Type'].isna().sum()),authors_distinct_names=len(auth(df)),
      single_authored=int(df['Authors'].fillna('').apply(lambda s:len([x for x in s.split(';') if x.strip()])==1).sum()),
      with_author_keywords=int(df['Author Keywords'].notna().sum()))
T={'raw':tab(d),'clean':tab(clean)}
json.dump(T,open('../results/repair/table1_raw_vs_clean.json','w'),indent=1)
print(json.dumps(T,indent=1))
rows=[]
kr,kc=kwc(d),kwc(clean)
for w,n in kr.most_common(25): rows.append((w,n,kc.get(w,0)))
pd.DataFrame(rows,columns=['keyword','raw_168','clean_155']).to_csv('../results/repair/table2_keywords.csv',index=False)
print(pd.DataFrame(rows,columns=['kw','raw','clean']).head(25).to_string())
cr,cc=ctry(d),ctry(clean)
pd.DataFrame([(c,n,cc.get(c,0)) for c,n in cr.most_common(20)],columns=['country','records_raw','records_clean']).to_csv('../results/repair/table3_countries.csv',index=False)
sr,sc=d['Source title'].value_counts(),clean['Source title'].value_counts()
pd.DataFrame([(s,n,int(sc.get(s,0))) for s,n in sr.head(12).items()],columns=['source','raw','clean']).to_csv('../results/repair/table5_sources.csv',index=False)
print(pd.DataFrame([(s,n,int(sc.get(s,0))) for s,n in sr.head(12).items()]))
ar,ac=auth(d),auth(clean)
pd.DataFrame([(a,n,ac.get(a,0)) for a,n in ar.most_common(12)],columns=['author','raw','clean']).to_csv('../results/repair/authors.csv',index=False)
print(ar.most_common(6))
print(d.groupby('Year').size().to_dict(), clean.groupby('Year').size().to_dict())
# Table 4
t4=clean.sort_values('cit',ascending=False).head(12)[['Title','Year','Source title','cit','DOI','Authors']]
t4.to_csv('../results/repair/table4_corrected_top12.csv',index=False)
print(t4[['Title','Year','Source title','cit']].to_string(max_colwidth=70))
