"""Tiny cached HTTP helper for pack 10 (no email or personal identifier is ever sent).
Responses (200/404 only) are cached in data/cache/http.sqlite so re-runs never refetch.
Per-host minimum intervals; exponential back-off on 429/5xx."""
import os, sqlite3, time, zlib, json, threading, hashlib
import requests
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, '..', 'data', 'cache', 'http.sqlite')
UA = 'ReproAuditResearch/1.0 (open-data audit; no personal identifiers)'
INTERVAL = {'api.crossref.org': 0.25, 'api.openalex.org': 0.15, 'api.semanticscholar.org': 1.3,
            'doaj.org': 0.5, 'export.arxiv.org': 3.1}
_next = {}; _lk = threading.Lock(); _conn = None
def _db():
    global _conn
    if _conn is None:
        if not os.path.exists('D://'): raise SystemExit('D: missing')
        os.makedirs(os.path.dirname(DB), exist_ok=True)
        _conn = sqlite3.connect(DB, check_same_thread=False, timeout=60)
        _conn.execute('CREATE TABLE IF NOT EXISTS h (k TEXT PRIMARY KEY, status INT, body BLOB, ts REAL)')
    return _conn
def get(url, params=None, as_json=True, tries=6, binary=False):
    req = requests.Request('GET', url, params=params).prepare()
    key = hashlib.sha1(req.url.encode()).hexdigest()
    with _lk:
        r = _db().execute('SELECT status, body FROM h WHERE k=?', (key,)).fetchone()
    if r is not None and not binary:
        txt = zlib.decompress(r[1]).decode('utf-8', 'replace')
        return r[0], (json.loads(txt) if (as_json and r[0] == 200) else txt)
    host = req.url.split('/')[2]
    for i in range(tries):
        with _lk:
            now = time.time(); t = max(now, _next.get(host, 0)); _next[host] = t + INTERVAL.get(host, 0.5)
        if t > now: time.sleep(t - now)
        try:
            resp = requests.get(req.url, headers={'User-Agent': UA}, timeout=60)
        except Exception as e:
            time.sleep(2 ** i); continue
        if resp.status_code in (429, 500, 502, 503, 504):
            ra = resp.headers.get('Retry-After')
            time.sleep(min(float(ra) if ra and ra.isdigit() else 2 ** (i + 2), 120)); continue
        if binary: return resp.status_code, resp.content
        if resp.status_code in (200, 404):
            with _lk:
                _db().execute('INSERT OR REPLACE INTO h VALUES (?,?,?,?)', (key, resp.status_code, zlib.compress(resp.text.encode()), time.time())); _db().commit()
        txt = resp.text
        if resp.status_code == 200 and as_json:
            try: return 200, json.loads(txt)
            except Exception: return 200, txt
        return resp.status_code, txt
    return 0, None
