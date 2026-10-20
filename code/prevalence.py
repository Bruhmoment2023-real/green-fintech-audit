"""Prevalence test: how often do book-series / proceedings / front-matter records enter topic searches on green finance x fintech,
and how often are they off-topic by their own title/abstract?

Sources (free, no login, no personal identifier in any request): Semantic Scholar Graph API (relevance search, abstracts + venue types)
and Crossref REST (bibliographic search). OpenAlex list/search calls were NOT used because the keyless daily budget is shared and nearly exhausted;
OpenAlex single-record lookups (free) are used only for the 15 series chapters (test C).
Outputs: data/prevalence/*.csv, results/prevalence_summary.json. Resumable: every HTTP response is cached (data/cache/http.sqlite)."""
import sys, os, re, json, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'prevalence'); os.makedirs(OUT, exist_ok=True)

QUERIES = [
 'green fintech', 'fintech green finance', 'fintech and green finance', 'digital finance green finance', 'fintech carbon emissions',
 'fintech environmental sustainability', 'fintech sustainable development', 'green finance bibliometric analysis', 'green finance systematic review',
 'fintech bibliometric analysis', 'sustainable finance fintech', 'blockchain green finance', 'artificial intelligence green finance',
 'green bonds fintech', 'ESG fintech', 'climate finance technology', 'green credit digital finance', 'financial inclusion carbon emissions',
 'digital finance carbon emissions', 'green finance carbon neutrality', 'green technology innovation fintech', 'fintech energy transition',
 'fintech renewable energy', 'fintech natural resources', 'crowdfunding renewable energy', 'peer-to-peer lending sustainability',
 'green banking digital', 'robo-advisor sustainable investing', 'carbon markets blockchain', 'fintech ESG disclosure',
 'green finance', 'fintech', 'sustainable finance', 'ESG investing', 'climate finance', 'carbon neutrality finance', 'digital finance',
 'green innovation finance', 'fintech China environmental', 'fintech India sustainability', 'fintech SMEs green', 'green finance supply chain',
 'sustainable finance artificial intelligence', 'fintech sustainability literature review', 'green finance research agenda', 'fintech adoption sustainability',
 'financial technology environmental performance', 'green finance digital leadership', 'central bank digital currency climate', 'insurtech climate risk']
S2_MAX = int(os.environ.get('S2_MAX', '20'))
STOP = set('and the of in for on to a an'.split())
def stems(q):
    return [w[:6].lower() for w in re.findall(r"[A-Za-z\-]+", q) if w.lower() not in STOP]
FRONT = re.compile(r'^(prelims|front matter|frontmatter|contents|table of contents|preface|foreword|acknowledg\w+|index|list of (figures|tables|contributors|abbreviations)|about the (authors?|editors?)|editorial board|cover|title page|introduction to (the )?(volume|series))\b', re.I)

def s2_search(q, pages=1):
    res = []
    for p in range(pages):
        s, j = get('https://api.semanticscholar.org/graph/v1/paper/search', params={
            'query': q, 'limit': 100, 'offset': p * 100,
            'fields': 'title,abstract,year,venue,publicationTypes,publicationVenue,externalIds'}, tries=3)
        if s != 200 or not isinstance(j, dict): break
        res += j.get('data', [])
        if len(j.get('data', [])) < 100: break
    return res

def cr_search(q, rows=100):
    s, j = get('https://api.crossref.org/works', params={'query.bibliographic': q, 'rows': rows,
               'select': 'DOI,title,container-title,type,publisher,issued,subject,abstract', 'filter': 'from-pub-date:2015'})
    return j['message']['items'] if s == 200 else []

def classify_s2(r):
    pt = r.get('publicationTypes') or []
    pv = (r.get('publicationVenue') or {}).get('type') or ''
    if 'JournalArticle' in pt or pv == 'journal': return 'journal'
    if 'Conference' in pt or pv == 'conference': return 'proceedings'
    if 'BookSection' in pt or 'Book' in pt or pv in ('book', 'book series'): return 'book/series'
    if pt: return 'other:' + pt[0]
    return 'unknown'

rows = []
for qi, q in enumerate(QUERIES):
    st = stems(q)
    for r in (s2_search(q) if qi < S2_MAX else []):
        txt = ((r.get('title') or '') + ' ' + (r.get('abstract') or '')).lower()
        has_abs = bool(r.get('abstract'))
        hit = all(s in txt for s in st)
        rows.append(dict(src='s2', q=q, id=(r.get('externalIds') or {}).get('DOI') or r.get('paperId'), title=r.get('title'), year=r.get('year'),
                         venue=r.get('venue'), rtype=classify_s2(r), has_abstract=has_abs, query_terms_in_own_title_abstract=hit,
                         front_matter=bool(FRONT.match((r.get('title') or '').strip()) or (r.get('title') or '').strip().lower() == (r.get('venue') or '').strip().lower())))
    print('s2', qi, q, len([x for x in rows if x['src'] == 's2' and x['q'] == q]), flush=True)
    for r in cr_search(q):
        t = (r.get('title') or [''])[0]; c = (r.get('container-title') or [''])[0]
        ty = r.get('type'); g = {'journal-article': 'journal', 'proceedings-article': 'proceedings', 'book-chapter': 'book/series', 'book': 'book/series', 'monograph': 'book/series', 'edited-book': 'book/series', 'book-part': 'book/series', 'book-section': 'book/series', 'reference-entry': 'book/series'}.get(ty, 'other:' + str(ty))
        own = all(s in (t + ' ' + (r.get('abstract') or '')).lower() for s in st)
        cont = all(s in (t + ' ' + c).lower() for s in st)
        rows.append(dict(src='crossref', q=q, id=r.get('DOI'), title=t, year=(r.get('issued', {}).get('date-parts') or [[None]])[0][0], venue=c,
                         rtype=g, has_abstract=bool(r.get('abstract')), query_terms_in_own_title_abstract=own, terms_only_via_container=(cont and not own),
                         front_matter=bool(FRONT.match(t.strip()) or (t.strip() and t.strip().lower() == c.strip().lower()))))
    print('cr', qi, q, flush=True)
with open(os.path.join(OUT, 'search_records.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['src', 'q', 'id', 'title', 'year', 'venue', 'rtype', 'has_abstract', 'query_terms_in_own_title_abstract', 'terms_only_via_container', 'front_matter'])
    w.writeheader(); w.writerows(rows)
print('records', len(rows))
