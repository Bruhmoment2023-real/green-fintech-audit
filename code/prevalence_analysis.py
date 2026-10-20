import pandas as pd, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
d=pd.read_csv('../data/prevalence/search_records.csv',dtype=str)
for c in ['has_abstract','query_terms_in_own_title_abstract','terms_only_via_container','front_matter']: d[c]=d[c].map({'True':True,'False':False})
d['year']=pd.to_numeric(d['year'],errors='coerce'); d=d[(d.year.isna())|(d.year>=2015)]
out={}
for src,g in d.groupby('src'):
    n=len(g); u=g.drop_duplicates('id'); 
    t=g.rtype.value_counts().to_dict()
    nonj=g[g.rtype.isin(['book/series','proceedings'])]
    r={'rows':n,'unique_ids':int(u.id.nunique()),'queries':int(g.q.nunique()),'by_type':t,
       'book_series_or_proceedings_rows':len(nonj),'book_series_or_proceedings_pct':round(100*len(nonj)/n,1),
       'front_matter_rows':int(g.front_matter.sum())}
    if src=='s2':
        a=g[g.has_abstract]; r['rows_with_abstract']=len(a)
        r['pct_off_terms_all_with_abstract']=round(100*(~a.query_terms_in_own_title_abstract).mean(),1)
        for k in ['journal','book/series','proceedings']:
            x=a[a.rtype==k]; r[f'pct_off_terms_{k}']=[round(100*(~x.query_terms_in_own_title_abstract).mean(),1) if len(x) else None,len(x)]
    else:
        r['container_only_matches']=int(g.terms_only_via_container.fillna(False).sum())
        r['container_only_in_book_proc']=int(nonj.terms_only_via_container.fillna(False).sum())
        for k in ['journal','book/series','proceedings']:
            x=g[g.rtype==k]; r[f'pct_title_lacks_terms_{k}']=[round(100*(~x.query_terms_in_own_title_abstract).mean(),1) if len(x) else None,len(x)]
    out[src]=r
print(json.dumps(out,indent=1))
json.dump(out,open('../results/prevalence_summary.json','w'),indent=1)
