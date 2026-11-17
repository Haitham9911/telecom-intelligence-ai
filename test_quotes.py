import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import quotes
HTML=(Path(__file__).parent/'tests/fixtures/msx-quote.html').read_text()
class QuoteTests(unittest.TestCase):
 def test_price_currency_change_and_unknown_trade_time(self):
  q=quotes.parse_msx(HTML,'OTEL')
  self.assertEqual(q['currency'],'OMR');self.assertEqual(q['price'],1.355)
  self.assertEqual(q['change'],-.005);self.assertEqual(q['change_percent'],-.37)
  self.assertEqual(q['volume'],7277488);self.assertIsNone(q['quote_time'])
 def test_wrong_security_rejected(self):
  with self.assertRaises(ValueError):quotes.parse_msx(HTML,'ORDS')
 def test_inconsistent_change_rejected(self):
  with self.assertRaises(ValueError):quotes.parse_msx(HTML.replace('-0.37%','5.0%'),'OTEL')
 def test_zero_or_nonfinite_price_rejected(self):
  for v in ('0.000','NaN','Infinity'):
   with self.assertRaises(ValueError):quotes.parse_msx(HTML.replace('>1.355<','>'+v+'<'),'OTEL')
 def test_missing_markup_does_not_publish_zero(self):
  with self.assertRaises(ValueError):quotes.parse_msx('<html>Service unavailable</html>','OTEL')
 def test_refresh_keeps_last_success_on_error(self):
  with tempfile.TemporaryDirectory() as d,patch.object(quotes,'SECURITIES',{'OTEL':'OTEL'}):
   initial=quotes.refresh(d,fetcher=lambda _:HTML,now='2026-11-17T12:00:00+00:00')
   def broken(_):raise TimeoutError('unavailable')
   failed=quotes.refresh(d,fetcher=broken,now='2026-11-17T13:00:00+00:00')['quotes'][0]
   self.assertEqual(failed['price'],1.355);self.assertEqual(failed['fetched_at'],initial['quotes'][0]['fetched_at'])
   self.assertEqual(failed['fetch_status'],'error');self.assertEqual(failed['last_attempt'],'2026-11-17T13:00:00+00:00')
 def test_initial_failure_is_missing_not_zero(self):
  with tempfile.TemporaryDirectory() as d,patch.object(quotes,'SECURITIES',{'OTEL':'OTEL'}):
   result=quotes.refresh(d,fetcher=lambda _:'Unavailable')['quotes'][0]
   self.assertIsNone(result['price']);self.assertIsNone(result['fetched_at'])
 def test_newer_cache_wins_over_committed_snapshot(self):
  with tempfile.TemporaryDirectory() as d,patch.object(quotes,'SECURITIES',{'OTEL':'OTEL'}):
   for name,date,price in [('stock-quotes.json','2026-11-16T12:00:00+00:00',1.36),('stock-quotes-cache.json','2026-11-17T12:00:00+00:00',1.355)]:
    (Path(d)/name).write_text(json.dumps({'quotes':[{'company_id':'OTEL','price':price,'fetched_at':date}]}))
   result=quotes.refresh(d,fetcher=lambda _:'Unavailable')['quotes'][0]
   self.assertEqual(result['price'],1.355);self.assertEqual(result['fetched_at'],'2026-11-17T12:00:00+00:00')
if __name__=='__main__':unittest.main()
