import copy,datetime as dt,json,tempfile,unittest
from pathlib import Path
import financial_refresh as f
TODAY=dt.date(2026,11,17)
def fixture():
 row={'end':'2025-12-31','val':100000000,'accn':'0000732712-26-000007','form':'10-K','filed':'2026-02-17','fy':2025}
 return {'cik':732712,'facts':{'us-gaap':{k:{'label':k,'description':'Definition','units':{'USD':[dict(row)]}} for k in ['Assets','CashAndCashEquivalentsAtCarryingValue']}}}
class FinancialRefreshTests(unittest.TestCase):
 def test_instant_reporting_date_and_unit_conversion(self):
  p=fixture();p['facts']['us-gaap']['Assets']['units']['USD'][0]['fy']=2026
  r=f.extract(p,'VZ',TODAY);self.assertEqual(r[0]['year'],2025);self.assertEqual(r[0]['value'],100);self.assertEqual(r[0]['period_type'],'annual')
 def test_duration_future_invalid_and_nonusd_are_excluded(self):
  p=fixture();rows=p['facts']['us-gaap']['Assets']['units']['USD'];base=rows[0]
  rows.extend([dict(base,start='2025-01-01'),dict(base,end='2027-12-31'),dict(base,val=True),dict(base,val=float('inf'))])
  p['facts']['us-gaap']['Assets']['units']['EUR']=[dict(base,val=900000000)]
  self.assertEqual(len(f.extract(p,'VZ',TODAY)),2)
 def test_wrong_company_is_rejected(self):
  with self.assertRaises(ValueError):f.extract(fixture(),'TMUS',TODAY)
 def test_later_filed_comparative_wins_without_changing_balance_date(self):
  p=fixture();r=p['facts']['us-gaap']['Assets']['units']['USD'];r.append(dict(r[0],filed='2026-10-29',val=120000000,accn='0000732712-26-000052',form='10-Q'))
  a=next(r for r in f.extract(p,'VZ',TODAY) if r['metric']=='assets');self.assertEqual(a['value'],120);self.assertEqual(a['period_end'],'2025-12-31')
 def test_failure_retains_last_success_and_previous_figures(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'financial-auto.json';p.write_text(json.dumps({'records':[{'company_id':'VZ','metric':'assets','period_end':'2025-12-31','value':100}],'companies':{'VZ':{'last_success':'2026-01-01T00:00:00+00:00'}}}))
   def failure(*args):raise ValueError('unavailable')
   r=f.refresh(d,fetcher=failure,force=True);self.assertEqual(r['records'][0]['value'],100);self.assertEqual(r['companies']['VZ']['last_success'],'2026-01-01T00:00:00+00:00');self.assertIn('unavailable',r['companies']['VZ']['last_error'])
 def test_six_hour_backoff_limits_requests(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'financial-auto.json').write_text(json.dumps({'records':[],'companies':{c:{'last_checked':f.now()} for c in f.COMPANIES}}))
   calls=[];f.refresh(d,fetcher=lambda *a:calls.append(a));self.assertEqual(calls,[])
 def test_auto_overlay_does_not_replace_company_defined_debt(self):
  with tempfile.TemporaryDirectory() as d:
   row={'company_id':'VZ','metric':'net_unsecured_debt','period_end':'2025-12-31','value':100}
   Path(d,'financial-indicators.json').write_text(json.dumps({'records':[row]}));Path(d,'financial-auto.json').write_text(json.dumps({'records':[dict(row,metric='cash',value=5)]}))
   self.assertEqual(len(f.combined(d)['records']),2)
 def test_reviewed_records_have_traceable_currency_scope_and_date(self):
  data=json.loads((Path(__file__).parent/'data/financial-indicators.json').read_text());keys=[]
  for r in data['records']:
   self.assertTrue(r['source_url'].startswith('https://'));self.assertTrue(r['scope_en']);self.assertTrue(r['basis_en']);self.assertEqual(r['year'],int(r['period_end'][:4]));keys.append((r['company_id'],r['metric'],r['period_end']))
   if r['unit']=='million_currency':self.assertIn(r['currency'],('OMR','KWD','QAR','SAR','AED','EUR','USD'))
  self.assertEqual(len(keys),len(set(keys)))
if __name__=='__main__':unittest.main()
