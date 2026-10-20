import pandas as pd, re, json, os
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
d=pd.read_csv('../data/source/scopus_export_original.csv',on_bad_lines='skip',dtype=str)
d=d[d['Year'].str.match(r'^\d{4}$',na=False)].copy().reset_index(drop=True)
d['row']=d.index+2
fin=re.compile(r'fin-?tech|financial technolog|digital financ|digital inclusive|digital banking|blockchain|artificial intelligence|\bai\b|mobile payment|crowdfunding|peer-to-peer|p2p',re.I)
grn=re.compile(r'green|sustainab|environment|carbon|climate|emission|esg|net.?zero|ecolog',re.I)
gf=re.compile(r'green financ|sustainable financ|green fintech|green credit|green invest|green bond|climate financ|esg',re.I)
ft=re.compile(r'fin-?tech|financial technolog|digital financ',re.I)
def ta(r): return ' '.join(str(r.get(c,'')) for c in ['Title','Abstract'])
d['ta']=d.apply(ta,axis=1)
d['has_fin_ta']=d['ta'].str.contains(fin); d['has_grn_ta']=d['ta'].str.contains(grn)
d['has_ft_ta']=d['ta'].str.contains(ft); d['has_gf_ta']=d['ta'].str.contains(gf)
d['series']=d['Source title'].eq('Review of Management Literature')
d['lexical_core']=d['has_ft_ta']|d['has_gf_ta']
print('records',len(d),'series',d.series.sum())
print('no fintech/digital finance AND no green-finance term in title/abstract:',(~d.lexical_core).sum())
print(d.loc[~d.lexical_core,['row','Source title','Title']].to_string(max_colwidth=90))
d.drop(columns=['ta']).to_csv('../data/scopus_export_flags.csv',index=False)
