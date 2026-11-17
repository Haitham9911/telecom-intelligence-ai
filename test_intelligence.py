import json,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import updater

class IntelligenceTests(unittest.TestCase):
 def test_joint_news_matches_both_groups(self):
  self.assertEqual(updater.companies_in('Zain and Ooredoo launch regional tower company'),['ZAIN','ORDS'])
 def test_oman_operator_not_group_and_eand_ampersand(self):
  self.assertEqual(updater.companies_in('Ooredoo Oman results'),['ORED'])
  self.assertIn('EAND',updater.companies_in('e& reports financial results'))
 def test_global_news_tagging(self):
  self.assertEqual(updater.companies_in('Verizon and T-Mobile announce agreement'),['VZ','TMUS'])
  self.assertIn('TEF',updater.companies_in('Telefónica results'))
  self.assertIn('DTE',updater.companies_in('Deutsche Telekom raises guidance'))
 def test_canonical_url_removes_tracking_not_article_identity(self):
  self.assertEqual(updater.canonical_url('https://EXAMPLE.com/story/?id=4&utm_source=rss#x'),'https://example.com/story?id=4')
 def test_same_article_two_feeds_stored_once(self):
  with tempfile.TemporaryDirectory() as d,patch.object(updater,'DB',Path(d)/'cache.db'):
   with updater.connect() as con:
    rss=b'<rss><channel><item><title>Zain and Ooredoo agreement</title><link>https://example.com/story</link></item></channel></rss>'
    fetch=lambda *_:{'data':rss,'status':200}
    for fid in ('one','two'):updater.update_feed(con,{'id':fid,'label':fid,'url':'https://example.com/'+fid},fetch)
    self.assertEqual(con.execute('select count(*) from feed_items').fetchone()[0],1)
    self.assertEqual(json.loads(con.execute('select company_ids from feed_items').fetchone()[0]),['ZAIN','ORDS'])
 def test_newsroom_date_and_source_not_detection_time(self):
  html=b'<div class="loading-tile f-news-room"><h2>Official telecom result announcement</h2><span class="annoucement-date">12 Nov 2026</span><a href="/en/news/result.html">Load More</a></div>'
  items=updater.parse_newsroom(html,{'adapter':'eand','url':'https://www.eand.com/en/news/news-overview.html','allowed_hosts':['www.eand.com'],'label':'Official'})
  self.assertEqual(items[0]['published'][:10],'2026-11-12')
  self.assertEqual(items[0]['title'],'Official telecom result announcement')
 def test_bad_newsroom_markup_is_failure_not_empty_success(self):
  with self.assertRaises(ValueError):updater.parse_newsroom(b'<html>maintenance</html>',{'adapter':'eand','allowed_hosts':['www.eand.com']})
 def test_five_years_have_sources_and_reporting_breaks(self):
  data=json.loads((Path(__file__).parent/'data/seed.json').read_text())['intelligence']
  for p in data['profiles']:
   self.assertEqual([x['year'] for x in p['annual']],[2021,2022,2023,2024,2025])
   self.assertEqual(p['latest']['period'],'9M 2026')
   for a in p['annual']:
    self.assertTrue(a['source_url'].startswith('https://'))
    self.assertGreater(a['revenue'],0)
  p=next(p for p in data['profiles'] if p['id']=='ORDS')
  self.assertFalse(p['annual'][1]['comparable_previous'])

if __name__=='__main__':unittest.main()
