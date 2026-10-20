import re, csv, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
t=open('C:/Users/seans/AppData/Local/Temp/claude/C--Users-seans/50bb9313-7d10-45ea-a6f0-57d4ba7c8693/scratchpad/ms.txt',encoding='utf-8').read()
body=t.split('\nReferences:')[0]; refs=t.split('\nReferences:')[1]
cites=re.findall(r'([A-Z][A-Za-z\u00C0-\u017F\-]+)(?: (?:et al\.|&|and) ?(?:[A-Z][A-Za-z\-]+)?)?,? \(?(20\d\d)\)?',body)
cites=re.findall(r'\(([^()]*?(?:19|20)\d\d[^()]*?)\)',body)
pairs=set()
for c in cites:
    for part in c.split(';'):
        m=re.match(r'\s*([A-Z][A-Za-z\-]+)(?: et al\.| & [A-Z][A-Za-z\-]+)?,? ((?:19|20)\d\d)',part)
        if m: pairs.add((m.group(1),m.group(2)))
reflines=[l for l in refs.split('\n') if l.strip()]
out=[]
for a,y in sorted(pairs):
    inlist=any(l.strip().startswith(a) and y in l for l in reflines)
    out.append((a,y,inlist))
for o in out: print(o)
listed_not_cited=[l[:60] for l in reflines if not any(a in l[:40] and y in l for a,y in pairs)]
print('LISTED BUT NOT CITED:',listed_not_cited)
w=csv.writer(open('../results/repair/intext_vs_list.csv','w',newline='',encoding='utf-8')); w.writerow(['first_author','year','in_reference_list']); w.writerows(out)
