"""Offline integration tests for RSS/Atom parser, deduplication and endpoint."""
import unittest, tempfile, sqlite3, json, io
from pathlib import Path
from unittest.mock import patch
import updater

RSS=b'''<?xml version="1.0"?><rss version="2.0"><channel><title>Test</title>
<item><title>Zain Group reports EBITDA increase</title><link>https://example.com/news/1</link><pubDate>Mon, 16 Nov 2026 12:00:00 GMT</pubDate><description>Publicly reported results</description></item>
<item><title>Omantel tower agreement</title><link>https://example.com/news/2</link></item>
</channel></rss>'''
ATOM=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>stc new 5G network</title><link href="https://example.com/story"/><updated>2026-11-17T08:00:00Z</updated></entry></feed>'''

class LiveTests(unittest.TestCase):
 def test_parse_rss(self):
  rows=updater.parse_feed(RSS);self.assertEqual(len(rows),2);self.assertEqual(rows[0]['published'][:10],'2026-11-16')
 def test_atom(self):
  self.assertEqual(updater.parse_feed(ATOM)[0]['url'],'https://example.com/story')
 def test_category(self):
  self.assertEqual(updater.categorize('Zain Group EBITDA results'),('ZAIN','Earnings'))
 def test_dedupe_and_304(self):
  with tempfile.TemporaryDirectory() as directory:
   with patch.object(updater,'DB',Path(directory)/'test.sqlite3'):
    feed={'id':'test','url':'https://example.com/rss','label':'Test News','kind':'industry','enabled':True}
    con=updater.connect()
    def get(*_):return {'status':200,'data':RSS,'headers':{'ETag':'v1'}}
    self.assertEqual(updater.update_feed(con,feed,get),2)
    self.assertEqual(updater.update_feed(con,feed,get),0)
    self.assertEqual(updater.update_feed(con,feed,lambda *_:{'status':304}),0)
    self.assertEqual(con.execute('select count(*) from feed_items').fetchone()[0],2)
    self.assertEqual(con.execute('select etag from feed_health').fetchone()[0],'v1')
    con.close()
 def test_reject_insecure_article(self):
  bad=b'<rss><channel><item><title>Bad</title><link>http://example.com</link></item></channel></rss>'
  self.assertEqual(updater.parse_feed(bad),[])

if __name__=='__main__':unittest.main()
