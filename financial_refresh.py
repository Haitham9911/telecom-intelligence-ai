"""Refresh selected SEC balance-sheet facts; keep reviewed telecom KPIs separate."""
import csv,datetime as dt,json,math,os,re,time
from pathlib import Path
from urllib.request import Request,urlopen
COMPANIES={'VZ':732712,'TMUS':1283699}
USER_AGENT='TelecomIntelligenceAI/1.0 (+https://github.com/Haitham9911/telecom-intelligence-ai/issues)'
INTERVAL=21600
TAGS={
 'assets':'Assets','cash':'CashAndCashEquivalentsAtCarryingValue',
 'total_equity':'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
 'parent_equity':'StockholdersEquity','current_assets':'AssetsCurrent',
 'current_liabilities':'LiabilitiesCurrent','total_liabilities':'Liabilities',
 'long_term_debt':'LongTermDebt',
 'debt_including_finance_leases':'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities'}
def now():return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
def read(path,default):
 try:return json.loads(path.read_text())
 except (OSError,ValueError):return default

def extract(payload,cid,today=None):
 today=today or dt.date.today();cik=COMPANIES[cid]
 if int(payload.get('cik',0))!=cik:raise ValueError('Company identifier mismatch')
 facts=payload.get('facts',{}).get('us-gaap',{});records=[]
 for metric,tag in TAGS.items():
  concept=facts.get(tag,{})
  by_end={}
  for x in concept.get('units',{}).get('USD',[]):
   if x.get('start') or x.get('form') not in ('10-K','10-K/A','10-Q','10-Q/A'):continue
   try:
    end=dt.date.fromisoformat(x['end']);filed=dt.date.fromisoformat(x['filed']);value=float(x['val']);accn=x['accn']
   except (KeyError,TypeError,ValueError):continue
   if isinstance(x['val'],bool) or not isinstance(x['val'],(int,float)) or filed<end or not math.isfinite(value) or end>today or filed>today or end.year<max(2021,today.year-6) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accn):continue
   if metric!='parent_equity' and value<0:continue
   # Instant facts only. Calendar year-end is distinct from an interim balance.
   prior=by_end.get(x['end'])
   if prior is None or (x['filed'],accn)>(prior['filed'],prior['accn']):by_end[x['end']]=x
  for end,x in by_end.items():
   source=f'https://www.sec.gov/Archives/edgar/data/{cik}/{x["accn"].replace("-","")}/{x["accn"]}-index.htm'
   records.append({'company_id':cid,'metric':metric,'year':int(end[:4]),'period_end':end,'period_type':'annual' if end.endswith('-12-31') else 'interim','value':x['val']/1000000,'unit':'million_currency','currency':'USD','label_en':concept.get('label',tag),'basis_en':concept.get('description',tag)+' Latest filed comparative for this balance date; may be restated.','scope_en':'Consolidated filing entity','scope_ar':'الكيان الموحد في الإفصاح','source_url':source,'source_api':f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json','source_page':tag,'filed_at':x['filed'],'method':'sec-xbrl','accession':x['accn'],'reviewed_at':now()})
 if not any(r['metric']=='assets' for r in records) or not any(r['metric']=='cash' for r in records):raise ValueError('Required balance-sheet facts missing')
 return records

def refresh(data_dir,fetcher=None,force=False):
 path=Path(data_dir)/'financial-auto.json';cache=read(path,{'schema':1,'records':[],'companies':{}});stamp=now()
 for cid,cik in COMPANIES.items():
  state=cache.setdefault('companies',{}).setdefault(cid,{})
  try:elapsed=(dt.datetime.fromisoformat(stamp)-dt.datetime.fromisoformat(state['last_checked'])).total_seconds()
  except (ValueError,KeyError,TypeError):elapsed=INTERVAL+1
  if not force and elapsed<INTERVAL:continue
  state['last_checked']=stamp
  try:
   url=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json'
   if fetcher:payload=fetcher(cid,url)
   else:
    with urlopen(Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/json'}),timeout=25) as response:
     raw=response.read(25_000_001)
     if len(raw)>25_000_000:raise ValueError('Response too large')
     payload=json.loads(raw)
   rows=extract(payload,cid)
   # Retain known dates if a response temporarily omits a historic concept.
   keys={(r['company_id'],r['metric'],r['period_end']) for r in rows}
   cache['records']=[r for r in cache.get('records',[]) if (r['company_id'],r['metric'],r['period_end']) not in keys]+rows
   state.update(last_success=stamp,last_error=None,latest_period_end=max(r['period_end'] for r in rows),metric_count=len({r['metric'] for r in rows}))
  except Exception as exc:state['last_error']=(type(exc).__name__+': '+str(exc))[:180]
  if not fetcher:time.sleep(.2)
 path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n');return cache

def combined(data_dir):
 data_dir=Path(data_dir)
 reviewed=read(data_dir/'financial-indicators.json',{'schema':1,'records':[]})
 automatic=read(data_dir/'financial-auto.json',{'records':[],'companies':{}})
 records={}
 for row in reviewed.get('records',[])+automatic.get('records',[]):
  if row.get('value') is not None:records[(row['company_id'],row['metric'],row['period_end'])]=row
 return {'schema':1,'reviewed_at':reviewed.get('reviewed_at'),'built_at':now(),'refresh_interval_seconds':INTERVAL,'refresh':automatic.get('companies',{}),'notes':reviewed.get('notes',{}),'records':sorted(records.values(),key=lambda r:(r['company_id'],r['metric'],r['period_end']))}

def export(data_dir):
 data_dir=Path(data_dir);data=combined(data_dir)
 (data_dir/'indicator-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 fields=['company_id','metric','period_start','period_end','period_type','value','unit','currency','label_en','scope_en','basis_en','source_url','source_page','source_vintage','source_unit','method','filed_at','reviewed_at']
 with (data_dir/'financial-indicators.csv').open('w',encoding='utf-8-sig',newline='') as fh:
  w=csv.DictWriter(fh,fields,extrasaction='ignore');w.writeheader();w.writerows(data['records'])
 return data
if __name__=='__main__':
 folder=Path(__file__).resolve().parent/'data';result=refresh(folder);export(folder)
 print(json.dumps(result['companies'],indent=2))
