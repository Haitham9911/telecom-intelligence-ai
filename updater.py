#!/usr/bin/env python3
"""Public-feed monitor. Headlines only; no fabricated financial KPIs or MSX price feed.

Usage: python updater.py --once ; python updater.py --loop
The host must have Internet access, and feed usage must meet provider terms.
"""
import argparse, datetime as dt, email.utils, hashlib, json, os, re, sqlite3, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from html import unescape

ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'intelligence.sqlite3'
FEEDS_FILE=ROOT/'feeds.json'
INTERVAL=max(300,int(os.getenv('FEED_POLL_SECONDS','1800')))
USER_AGENT='TelecomIntelligenceResearch/0.3 (+personal research; public RSS headlines)'
MAX_RESPONSE=2_000_000


def connect():
    con=sqlite3.connect(DB, timeout=15)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA busy_timeout=15000')
    con.executescript('''CREATE TABLE IF NOT EXISTS feed_items (
        id TEXT PRIMARY KEY, feed_id TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL,
        published TEXT, discovered TEXT NOT NULL, company_id TEXT, category TEXT NOT NULL,
        impact TEXT NOT NULL DEFAULT 'Review', summary TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT 'secondary');
        CREATE TABLE IF NOT EXISTS feed_health (
        feed_id TEXT PRIMARY KEY, label TEXT NOT NULL, url TEXT NOT NULL, enabled INTEGER NOT NULL,
        last_checked TEXT, last_success TEXT, last_error TEXT, last_http_status INTEGER,
        received_count INTEGER NOT NULL DEFAULT 0, etag TEXT, last_modified TEXT);
        CREATE INDEX IF NOT EXISTS idx_feed_items_discovered ON feed_items(discovered DESC);
        CREATE INDEX IF NOT EXISTS idx_feed_items_company ON feed_items(company_id);''')
    for name in ("company_ids", "publisher"):
        if name not in {r[1] for r in con.execute("PRAGMA table_info(feed_items)")}:
            con.execute("ALTER TABLE feed_items ADD COLUMN " + name + " TEXT")
    return con


def utcnow():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def normalized_date(value):
    if not value:return None
    try:
        d=email.utils.parsedate_to_datetime(value)
        if d:return d.astimezone(dt.timezone.utc).isoformat(timespec='seconds')
    except (ValueError,TypeError,OverflowError):pass
    try:return dt.datetime.fromisoformat(value.strip().replace('Z','+00:00')).astimezone(dt.timezone.utc).isoformat(timespec='seconds')
    except (ValueError,TypeError):return None


def text_of(element, names):
    for child in element.iter():
        if child is element:continue
        if child.tag.split('}')[-1].lower() in names and child.text and child.text.strip():return child.text.strip()
    return ''


def parse_feed(data):
    """Support RSS 2.0 and Atom 1.0 (title/url/date/description only)."""
    root=ET.fromstring(data)
    if root.tag.split('}')[-1].lower() not in ('rss','feed','rdf'):raise ValueError('Not a recognized RSS/Atom feed')
    out=[]
    for node in root.iter():
        if node.tag.split('}')[-1].lower() not in ('item','entry'):continue
        title=unescape(re.sub(r'<[^>]*>','',text_of(node,{'title'}))).strip()
        link=text_of(node,{'link'})
        if not link:
            for ch in node:
                if ch.tag.split('}')[-1]=='link' and ch.attrib.get('href'):
                    link=ch.attrib['href'];break
        if not link:
            link=text_of(node,{'guid','id'})
        parsed=urlparse(link)
        if not title or parsed.scheme!='https' or not parsed.hostname:continue
        description=text_of(node,{'description','summary','subtitle'})
        description=unescape(re.sub(r'<[^>]*>',' ',description))
        description=re.sub(r'\s+',' ',description).strip()[:450]
        published=normalized_date(text_of(node,{'pubdate','published','updated','date'}))
        out.append({'title':title[:320],'url':link[:1500],'summary':'','published':published,'publisher':text_of(node,{'source'})[:120]})
    return out[:80]

COMPANY_TERMS=[('ZAIN',r'\bzain\b|زين'),('OTEL',r'\bomantel\b|\bzoi\b|عمانتل'),('ORED',r'ooredoo oman|أوريدو ع[ُ]?مان|اوريدو عمان'),('ORDS',r'\booredoo\b|أوريدو|اوريدو'),('STC',r'\bstc\b|saudi telecom|السعودية للاتصالات|الاتصالات السعودية|إس تي سي'),('EAND',r'(?<!\w)e\s*&(?=\s|$|[^a-z])|\betisalat\b|اتصالات الإمارات|مجموعة إي|إي آند'),('VOD',r'\bvodafone\b|فودافون'),('DTE',r'deutsche telekom'),('SINGTEL',r'\bsingtel\b')]

def companies_in(title):
    ids=[company for company,pattern in COMPANY_TERMS if re.search(pattern,title,re.I)]
    # Explicit Oman operating-company news stays distinct unless Group is also named.
    if 'ORED' in ids and not re.search(r'ooredoo group|مجموعة أوريدو|مجموعة اوريدو',title,re.I):
        ids=[x for x in ids if x!='ORDS']
    return ids

def categorize(title):
    t=title.lower(); ids=companies_in(title)
    if re.search(r'earnings|financial results|net profit|revenue|ebitda|نتائج|أرباح|الأرباح|ايرادات|إيرادات',t,re.I):category='Earnings'
    elif re.search(r'merger|acquisition|stake|tower sale|استحواذ|اندماج|حصة|حصص',t,re.I):category='M&A'
    elif re.search(r'regulat|license|spectrum|ضريب|تنظيم|ترخيص',t,re.I):category='Regulation'
    elif re.search(r'artificial intelligence|\bAI\b|cloud|digital|strategy|strategic|ذكاء|سحاب|استراتيج|رقمي',t,re.I):category='Strategy & AI'
    elif re.search(r'5g|6g|fiber|fibre|data cent|submarine|tower|شبك|أبراج|كابل',t,re.I):category='Infrastructure'
    elif re.search(r'dividend|توزيع',t,re.I):category='Dividends'
    else:category='Industry News'
    return (ids[0] if ids else None),category

def canonical_url(url):
    p=urlsplit(url)
    query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')]
    return urlunsplit((p.scheme,p.netloc.lower(),p.path.rstrip('/'),urlencode(query),''))

class NewsLinks(HTMLParser):
    def __init__(self):
        super().__init__();self.href=None;self.parts=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.href=dict(attrs).get('href');self.parts=[]
    def handle_data(self,text):
        if self.href:self.parts.append(text)
    def handle_endtag(self,tag):
        if tag=='a' and self.href:
            self.links.append((self.href,' '.join(' '.join(self.parts).split())))
            self.href=None;self.parts=[]

def parse_newsroom(data,feed):
    html=data.decode('utf-8',errors='replace')
    if feed.get('adapter')=='eand':
        out=[]
        for block in re.split(r'<div[^>]*class=["\'][^"\']*f-news-room[^"\']*["\']',html)[1:]:
            title=re.search(r'<h2[^>]*>(.*?)</h2>',block,re.S)
            date=re.search(r'class=["\']annoucement-date["\'][^>]*>(.*?)</span>',block,re.S)
            href=re.search(r'<a[^>]*href=["\']([^"\']+/news/[^"\']+)["\']',block)
            if not (title and href):continue
            url=urljoin(feed['url'],unescape(href[1]))
            if urlparse(url).hostname not in feed['allowed_hosts']:continue
            published=None
            if date:
                try:published=dt.datetime.strptime(date[1].strip(),'%d %b %Y').replace(tzinfo=dt.timezone.utc).isoformat()
                except ValueError:pass
            out.append({'title':unescape(re.sub('<[^>]+>','',title[1])).strip(),'url':url,'published':published,'summary':'','publisher':feed['label']})
        if not out:raise ValueError('Official newsroom markup changed')
        return out[:80]
    parser=NewsLinks();parser.feed(html)
    items={}
    for href,title in parser.links:
        url=urljoin(feed['url'],href);p=urlparse(url)
        if p.scheme!='https' or p.hostname not in feed['allowed_hosts']:continue
        if not re.search(feed['article_pattern'],p.path) or len(title)<35:continue
        title=re.sub(r'(?i)\s*(read more|learn more|المزيد|اقرأ المزيد)\s*$','',title).strip()
        if len(title)<35:continue
        # Listing dates are not inferred from retrieval time; no article body is copied.
        items[canonical_url(url)]={'title':title[:320],'url':url,'summary':'','published':None,'publisher':feed['label']}
    if not items:raise ValueError('No article links found; newsroom structure needs review')
    return list(items.values())[:60]

def update_feed(con, feed, fetcher=None):
    """Read public RSS or configured company newsroom links without access-control bypass."""
    fid=feed['id'];label=feed['label'];url=feed['url'];now=utcnow()
    domain=urlparse(url)
    if domain.scheme!='https' or not domain.hostname:raise ValueError('Only HTTPS feed URLs permitted')
    con.execute('INSERT OR IGNORE INTO feed_health(feed_id,label,url,enabled) VALUES(?,?,?,?)',(fid,label,url,int(feed.get('enabled',True))))
    con.execute('UPDATE feed_health SET label=?,url=?,enabled=?,last_checked=? WHERE feed_id=?',(label,url,int(feed.get('enabled',True)),now,fid))
    if not feed.get('enabled',True):con.commit();return 0
    state=con.execute('SELECT * FROM feed_health WHERE feed_id=?',(fid,)).fetchone()
    headers={'User-Agent':USER_AGENT,'Accept':'text/html' if feed.get('format')=='html' else 'application/rss+xml, application/atom+xml, application/xml, text/xml'}
    if state['etag']:headers['If-None-Match']=state['etag']
    if state['last_modified']:headers['If-Modified-Since']=state['last_modified']
    con.commit() # Release SQLite's write lock before network I/O.
    try:
        if fetcher:
            response=fetcher(url,headers)
            status=response.get('status',200);data=response.get('data',b'');hdr=response.get('headers',{})
        else:
            with urlopen(Request(url,headers=headers),timeout=12) as r:
                status=r.status;data=r.read(MAX_RESPONSE+1);hdr=dict(r.headers.items())
                if urlparse(r.url).scheme!='https':raise ValueError('Unsafe redirect')
        if status==304:
            con.execute('UPDATE feed_health SET last_success=?,last_error=NULL,last_http_status=304 WHERE feed_id=?',(now,fid));con.commit();return 0
        if status!=200:raise ValueError('Feed HTTP '+str(status))
        if len(data)>MAX_RESPONSE:raise ValueError('Feed response too large')
        items=parse_newsroom(data,feed) if feed.get('format')=='html' else parse_feed(data)
        count=0
        for item in items:
            company,category=categorize(item['title'])
            ids=companies_in(item['title'])
            if feed.get('kind')=='aggregator' and not ids:continue
            if feed.get('company_id') and feed['company_id'] not in ids:ids.append(feed['company_id'])
            company=company or feed.get('company_id')
            digest=hashlib.sha256(canonical_url(item['url']).encode()).hexdigest()[:32]
            cur=con.execute('INSERT OR IGNORE INTO feed_items(id,feed_id,title,url,published,discovered,company_id,category,summary,kind,company_ids,publisher) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (digest,fid,item['title'],item['url'],item['published'],now,company,category,item['summary'],feed.get('kind','secondary'),json.dumps(ids),item.get('publisher','')))
            count+=cur.rowcount
        con.execute('UPDATE feed_health SET last_success=?,last_error=NULL,last_http_status=200,received_count=received_count+?,etag=?,last_modified=? WHERE feed_id=?',
            (now,count,hdr.get('ETag') or hdr.get('etag') or state['etag'],hdr.get('Last-Modified') or hdr.get('last-modified') or state['last_modified'],fid))
        con.commit();return count
    except HTTPError as exc:
        if exc.code==304:
            con.execute('UPDATE feed_health SET last_success=?,last_error=NULL,last_http_status=304 WHERE feed_id=?',(now,fid));con.commit();return 0
        err=f'HTTP {exc.code}'
    except Exception as exc:err=(type(exc).__name__+': '+str(exc))[:300]
    con.execute('UPDATE feed_health SET last_error=?,last_http_status=NULL WHERE feed_id=?',(err,fid));con.commit();return 0


def refresh(fetcher=None):
    feeds=json.loads(FEEDS_FILE.read_text(encoding='utf-8'))['feeds']
    def one(feed):
        with connect() as con:return feed['id'],update_feed(con,feed,fetcher)
    with connect():pass # Complete schema migrations before concurrent connections.
    with ThreadPoolExecutor(max_workers=5) as pool:return dict(pool.map(one,feeds))


def worker_loop(stop_event=None):
    while True:
        refresh()
        if stop_event:
            if stop_event.wait(INTERVAL):break
        else:time.sleep(INTERVAL)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--once',action='store_true',help='Run one refresh then stop');p.add_argument('--loop',action='store_true',help='Run every FEED_POLL_SECONDS')
    args=p.parse_args()
    if args.loop:worker_loop()
    else:print(json.dumps(refresh(),ensure_ascii=False,indent=2))
