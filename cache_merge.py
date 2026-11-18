"""Preserve newer reviewed source snapshots across GitHub cache restoration."""
import argparse,json,shutil
from pathlib import Path
CONFIG={'financial-auto.json':('companies','company_id'),'oman-auto.json':('sources','dataset')}
def merge(committed,cached,state_key,group_key):
 result={**cached,**committed};result[state_key]={};records={}
 for group in set(committed.get(state_key,{}))|set(cached.get(state_key,{})):
  a=committed.get(state_key,{}).get(group,{});b=cached.get(state_key,{}).get(group,{})
  # Latest attempt determines error/backoff, latest success determines values.
  state=dict(max([a,b],key=lambda s:s.get('last_checked') or ''))
  success=max([a,b],key=lambda s:s.get('last_success') or '')
  for k in ('last_success','latest_period_end','metric_count'):
   if k in success:state[k]=success[k]
  result[state_key][group]=state
  older,newer=(cached,committed) if (a.get('last_success') or '')>=(b.get('last_success') or '') else (committed,cached)
  for source in (older,newer):
   for row in source.get('records',[]):
    if row.get(group_key)==group:records[(group,row['metric'],row['period_end'])]=row
 result['records']=sorted(records.values(),key=lambda r:(r.get(group_key,''),r['metric'],r['period_end']))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['snapshot','merge']);p.add_argument('backup');a=p.parse_args();backup=Path(a.backup);backup.mkdir(parents=True,exist_ok=True)
 for name,(state,group) in CONFIG.items():
  path=Path('data')/name;saved=backup/name
  if a.mode=='snapshot':
   if path.exists():shutil.copy2(path,saved)
  elif saved.exists():
   original=json.loads(saved.read_text());cached=json.loads(path.read_text()) if path.exists() else {}
   path.write_text(json.dumps(merge(original,cached,state,group),ensure_ascii=False,indent=2)+'\n')
