import unittest
from server import SEED

class DataTests(unittest.TestCase):
 def facts(self,scope='consolidated',period='9M 2026'):
  return {f['metric']:f for f in SEED['facts'] if f['company_id']=='OTEL' and f['scope']==scope and f['period']==period}
 def test_omantel_latest_board_approved_values(self):
  f=self.facts()
  self.assertEqual(f['revenue']['value'],2579.806)
  self.assertEqual(f['attributable_profit']['previous_value'],55.697)
  self.assertAlmostEqual(f['net_income']['value'],f['attributable_profit']['value']+f['non_controlling_profit']['value'],places=3)
  self.assertEqual(f['net_income']['source_id'],'omantel-q3-2026')
 def test_excluding_zain_never_mixed_with_consolidated(self):
  f=self.facts('excluding_zain')
  self.assertEqual(f['revenue']['value'],535.19)
  self.assertEqual(f['ebitda']['growth_yoy'],-2.9)
  self.assertNotIn('net_income',f)
  self.assertEqual(f['normalized_profit']['value'],56.947)
  self.assertNotIn('normalized_profit',self.facts())
 def test_quarter_and_half_year_values_are_separate(self):
  self.assertEqual(self.facts(period='Q3 2026')['revenue']['value'],874.05)
  self.assertEqual(self.facts(period='H1 2026')['revenue']['value'],1705.756)
 def test_every_financial_fact_has_a_verified_source(self):
  verified={s['id'] for s in SEED['sources'] if s['mode']=='verified-seed'}
  for f in SEED['facts']: self.assertIn(f['source_id'],verified)
  self.assertEqual({f['company_id'] for f in SEED['facts']},{'OTEL','ZAIN'})
 def test_reported_margin_not_recomputed_from_rounded_revenue(self):
  zain=next(f for f in SEED['facts'] if f['company_id']=='ZAIN' and f['period']=='9M 2026' and f['metric']=='ebitda_margin')
  self.assertEqual(zain['value'],34)
  self.assertEqual(self.facts('excluding_zain')['ebitda_margin']['value'],23)
 def test_financial_fact_identity_includes_scope(self):
  keys=[(f['company_id'],f['scope'],f['period'],f['metric']) for f in SEED['facts']]
  self.assertEqual(len(keys),len(set(keys)))
 def test_reports_match_sources(self):
  sources={s['id']:s for s in SEED['sources']}
  self.assertGreaterEqual(len(SEED['reports']),29)
  for r in SEED['reports']:self.assertEqual(r['url_en'],sources[r['source_id']]['url'])

if __name__=='__main__':unittest.main()
