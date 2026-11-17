import json,tempfile,unittest
from pathlib import Path
import oman_refresh as om
R=Path(__file__).resolve().parent
class OmanTests(unittest.TestCase):
 def html(self,vals):
  h=om.SOURCES['mobile-subscriptions'][0];return '<table><tr>'+''.join('<th>'+s+'</th>' for s in h)+'</tr><tr>'+''.join('<td>'+str(s)+'</td>' for s in vals)+'</tr></table>'
 def test_mobile_table_dates_scope_and_total(self):
  r=om.extract(self.html([2026,2,6619238,123.87,5305401,1313837,5534086,103.56,1705168]),'mobile-subscriptions')
  self.assertEqual(r[0]['period_end'],'2026-06-30');self.assertEqual(r[0]['value'],6619238);self.assertEqual(r[-1]['value'],1705168);self.assertEqual(r[1]['unit'],'percent')
 def test_bad_structure_and_inconsistent_counts_rejected(self):
  for html in ['<p>unavailable</p>',self.html([2026,2,6619239,123.87,5305401,1313830,5534086,103.56,1705168]),self.html([2026,2,'NaN',123.87,5305401,1313837,5534086,103.56,1705168])]:
   with self.assertRaises(ValueError):om.extract(html,'mobile-subscriptions')
 def test_failed_refresh_retains_records_and_backoff(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);record={'metric':'mobile','value':100,'period_end':'2025-12-31','source_id':'TRA','dataset':'mobile-subscriptions'}
   (d/'oman-auto.json').write_text(json.dumps({'schema':1,'sources':{'mobile-subscriptions':{'last_success':'2026-11-01T00:00:00+00:00'}},'records':[record]}))
   calls=[]
   def broken(url):calls.append(url);raise OSError('offline')
   c=om.refresh(d,fetcher=broken);self.assertEqual(c['records'],[record]);self.assertEqual(c['sources']['mobile-subscriptions']['last_success'],'2026-11-01T00:00:00+00:00')
   om.refresh(d,fetcher=broken);self.assertEqual(len(calls),5)
 def test_published_records_and_shares_have_sources(self):
  d=json.loads((R/'data/oman-market.json').read_text())
  for r in d['national']:self.assertTrue(r['source_url'].startswith('https://'));self.assertGreaterEqual(r['value'],0)
  for s in d['shares']:
   self.assertAlmostEqual(sum(r['share'] for r in s['operators']),100);self.assertEqual(s['period_end'],s['id'].split('-',1)[1] if s['id'].startswith('mobile-') else s['id'].split('-',1)[1])
   self.assertGreater(s['total'],0)
 def test_ooredoo_mobile_excludes_fixed(self):
  o=json.loads((R/'data/oman-market.json').read_text())['ooredoo']
  for r in o['ooredoo_oman_annual']+o['ooredoo_oman_quarters']:
   self.assertEqual(r['postpaid']+r['prepaid'],r['mobile_customers']);self.assertEqual(r['mobile_customers']+r['fixed_line'],r['total_customers'])
if __name__=='__main__':unittest.main()
