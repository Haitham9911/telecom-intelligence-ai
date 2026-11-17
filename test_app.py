import unittest, json, sqlite3, tempfile
from pathlib import Path
from server import initialize, rows, SEED
class DataTests(unittest.TestCase):
 def test_zain_source_on_all_facts(self):
  self.assertTrue(all(f['source_id']=='zain-2026' for f in SEED['facts']))
 def test_no_peer_values_in_seed(self):
  self.assertEqual({f['company_id'] for f in SEED['facts']},{'ZAIN'})
 def test_reported_margin_not_from_rounded_revenue(self):
  f={(v['period'],v['metric']):v['value'] for v in SEED['facts']}
  self.assertEqual(f[('9M 2026','ebitda_margin')],34)
 def test_sources_known(self):
  self.assertEqual({x['id'] for x in SEED['sources'] if x['mode']=='verified-seed'},{'zain-2026'})
if __name__=='__main__':unittest.main()
