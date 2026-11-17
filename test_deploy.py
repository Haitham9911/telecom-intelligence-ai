import json, tempfile, shutil, unittest
from pathlib import Path
from unittest.mock import patch
import build_static
class DeployTests(unittest.TestCase):
 def test_static_build_no_secrets(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);(base/'data').mkdir()
   for name in ('index.html','styles.css','app.js','research.js','stocks.js','intelligence.js','indicators.js','oman.js','icon.svg'):
    shutil.copy2(build_static.R/name,base/name)
   (base/'data'/'seed.json').write_text((build_static.R/'data'/'seed.json').read_text())
   with patch.object(build_static,'R',base),patch.object(build_static,'SITE',base/'_site'),patch.object(build_static,'DATA',base/'data'),patch.object(build_static.updater,'DB',base/'data'/'cache.sqlite3'):
    build_static.build(refresh=False)
   site=base/'_site'
   html=(site/'index.html').read_text()
   self.assertIn('const IS_STATIC=true',html)
   self.assertIn('data/live-news.json',(site/'app.js').read_text())
   self.assertIn('data/facts.csv',(site/'app.js').read_text())
   for name in ('styles.css','app.js','research.js','stocks.js','intelligence.js','indicators.js','oman.js','icon.svg'):
    self.assertTrue((site/name).is_file())
   self.assertTrue((site/'data'/'stock-quotes.json').is_file())
   self.assertTrue((site/'data'/'indicator-data.json').is_file())
   self.assertTrue((site/'data'/'oman-data.json').is_file())
   self.assertTrue((site/'data'/'oman-market.csv').is_file())
   self.assertTrue((site/'data'/'financial-indicators.csv').is_file())
   self.assertFalse((site/'quotes.py').exists())
   self.assertFalse((site/'server.py').exists())
   self.assertFalse((site/'data'/'cache.sqlite3').exists())
   self.assertEqual(json.loads((site/'data'/'live-news.json').read_text()),[])
 def test_feed_history_survives_failed_refresh_and_disabled_feed_is_excluded(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);(base/'data').mkdir()
   for name in ('index.html','styles.css','app.js','research.js','stocks.js','intelligence.js','indicators.js','oman.js','icon.svg'):
    shutil.copy2(build_static.R/name,base/name)
   (base/'data'/'seed.json').write_text((build_static.R/'data'/'seed.json').read_text())
   prior=[{'id':'retained-story','title':'Previous headline','url':'https://example.com/retained','company_ids':[],'published':'2026-11-17T08:00:00+00:00'}]
   (base/'data'/'live-news.json').write_text(json.dumps(prior))
   with patch.object(build_static,'R',base),patch.object(build_static,'SITE',base/'_site'),patch.object(build_static,'DATA',base/'data'),patch.object(build_static.updater,'DB',base/'data'/'cache.sqlite3'):
    with build_static.updater.connect() as db:
     db.execute("INSERT INTO feed_health(feed_id,label,url,enabled,last_error) VALUES('disabled','Disabled','https://example.com/rss',0,'old error')")
     db.execute("INSERT INTO feed_health(feed_id,label,url,enabled,last_success,last_checked,last_error) VALUES('active','Active','https://example.com/rss',1,'2026-11-17T08:00:00+00:00','2026-11-17T09:00:00+00:00','temporary outage')")
    build_static.build(refresh=False)
   self.assertEqual(json.loads((base/'_site/data/live-news.json').read_text()),prior)
   status=json.loads((base/'_site/data/live-status.json').read_text())
   self.assertEqual(status['feeds_failed'],1)
   self.assertEqual(status['feeds_disabled'],1)
   self.assertEqual(status['last_success'],'2026-11-17T08:00:00+00:00')
if __name__=='__main__':unittest.main()
