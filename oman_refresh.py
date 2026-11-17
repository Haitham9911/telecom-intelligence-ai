"""Daily validation and snapshotting of TRA Oman's public structured tables."""
import calendar,csv,datetime as dt,json,math,urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
INTERVAL=86400
SOURCES={
 'bbs-technology':(['السنة','الربع','اشتراكات تقنية الألياف البصرية','اشتراكات تقنية الخط المشترك الرقمي (ADSL)','اشتراكات تقنية الجيل الرابع الثابت','اشتراكات تقنية الجيل الخامس الثابت','الاشتراكات الساتلية','الاشتراكات الأخرى','إجمالي الاشتراكات النشطة'],['fiber','adsl','fixed_4g','fixed_5g','satellite','fixed_other','fixed_broadband']),
 'mobile-subscriptions':(['السنة','الربع','اشتراكات الهاتف المتنقل','نسبة انتشار الهاتف المتنقل من إجمالي عدد السكان','اشتراكات الهاتف المتنقل مسبق الدفع','اشتراكات الهاتف المتنقل آجل الدفع','اشتراكات النطاق العريض المتنقل','نسبة انتشار النطاق العريض المتنقل من إجمالي عدد السكان','الاشتراكات في الشبكات المتنقلة للاتصالات من آلة إلى آلة'],['mobile','mobile_penetration','prepaid','postpaid','mobile_broadband','mbb_penetration','m2m']),
 'fixed-subscriptions':(['السنة','الربع','اشتراكات خدمة الصوت الثابتة','نسبة انتشار خدمات الهاتف الثابت لكل 100 أسرة','اشتراكات النطاق العريض الثابت','نسب انتشار خدمات النطاق العريض الثابت لكل 100 أسرة','اشتراكات النطاق العريض الثابت (سكني)','اشتراكات النطاق العريض الثابت (تجاري)'],['fixed_voice','voice_household_penetration','fixed_broadband','fbb_household_penetration','fbb_residential','fbb_business']),
 'revenue':(['السنة','الربع','الإيرادات من خدمات الهاتف المتنقل (بالريال العماني)','متوسط الإيرادات من خدمات الهاتف المتنقل لكل اشتراك (بالريال العماني)','الإيرادات من خدمات النطاق العريض المتنقل (بالريال العماني)','متوسط الإيرادات من خدمات النطاق العريض المتنقل لكل اشتراك (بالريال العماني)','الإيرادات من خدمات الهاتف الثابت (بالريال العماني)','متوسط الإيرادات من خدمات الهاتف الثابت لكل اشتراك (بالريال العماني)','الإيرادات من خدمات النطاق العريض الثابت (بالريال العماني)','متوسط الإيرادات من خدمات النطاق العريض الثابت لكل اشتراك (بالريال العماني)'],['mobile_voice_revenue','mobile_voice_arpu','mbb_revenue','mbb_arpu','fixed_voice_revenue','fixed_voice_arpu','fbb_revenue','fbb_arpu']),
 'investment':(['السنة','الاستثمارات في خدمات الاتصالات الثابتة (بالريال العماني)','الاستثمارات في خدمات الاتصالات المتنقلة (بالريال العماني)','الاستثمارات في مجالات اخرى متعلقة بالاتصالات (بالريال العماني)','إجمالي الاستثمارات في قطاع الاتصالات (بالريال العماني)'],['fixed_investment','mobile_investment','other_investment','sector_investment'])}
def now():return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
def read(path,default):
 try:return json.loads(Path(path).read_text())
 except (OSError,ValueError):return default
class Tables(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=='table':self.table=[]
  elif tag=='tr' and self.table is not None:self.row=[]
  elif tag in ('td','th') and self.row is not None:self.cell=[]
 def handle_data(self,s):
  if self.cell is not None:self.cell.append(s)
 def handle_endtag(self,tag):
  if tag in ('td','th') and self.cell is not None:self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
  elif tag=='tr' and self.row is not None:self.table.append(self.row);self.row=None
  elif tag=='table' and self.table is not None:self.tables.append(self.table);self.table=None
def extract(html,source_id,today=None):
 p=Tables();p.feed(html);headers,metrics=SOURCES[source_id]
 matches=[r for r in p.tables if r and r[0]==headers]
 if len(matches)!=1:raise ValueError('TRA table structure changed or unavailable')
 today=today or dt.date.today();out=[];seen=set();annual=source_id=='investment'
 for cells in matches[0][1:]:
  if len(cells)!=len(headers):raise ValueError('Column count mismatch')
  y=int(cells[0]);q=4 if annual else int(cells[1]);offset=1 if annual else 2
  if not 1<=q<=4:raise ValueError('Invalid quarter')
  end=dt.date(y,q*3,calendar.monthrange(y,q*3)[1])
  if y<2021 or end>today:continue
  if end in seen:raise ValueError('Duplicate period')
  seen.add(end);values=[float(x.replace(',','')) for x in cells[offset:]]
  if any(not math.isfinite(v) or v<0 for v in values):raise ValueError('Invalid number')
  vals=dict(zip(metrics,values))
  if source_id=='bbs-technology' and abs(sum(values[:-1])-values[-1])>2:raise ValueError('Technology total does not reconcile')
  if source_id=='mobile-subscriptions' and abs(vals['prepaid']+vals['postpaid']-vals['mobile'])>1:raise ValueError('Mobile total does not reconcile')
  if source_id=='fixed-subscriptions' and abs(vals['fbb_residential']+vals['fbb_business']-vals['fixed_broadband'])>1:raise ValueError('Fixed total does not reconcile')
  if source_id=='investment' and abs(sum(values[:-1])-values[-1])>2:raise ValueError('Investment total does not reconcile')
  for metric,v in vals.items():
   unit='percent' if 'penetration' in metric else 'OMR_per_month' if metric.endswith('arpu') else 'OMR' if metric.endswith(('revenue','investment')) else 'subscriptions'
   if unit=='subscriptions' and not v.is_integer():raise ValueError('Fractional subscription count')
   out.append(dict(metric=metric,value=v,unit=unit,period_end=end.isoformat(),period_kind='annual' if annual else 'quarter',source_id='TRA',source_url='https://tra.gov.om/open-data/'+source_id,dataset=source_id,method='reported'))
 if not out:raise ValueError('No valid rows')
 return out
def refresh(data_dir,fetcher=None,force=False):
 data_dir=Path(data_dir);data_dir.mkdir(exist_ok=True);path=data_dir/'oman-auto.json';cache=read(path,{'schema':1,'sources':{},'records':[]});stamp=now()
 def run(source_id):
  state=cache['sources'].get(source_id,{})
  if not force and state.get('last_checked') and (dt.datetime.fromisoformat(stamp)-dt.datetime.fromisoformat(state['last_checked'])).total_seconds()<INTERVAL:return source_id,None,None
  url='https://tra.gov.om/open-data/'+source_id
  try:
   if fetcher:html=fetcher(url)
   else:
    req=urllib.request.Request(url,headers={'User-Agent':'TelecomIntelligenceAI/1.0 (+https://github.com/Haitham9911/telecom-intelligence-ai)'})
    with urllib.request.urlopen(req,timeout=25) as r:html=r.read(5_000_000).decode('utf-8')
   return source_id,extract(html,source_id),None
  except Exception as exc:return source_id,None,(type(exc).__name__+': '+str(exc))[:180]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for source_id,rows,error in pool.map(run,SOURCES):
   if rows is None and error is None:continue
   state=cache['sources'].setdefault(source_id,{});state.update(last_checked=stamp,last_error=error)
   if rows:
    prior={(r['metric'],r['period_end']):r for r in cache['records'] if r.get('dataset')==source_id}
    prior.update({(r['metric'],r['period_end']):r for r in rows})
    cache['records']=[r for r in cache['records'] if r.get('dataset')!=source_id]+list(prior.values())
    state.update(last_success=stamp,latest_period_end=max(r['period_end'] for r in rows))
 path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n');return cache
def combined(data_dir):
 data_dir=Path(data_dir);data=read(data_dir/'oman-market.json',{'schema':1,'national':[],'shares':[]});auto=read(data_dir/'oman-auto.json',{'records':[],'sources':{}})
 rows={}
 for r in data.get('national',[])+auto['records']:rows[(r['metric'],r['period_end'],r['source_id'])]=r
 # NCSI reports prepaid/postpaid and total including M2M. Derive telephone
 # subscriptions only within the exact same source vintage and reporting date.
 for key,r in list(rows.items()):
  if r['metric']!='prepaid':continue
  post=rows.get(('postpaid',r['period_end'],r['source_id']))
  mobile_key=('mobile',r['period_end'],r['source_id'])
  if post and mobile_key not in rows:
   rows[mobile_key]=dict(r,metric='mobile',value=r['value']+post['value'],method='calculated',formula='prepaid + postpaid; same source and date')
 data['national']=sorted(rows.values(),key=lambda r:(r['period_end'],r['metric'],r['source_id']));data['refresh']=auto['sources'];data['built_at']=now();return data
def export(data_dir):
 data_dir=Path(data_dir);data=combined(data_dir)
 (data_dir/'oman-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 with (data_dir/'oman-market.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,['metric','value','unit','period_end','period_kind','source_id','source_url','method'],extrasaction='ignore');w.writeheader();w.writerows(data['national'])
 return data
if __name__=='__main__':
 d=Path(__file__).resolve().parent/'data';c=refresh(d);export(d);print(json.dumps(c['sources'],indent=2))
