"""Hand labels (by reading title and container) for a random sample of 60 Crossref book/series/proceedings records whose query terms occur
only in the container title (random_state=17). F = front/back matter or bare section title (Index, Copyright, Foreword, Chapter 1 Introduction);
G = generic or unrelated chapter pulled in by the container title; B = borderline (touches the theme, misses the query); R = relevant to the query."""
import pandas as pd, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
L={3847:'G',4588:'R',2630:'F',2636:'R',5213:'R',1761:'R',4340:'F',807:'G',4099:'F',4999:'B',368:'G',2602:'R',3874:'G',3865:'G',1825:'B',3819:'G',3384:'R',342:'R',3221:'G',5100:'R',
4934:'B',3984:'R',4958:'R',2662:'R',4935:'B',3817:'G',1795:'R',1928:'R',2617:'F',1971:'R',4046:'F',3838:'G',4173:'F',2933:'G',4988:'G',3891:'G',3331:'B',3831:'G',5300:'G',2908:'R',
3884:'G',1229:'R',4179:'F',3316:'R',3846:'G',2693:'R',2006:'R',5105:'R',1247:'R',1853:'R',3881:'G',1900:'B',3678:'R',3323:'R',3408:'G',2622:'R',4941:'R',1896:'B',2610:'F',3875:'G'}
d=pd.read_csv('../data/prevalence/search_records.csv',dtype=str)
x=d[(d.src=='crossref')&(d.rtype.isin(['book/series','proceedings']))&(d.terms_only_via_container=='True')].drop_duplicates('id')
s=x.sample(60,random_state=17).copy(); s['hand_label']=s.index.map(L)
assert s.hand_label.notna().all(), s[s.hand_label.isna()].index.tolist()
s[['q','id','title','venue','rtype','hand_label']].to_csv('../results/prevalence_hand_labelled_sample.csv',index=False)
c=s.hand_label.value_counts().to_dict(); print(len(x),c)
n=len(s); import math
def ci(k): p=k/n; h=1.96*math.sqrt(p*(1-p)/n); return [round(100*p,1),round(100*max(0,p-h),1),round(100*min(1,p+h),1)]
out={'unique_container_only_book_proceedings_records':len(x),'sample':n,'counts':c,'off_topic_F_plus_G_pct_with_95ci':ci(c.get('F',0)+c.get('G',0)),'borderline_pct':ci(c.get('B',0)),'relevant_pct':ci(c.get('R',0))}
print(out); json.dump(out,open('../results/prevalence_hand_label_summary.json','w'),indent=1)
