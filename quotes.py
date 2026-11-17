#!/usr/bin/env python3
"""Public, delayed MSX snapshots. Fetch time is never treated as trade time."""
import datetime as dt
import json
import math
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
SECURITIES={'OTEL':'OTEL','ORED':'ORDS'}
PREFIX='ctl00_ContentPlaceHolder1_'
FIELDS={'CompanySymbolLabel':'symbol','LTPLabel':'price','PrevCloseLabel':'previous_close','ChangeLabel':'reported_change'}
CLASSES={'company-high':'high','company-low':'low','company-volume':'volume'}

class QuoteHTML(HTMLParser):
    def __init__(self):
        super().__init__();self.active=[];self.values={}
    def handle_starttag(self,tag,attrs):
        if tag in {'br','hr','img','input','meta','link','source','wbr','area','base','embed','param','track','col'}:return
        for item in self.active:item['depth']+=1
        a=dict(attrs);key=FIELDS.get(a.get('id','').removeprefix(PREFIX))
        if not key:
            key=next((CLASSES[c] for c in a.get('class','').split() if c in CLASSES),None)
        if key and key not in self.values:self.active.append({'key':key,'depth':1,'parts':[]})
    def handle_data(self,text):
        for item in self.active:item['parts'].append(text)
    def handle_endtag(self,tag):
        for item in self.active:item['depth']-=1
        for item in self.active:
            if item['depth']==0:self.values.setdefault(item['key'],' '.join(''.join(item['parts']).split()))
        self.active=[x for x in self.active if x['depth']>0]

def number(text):
    value=Decimal(text.replace(',','').replace('−','-').strip())
    if not value.is_finite():raise ValueError('Non-finite quote')
    return value

def parse_msx(html,symbol):
    p=QuoteHTML();p.feed(html);v=p.values
    if v.get('symbol','').strip('() ')!=symbol:raise ValueError('Security identity did not match')
    price=number(v['price']);previous=number(v['previous_close'])
    if price<=0 or previous<=0:raise ValueError('Missing or invalid price')
    change=price-previous;percent=100*change/previous
    reported=re.search(r'([+\-−]?\d+(?:\.\d+)?)\s*%',v.get('reported_change',''))
    if not reported or abs(number(reported.group(1))-percent)>Decimal('0.02'):
        raise ValueError('Price and reported change did not reconcile')
    result={'symbol':symbol,'exchange':'MSX','currency':'OMR','price':float(price),'previous_close':float(previous),'change':float(change),'change_percent':float(round(percent,2)),'source_delay_minutes':15,'quote_time':None,'source':'Muscat Stock Exchange','source_url':'https://www.msx.om/snapshot.aspx?s='+symbol}
    for field in ('high','low','volume'):
        if v.get(field):
            n=number(v[field]);result[field]=int(n) if field=='volume' else float(n)
    if result.get('high',price)<price or result.get('low',price)>price:raise ValueError('Price outside published session range')
    return result

def download(url):
    req=urllib.request.Request(url,headers={'User-Agent':'TelecomIntelligence/1.0 (public delayed market snapshot)','Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=30) as response:
        if 'text/html' not in response.headers.get('Content-Type',''):raise ValueError('Expected HTML quote')
        raw=response.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('Oversized quote response')
        return raw.decode('utf-8')

def read(path):
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data,dict) and isinstance(data.get('quotes'),list) else {'quotes':[]}
    except (OSError,ValueError):return {'quotes':[]}

def refresh(data_dir=None,fetcher=download,now=None):
    data_dir=Path(data_dir) if data_dir is not None else DATA
    data_dir.mkdir(parents=True,exist_ok=True)
    checked=now or dt.datetime.now(dt.timezone.utc).isoformat()
    prior={}
    for filename in ('stock-quotes.json','stock-quotes-cache.json'):
        for q in read(data_dir/filename)['quotes']:
            if q.get('company_id') in SECURITIES and (q.get('fetched_at') or '')>(prior.get(q['company_id'],{}).get('fetched_at') or ''):prior[q['company_id']]=q
    def update(item):
        company,symbol=item
        try:
            quote=parse_msx(fetcher('https://www.msx.om/snapshot.aspx?s='+symbol),symbol)
            return dict(quote,company_id=company,fetched_at=checked,last_attempt=checked,fetch_status='ok')
        except Exception as exc:
            # A failed run never advances the last successful retrieval timestamp.
            quote=dict(prior.get(company,{'company_id':company,'symbol':symbol,'exchange':'MSX','currency':'OMR','source':'Muscat Stock Exchange','source_url':'https://www.msx.om/snapshot.aspx?s='+symbol,'price':None,'quote_time':None,'fetched_at':None,'source_delay_minutes':15}))
            quote.update(last_attempt=checked,fetch_status='error',error_type=type(exc).__name__)
            return quote
    with ThreadPoolExecutor(max_workers=2) as pool:quotes=list(pool.map(update,SECURITIES.items()))
    result={'schema':1,'checked_at':checked,'poll_interval_seconds':1800,'quotes':quotes}
    payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    for filename in ('stock-quotes.json','stock-quotes-cache.json'):(data_dir/filename).write_text(payload,encoding='utf-8')
    print('MSX quotes:',sum(q['fetch_status']=='ok' for q in quotes),'of',len(quotes),'retrieved')
    return result

if __name__=='__main__':refresh()
