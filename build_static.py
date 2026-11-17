#!/usr/bin/env python3
"""Build public static site. No company secrets, no external dependencies."""
import csv,datetime as dt,io,json,shutil,sqlite3
from pathlib import Path
import updater,quotes
R=Path(__file__).resolve().parent
SITE=R/'_site'; DATA=R/'data'

def build(refresh=True):
    DATA.mkdir(exist_ok=True)
    prior=[]
    cache=DATA/'live-news.json'
    if cache.exists():
        try:prior=json.loads(cache.read_text())
        except (ValueError, OSError):pass
    if refresh:
        updater.refresh()
        quotes.refresh(DATA)
    if not (DATA/'stock-quotes.json').exists():
        (DATA/'stock-quotes.json').write_text(json.dumps({'schema':1,'quotes':[]}))
    with updater.connect() as db:
        db.row_factory=sqlite3.Row
        recent=[dict(r) for r in db.execute('SELECT * FROM feed_items ORDER BY COALESCE(published,discovered) DESC LIMIT 150')]
        health=[dict(r) for r in db.execute('SELECT * FROM feed_health ORDER BY feed_id')]
    # Maintain historical stories despite GitHub Actions' temporary runners.
    uniq={x['id']:x for x in prior if x.get('id')}
    uniq.update({x['id']:x for x in recent})
    news=sorted(uniq.values(),key=lambda x:x.get('published') or x.get('discovered') or '',reverse=True)[:150]
    active_health=[x for x in health if x.get('enabled')]
    status={'mode':'scheduled-public-rss','worker_enabled':True,'poll_interval_seconds':1800,
      'last_success':max((x['last_success'] for x in active_health if x.get('last_success')),default=None),
      'last_checked':max((x['last_checked'] for x in active_health if x.get('last_checked')),default=None),
      'feeds_ok':sum(bool(x.get('last_success') and not x.get('last_error')) for x in active_health),
      'feeds_failed':sum(bool(x.get('last_error')) for x in active_health),
      'feeds_disabled':sum(not x.get('enabled') for x in health),
      'financial_kpis_live':False,'msx_connected':False,'msx_quotes_mode':'scheduled-delayed-snapshot',
      'message':'Scheduled public news and delayed MSX share-price snapshots; verified earnings do not update automatically.'}
    for name,obj in [('live-news.json',news),('feed-health.json',health),('live-status.json',status)]:
        (DATA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    seed=json.loads((DATA/'seed.json').read_text(encoding='utf-8'))
    with (DATA/'facts.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=['company_id','scope','period','metric','value','previous_value','previous_period','comparison_basis','unit','precision','growth_yoy','growth_basis','source_id']);writer.writeheader();writer.writerows(seed['facts'])
    if SITE.exists():shutil.rmtree(SITE)
    (SITE/'data').mkdir(parents=True)
    for name in ('seed.json','live-news.json','feed-health.json','live-status.json','facts.csv','stock-quotes.json'):
        shutil.copy2(DATA/name,SITE/'data'/name)
    html=(R/'index.html').read_text(encoding='utf-8')
    if 'const IS_STATIC=false;' not in html:
        raise ValueError('Static build marker is missing')
    html=html.replace('const IS_STATIC=false;', 'const IS_STATIC=true;', 1)
    for name in ('styles.css', 'app.js', 'research.js', 'stocks.js', 'icon.svg'):
        shutil.copy2(R/name, SITE/name)
    (SITE/'index.html').write_text(html,encoding='utf-8')
    (SITE/'.nojekyll').write_text('',encoding='utf-8')
    print('Site built:',SITE,'news:',len(news),'successful feeds:',status['feeds_ok'])
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');args=p.parse_args()
    build(refresh=not args.offline)
