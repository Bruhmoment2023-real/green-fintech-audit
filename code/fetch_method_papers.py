"""Locate and fetch open copies of the methodological papers used for the rubric and reading notes.
Order: OpenAlex best_oa_location / locations (single lookups, free) -> direct PDF fetch (no evasion of 403s; a block is logged and skipped).
PDFs go to E:\\Research-Staging\\10-green-fintech-audit\\pdfs\\ (staging; logged in STAGING.md); extracted text to data/fulltext/."""
import sys, os, json, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get
from pypdf import PdfReader
STAGE = 'E:/Research-Staging/10-green-fintech-audit/pdfs/'
TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'fulltext') + os.sep
PAPERS = {'farooq2023': '10.1007/s11192-023-04765-8', 'baas2020': '10.1162/qss_a_00019', 'aria2017': '10.1016/j.joi.2017.08.007',
          'donthu2021': '10.1016/j.jbusres.2021.04.070', 'gusenbauer2020': '10.1002/jrsm.1378', 'zupic2015': '10.1177/1094428114562629',
          'gusenbauer2019': '10.1007/s11192-018-2958-5', 'ellegaard2015': '10.1007/s11192-015-1645-z'}
H = {'User-Agent': 'ReproAuditResearch/1.0 (open-data audit)'}
log = {}
for k, doi in PAPERS.items():
    s, j = get('https://api.openalex.org/works/doi:' + doi, params={'select': 'title,open_access,best_oa_location,locations'})
    urls = []
    if s == 200:
        for l in [j.get('best_oa_location')] + (j.get('locations') or []):
            if l and l.get('pdf_url') and l['pdf_url'] not in urls: urls.append(l['pdf_url'])
    ok = False
    for u in urls[:4]:
        try:
            r = requests.get(u, headers=H, timeout=60)
            if r.content[:4] == b'%PDF':
                open(STAGE + k + '.pdf', 'wb').write(r.content)
                rd = PdfReader(STAGE + k + '.pdf'); t = ''
                for i, p in enumerate(rd.pages): t += f'\n\n=====PAGE {i+1}=====\n' + (p.extract_text() or '')
                open(TXT + k + '.txt', 'w', encoding='utf-8').write(t); ok = True
                log[k] = dict(doi=doi, url=u, pages=len(rd.pages), status='opened in full'); break
            else: log.setdefault(k, {}).update(dict(doi=doi, last_http=r.status_code, tried=urls))
        except Exception as e: log.setdefault(k, {}).update(dict(doi=doi, error=str(e)[:80], tried=urls))
    if not ok: log.setdefault(k, {}).update(dict(doi=doi, status='no open PDF reachable', oa=(j.get('open_access') if s == 200 else None)))
    print(k, log[k].get('status'), log[k].get('url', ''), flush=True)
json.dump(log, open('../data/method_papers_fetch_log.json', 'w'), indent=1)
