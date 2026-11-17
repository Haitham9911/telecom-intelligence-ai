#!/usr/bin/env python3
"""Build public static site. No company secrets, no external dependencies."""
import csv,datetime as dt,io,json,shutil,sqlite3
from pathlib import Path
import updater,quotes,financial_refresh,oman_refresh
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
        financial_refresh.refresh(DATA)
        oman_refresh.refresh(DATA)
    if not (DATA/'stock-quotes.json').exists():
        (DATA/'stock-quotes.json').write_text(json.dumps({'schema':1,'quotes':[]}))
    with updater.connect() as db:
        db.row_factory=sqlite3.Row
        recent=[dict(r) for r in db.execute('SELECT * FROM feed_items ORDER BY COALESCE(published,discovered) DESC LIMIT 2000')]
        health=[dict(r) for r in db.execute('SELECT * FROM feed_health ORDER BY feed_id')]
    # Maintain historical stories despite GitHub Actions' temporary runners.
    curated=json.loads((DATA/'curated-news.json').read_text()) if (DATA/'curated-news.json').exists() else []
    uniq={}
    for x in prior+recent+curated:
        if x.get('kind')=='aggregator' and not updater.companies_in(x['title']):continue
        key=updater.canonical_url(x['url'])
        ids=x.get('company_ids') or updater.companies_in(x['title'])
        if isinstance(ids,str):ids=json.loads(ids)
        if x.get('company_id') and x['company_id'] not in ids:ids.append(x['company_id'])
        x['company_ids']=ids
        if key in uniq:
            x['company_ids']=list(dict.fromkeys(uniq[key]['company_ids']+ids))
            x['discovered']=min(x.get('discovered') or updater.utcnow(),uniq[key].get('discovered') or updater.utcnow())
        uniq[key]=x
    news=sorted(uniq.values(),key=lambda x:x.get('published') or x.get('discovered') or '',reverse=True)[:2000]
    active_health=[x for x in health if x.get('enabled')]
    status={'mode':'scheduled-public-rss','worker_enabled':True,'poll_interval_seconds':1800,
      'last_success':max((x['last_success'] for x in active_health if x.get('last_success')),default=None),
      'last_checked':max((x['last_checked'] for x in active_health if x.get('last_checked')),default=None),
      'feeds_ok':sum(bool(x.get('last_success') and not x.get('last_error')) for x in active_health),
      'feeds_failed':sum(bool(x.get('last_error')) for x in active_health),
      'feeds_disabled':sum(not x.get('enabled') for x in health),
      'financial_kpis_live':False,'msx_connected':False,'msx_quotes_mode':'scheduled-delayed-snapshot',
      'message':'Scheduled public news and delayed MSX share-price snapshots; verified earnings do not update automatically.'}
    configured=json.loads(updater.FEEDS_FILE.read_text())['feeds']
    status['company_coverage']={cid:[dict(row,kind=next((f.get('kind') for f in configured if f['id']==row['feed_id']),'')) for row in health if any(f['id']==row['feed_id'] and f.get('company_id')==cid for f in configured)] for cid in ('OTEL','ZAIN','ORDS','STC','EAND','DTE','VZ','TMUS','TEF')}
    status['built_at']=updater.utcnow()
    for name,obj in [('live-news.json',news),('feed-health.json',health),('live-status.json',status)]:
        (DATA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    financial_refresh.export(DATA)
    oman_refresh.export(DATA)
    seed=json.loads((DATA/'seed.json').read_text(encoding='utf-8'))
    with (DATA/'facts.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=['company_id','scope','period','metric','value','previous_value','previous_period','comparison_basis','unit','precision','growth_yoy','growth_basis','source_id']);writer.writeheader();writer.writerows(seed['facts'])
    with (DATA/'five-year-financials.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        w=csv.writer(fh);w.writerow(['company','year','currency_millions','revenue','ebitda','attributable_profit','basis','source','ebitda_source','operating_earnings_metric','profit_metric','comparable_prior_revenue','comparable_prior_source'])
        for p in seed.get('intelligence',{}).get('profiles',[]):
            for a in p['annual']:w.writerow([p['id'],a['year'],p['currency'],a.get('revenue'),a.get('ebitda'),a.get('attributable_profit'),a.get('basis_en'),a.get('source_url'),a.get('ebitda_source_url'),a.get('ebitda_label',p.get('ebitda_label','EBITDA')),p.get('profit_label','Attributable profit'),a.get('comparative_revenue'),a.get('comparative_source_url')])
    with (DATA/'operating-metrics.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        w=csv.writer(fh);w.writerow(['company','scope_or_market','year','metric','value','unit','basis','source'])
        for p in seed.get('intelligence',{}).get('profiles',[]):
            op=p.get('operations',{})
            for row in op.get('group',[]):
                for k in ('capex','free_cash_flow','operating_cash_flow','customers','net_debt','net_debt_ebitda'):
                    if row.get(k) is not None:w.writerow([p['id'],op.get('scope_en','Group'),row['year'],k,row[k],'million customers' if k=='customers' else 'times' if k=='net_debt_ebitda' else op.get('currency',p['currency'])+' million',' | '.join(filter(None,[op.get('note_en',''),row.get('basis',{}).get(k),str(op.get('metric_labels',{}).get(k,''))])),row.get('sources',{}).get(k) or row.get('source_url','')])
            for market in op.get('markets',[]):
                for row in market['rows']:
                    for k in ('arpu','prepaid','postpaid','revenue','ebitda','customers'):
                        if row.get(k) is not None:w.writerow([p['id'],market['name_en'],row['year'],k,row[k],market['arpu_unit'] if k in ('arpu','prepaid','postpaid') else 'million customers' if k=='customers' else market['currency']+' million',market['note_en'],row.get('sources',{}).get(k) or row.get('source_url',market.get('source_url',''))])
    if SITE.exists():shutil.rmtree(SITE)
    (SITE/'data').mkdir(parents=True)
    for name in ('seed.json','live-news.json','feed-health.json','live-status.json','facts.csv','stock-quotes.json','five-year-financials.csv','operating-metrics.csv','indicator-data.json','financial-indicators.csv','oman-data.json','oman-market.csv'):
        shutil.copy2(DATA/name,SITE/'data'/name)
    html=(R/'index.html').read_text(encoding='utf-8')
    if 'const IS_STATIC=false;' not in html:
        raise ValueError('Static build marker is missing')
    html=html.replace('const IS_STATIC=false;', 'const IS_STATIC=true;', 1)
    for name in ('styles.css', 'app.js', 'research.js', 'stocks.js', 'intelligence.js', 'indicators.js', 'oman.js','oman-analysis.js','oman-research.js', 'icon.svg'):
        shutil.copy2(R/name, SITE/name)
    (SITE/'index.html').write_text(html,encoding='utf-8')
    (SITE/'.nojekyll').write_text('',encoding='utf-8')
    print('Site built:',SITE,'news:',len(news),'successful feeds:',status['feeds_ok'])
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');args=p.parse_args()
    build(refresh=not args.offline)
