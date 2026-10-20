"""Second-coder check: a keyword/regex detector (written before looking at the manual scores' per-item agreement) is run on the six opened texts
and compared with the hand scores on 'reported at all' (score >= 1). With 6 papers x 9 items this is a sanity check, not a reliability estimate.
Output: results/auto_vs_manual.csv, results/auto_vs_manual_summary.json"""
import re, os, csv, json, zipfile, html, unicodedata
os.chdir(os.path.dirname(os.path.abspath(__file__)))
def clean(t):
    t = unicodedata.normalize('NFKC', t)
    t = re.sub(r'(?<=\w)-\s+(?=\w)', '', t)
    return re.sub(r'\s+', ' ', t)
texts = {f'R{n:02d}': clean(open(f'../data/fulltext/review{n:02d}.txt', encoding='utf-8').read()) for n in (1, 4, 6, 9, 10)}
x = zipfile.ZipFile('../data/source/manuscript_2026-05-24.docx').read('word/document.xml').decode('utf8')
texts['S0'] = clean(html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', x))))
DET = {
 'R1': r'(scopus|web of science|\bwos\b|google scholar|dimensions|econlit)',
 'R2': r'(\bAND\b|\bOR\b)[^.]{0,80}(\bAND\b|\bOR\b)|TITLE-ABS-KEY|TS ?=|title, abstract',
 'R3': r'(search|retriev|download|extract|data|survey)[^.]{0,60}(initiated|conducted|performed|carried out|accessed|obtained|collected|retrieved)[^.]{0,40}(january|february|march|april|may|june|july|august|september|october|november|december)\s+(19|20)\d\d|(accessed|until|up to)[^.]{0,30}(january|february|march|april|may|june|july|august|september|october|november|december)',
 'R4': r'(limited to|restricted to|only (journal )?articles|written in english|english[- ]language|language)',
 'R5': r'(inclusion|exclusion) criteria|eligib',
 'R6': r'(\bn ?= ?\d+|\b\d{2,5} (papers|articles|documents|publications|records))[^.]{0,80}(screen|included|final|selected|retriev|obtained|identified|resulted)|(screen|included|final|selected|retriev|obtained|identified|resulted)[^.]{0,80}\b\d{2,5} (papers|articles|documents|publications|records)',
 'R7': r'duplicate|de-?duplic|thesaurus|synonym|cleaning|cleaned|merged|verified twice|screened',
 'R8': r'(vosviewer|bibliometrix|biblioshiny|r software|rstudio)[^.]{0,25}\b(version )?\d+\.\d+(\.\d+)?',
 'R10': r'data availab|available on request|supplementary material|repository|github|zenodo|osf\.io|figshare'}
manual = {}
for r in csv.DictReader(open('../results/rubric_scores_long.csv', encoding='utf-8')):
    key = r['paper'][:3].strip() if not r['paper'].startswith('S0') else 'S0'
    manual[(key, r['item'])] = r['score']
rows = []; agree = 0; n = 0; tp = fp = fn = tn = 0
for p, t in texts.items():
    for it, pat in DET.items():
        m = manual.get((p, it))
        if m in (None, ''): continue
        auto = bool(re.search(pat, t, re.I)); man = int(m) >= 1
        rows.append(dict(paper=p, item=it, auto_detected=auto, manual_reported=man, agree=(auto == man)))
        n += 1; agree += (auto == man)
        tp += auto and man; fp += auto and not man; fn += (not auto) and man; tn += (not auto) and (not man)
po = agree / n; pe = ((tp + fp) / n) * ((tp + fn) / n) + ((fn + tn) / n) * ((fp + tn) / n)
kappa = (po - pe) / (1 - pe) if pe < 1 else float('nan')
w = csv.DictWriter(open('../results/auto_vs_manual.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
res = dict(n_judgements=n, agreement_pct=round(100 * po, 1), cohen_kappa=round(kappa, 2), auto_yes_manual_yes=int(tp), auto_yes_manual_no=int(fp), auto_no_manual_yes=int(fn), auto_no_manual_no=int(tn),
           disagreements=[(r['paper'], r['item'], 'auto yes, manual no' if r['auto_detected'] else 'auto no, manual yes') for r in rows if not r['agree']])
json.dump(res, open('../results/auto_vs_manual_summary.json', 'w'), indent=1); print(json.dumps(res, indent=1))
