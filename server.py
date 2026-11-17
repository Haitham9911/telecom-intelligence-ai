#!/usr/bin/env python3
"""Telecom Intelligence AI — local-first read-only demo backend, Python stdlib."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, sqlite3, os, sys, csv, io, threading, datetime
import updater,quotes,financial_refresh
ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'intelligence.sqlite3'
SEED=json.loads((ROOT/'data'/'seed.json').read_text(encoding='utf-8'))

def initialize():
    DB.parent.mkdir(exist_ok=True)
    con=sqlite3.connect(DB)
    con.executescript("""CREATE TABLE IF NOT EXISTS companies(id TEXT PRIMARY KEY,name TEXT,country TEXT,exchange TEXT,source TEXT);
      CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,label TEXT,url TEXT,published TEXT,checked TEXT,mode TEXT);
      CREATE TABLE IF NOT EXISTS facts(company_id TEXT,period TEXT,metric TEXT,value REAL,unit TEXT,precision TEXT,growth_yoy REAL,source_id TEXT,PRIMARY KEY(company_id,period,metric,source_id));
      CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,company_id TEXT,date TEXT,category TEXT,title TEXT,summary TEXT,impact TEXT,source_id TEXT);
      CREATE TABLE IF NOT EXISTS watchlist(company_id TEXT PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS alert_rules(id TEXT PRIMARY KEY,enabled INTEGER);""")
    for x in SEED['companies']:con.execute('INSERT OR IGNORE INTO companies VALUES (?,?,?,?,?)',tuple(x.values()))
    for x in SEED['sources']:con.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?)',(x['id'],x['label'],x['url'],x.get('published'),x.get('checked'),x['mode']))
    for x in SEED['facts']:con.execute('INSERT OR IGNORE INTO facts VALUES (?,?,?,?,?,?,?,?)',(x['company_id'],x['period'],x['metric'],x['value'],x['unit'],x.get('precision'),x.get('growth_yoy'),x['source_id']))
    for x in SEED['events']:con.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?,?)',(x['id'],x['company_id'],x['date'],x['category'],x['title'],x['summary'],x['impact'],x['source_id']))
    con.commit();con.close()

def feed_rows():
    with updater.connect() as db:
        items=[dict(r) for r in db.execute('SELECT * FROM feed_items ORDER BY COALESCE(published,discovered) DESC LIMIT 2000')]
        for item in items:item['company_ids']=json.loads(item.get('company_ids') or '[]')
        return [x for x in items if x.get('kind')!='aggregator' or updater.companies_in(x['title'])]

def health_rows():
    with updater.connect() as db:
        return [dict(r) for r in db.execute('SELECT * FROM feed_health ORDER BY feed_id')]

def rows(table):
    with sqlite3.connect(DB) as db:
        db.row_factory=sqlite3.Row
        return [dict(r) for r in db.execute('SELECT * FROM '+table)]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path.startswith('/api/'):
            mapping={'/api/companies':'companies','/api/facts':'facts','/api/events':'events','/api/sources':'sources'}
            if u.path in ('/api/five-years.csv','/api/operating-metrics.csv'):
                path=ROOT/'data'/('operating-metrics.csv' if u.path.endswith('operating-metrics.csv') else 'five-year-financials.csv')
                if not path.exists():self.send_error(404);return
                payload=path.read_bytes();self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.end_headers();self.wfile.write(payload);return
            if u.path=='/api/stock-quotes':self.json(quotes.read(ROOT/'data'/'stock-quotes.json'));return
            if u.path=='/api/indicators':self.json(financial_refresh.combined(ROOT/'data'));return
            if u.path=='/api/financial-indicators.csv':
                financial_refresh.export(ROOT/'data');payload=(ROOT/'data'/'financial-indicators.csv').read_bytes();self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.end_headers();self.wfile.write(payload);return
            if u.path=='/api/seed':self.json(SEED);return
            if u.path=='/api/status':
                health=health_rows()
                self.json({'mode':'scheduled-public-rss','poll_interval_seconds':updater.INTERVAL,'worker_enabled':os.getenv('ENABLE_FEEDS','1')=='1','last_checked':max([f['last_checked'] for f in health if f['last_checked']],default=None),'last_success':max([f['last_success'] for f in health if f['last_success']],default=None),'feeds_ok':sum(bool(f['last_success'] and not f['last_error']) for f in health),'feeds_failed':sum(bool(f['last_error']) for f in health),'financial_kpis_live':False,'msx_connected':False,'message':'Public news headlines may update while server is running and Internet is available; MSX and financial KPIs are not live.'});return
            if u.path=='/api/live-news':self.json(feed_rows());return
            if u.path=='/api/feed-health':self.json(health_rows());return
            if u.path in mapping:
                result=SEED[mapping[u.path]];q=parse_qs(u.query)
                if 'company_id' in q:result=[x for x in result if x.get('company_id',x.get('id'))==q['company_id'][0]]
                self.json(result);return
            if u.path=='/api/export.csv':
                s=io.StringIO();w=csv.DictWriter(s,fieldnames=['company_id','scope','period','metric','value','previous_value','previous_period','comparison_basis','unit','precision','growth_yoy','growth_basis','source_id']);w.writeheader();w.writerows(SEED['facts'])
                b=s.getvalue().encode('utf-8-sig');self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="telecom_verified_facts.csv"');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
            self.json({'error':'not found'},404);return
        if u.path=='/':self.path='/index.html'
        elif u.path.startswith('/data/') or u.path in ('/feeds.json','/updater.py','/server.py','/README.md','/test_app.py') or u.path.endswith(('.sqlite3','.py','.json','.zip')) or '/.' in u.path:self.send_error(403);return
        super().do_GET()
    def json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
if __name__=='__main__':
    initialize()
    updater.connect().close()
    if os.environ.get('ENABLE_FEEDS','1')=='1':
        threading.Thread(target=updater.worker_loop,daemon=True,name='feed-worker').start()
    port=int(os.environ.get('PORT','8765'));print(f'Telecom Intelligence AI running at http://localhost:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
