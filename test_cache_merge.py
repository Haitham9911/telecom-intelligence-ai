import unittest
from cache_merge import merge
class CacheTests(unittest.TestCase):
 def fixture(self,success,checked,value,error=None):
  return {'companies':{'VZ':{'last_success':success,'last_checked':checked,'last_error':error,'latest_period_end':'2026-09-30'}},'records':[{'company_id':'VZ','metric':'assets','period_end':'2026-09-30','value':value}]}
 def test_newer_review_survives_old_cache(self):
  r=merge(self.fixture('2026-11-18','2026-11-18',2),self.fixture('2026-11-17','2026-11-17',1),'companies','company_id');self.assertEqual(r['records'][0]['value'],2)
 def test_newer_cache_preserved(self):
  r=merge(self.fixture('2026-11-17','2026-11-17',1),self.fixture('2026-11-18','2026-11-18',2),'companies','company_id');self.assertEqual(r['records'][0]['value'],2)
 def test_later_failure_keeps_verified_values_and_reports_error(self):
  r=merge(self.fixture('2026-11-18','2026-11-18',2),self.fixture('2026-11-17','2026-11-19',1,'HTTP 403'),'companies','company_id');self.assertEqual(r['records'][0]['value'],2);self.assertEqual(r['companies']['VZ']['last_success'],'2026-11-18');self.assertEqual(r['companies']['VZ']['last_error'],'HTTP 403')
 def test_tra_datasets_do_not_collide(self):
  r={'sources':{'fixed-subscriptions':{},'bbs-technology':{}},'records':[{'dataset':d,'metric':'fixed_broadband','period_end':'2025-03-31','value':v} for d,v in [('fixed-subscriptions',585843),('bbs-technology',585853)]]}
  self.assertEqual(len(merge(r,{},'sources','dataset')['records']),2)
