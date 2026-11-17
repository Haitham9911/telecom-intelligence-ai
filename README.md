# Telecom Intelligence AI

Arabic and English telecom research workspace deployed through GitHub Pages.

## Research workspace

- Responsive layout, mobile navigation, and a light/dark theme.
- Searchable company directory and news feed with company, topic, and date-order filters.
- Sourced financial results with period selection, actual reported growth charts, and CSV export.
- Company and article bookmarks saved locally in the current browser.
- Source health, last successful refresh, and clear separation of news from financial data.

Articles retain their original publisher language. Interface language and theme
preferences persist in the current browser. No sign-in or cross-device bookmark
synchronization is provided.

## Deployment

This project belongs only to `Haitham9911/telecom-intelligence-ai`.
The deployment job checks the repository name before running.

In **Settings → Pages**, set **Source** to **GitHub Actions**. The workflow
`.github/workflows/pages.yml` validates, refreshes public RSS feeds, builds
`_site/`, and publishes it on pushes to `main`, manual runs, and the schedule.

## Scheduled news

The cron expression `7,37 * * * *` checks public news twice an hour, at minutes
07 and 37 (also 07 and 37 in Oman). GitHub may delay scheduled jobs. Public
repositories can have schedules disabled after 60 days without repository
activity; check the Actions page if the dashboard becomes stale.

Feed history and conditional-request metadata are retained in a repository
Actions cache. Cache eviction is possible; a fresh run can rebuild from the
publishers' current feeds. Failures and last successful checks are shown in
the dashboard. TeleGeography is enabled using its current RSS address. Telecoms Tech News is
disabled because its feed redirects to an HTML homepage. Only news headlines,
links, and short feed summaries refresh.
Financial figures and share prices do not refresh from RSS.

No API keys, private company data, or connection to other business systems
are required. The GitHub Pages build publishes only static HTML and public
JSON/CSV. Watchlists are browser-local bookmarks, not push notifications.

## Validation and local use

```sh
python -m unittest -v test_live.py test_app.py test_deploy.py
python build_static.py --offline
python -m http.server 8765 --directory _site
```

Run `python build_static.py` for a real public-feed refresh, or `python server.py`
for the optional local Python API on 127.0.0.1. The local server is not needed
for GitHub Pages.

## Financial data

The reviewed seed contains FY2021–FY2025 and separate 9M2026 disclosures for
nine groups: Omantel, Zain, Ooredoo, stc, e&, Deutsche Telekom, Verizon,
T-Mobile US and Telefónica. Each row preserves its source and reporting basis.
Reported margins are used where available; derived ratios are labelled.
Omantel excluding Zain cannot be calculated by simply subtracting the two
published consolidated groups; eliminations and adjustments are required.

## Not implemented

Live exchange prices, automatic financial-statement extraction, cross-company
normalized comparisons, AI-generated analysis, account login, native mobile
apps, and push/email alerts are not implemented.

### Omantel research and reporting scopes

The Arabic/English interface now includes direct `#omantel`, `#reports` and
`#comparisons` routes. Omantel has separate consolidated and excluding-Zain
views, prior-period figures, Q3/H1/9M period selection where sourced, and CSV
exports that retain reporting scope and source provenance.

Omantel consolidated figures use the financial statements approved 12 November
2026 and published on MSX; the 11 November preliminary disclosure supplies 9M
EBITDA, reported margins and the excluding-Zain scope. The latter is not derived
by subtracting Zain from consolidated results. Its normalized profits, including
the final dividend adjustment, are distinct metrics rather than reported profit.
The comparison retains OMR and KWD and charts growth/margins only, because the
scopes overlap and their absolute amounts cannot be combined.

Financial snapshots are reviewed manually. The existing GitHub Actions schedule
continues to refresh public news approximately twice an hour.

### Share prices

`#stocks` shows delayed MSX snapshots for Omantel (OTEL) and Ooredoo Oman
(ORDS, internal company ID ORED). `quotes.py` reads only their public MSX
snapshot pages and validates the symbol, price, previous close and percentage
change. Retrieval timestamps are distinct from the unavailable trade timestamp.
MSX quotes have a 15-minute source delay plus the existing approximately
30-minute GitHub Actions publication interval. Failed retrievals retain the last
successful price and timestamp and display a warning; missing prices are never
zero. The workflow caches quote history alongside public news history.

Attributed TradingView widgets display Zain (KSE:ZAIN, Kuwaiti fils), Deutsche
Telekom (XETR:DTE, EUR, end-of-day), Telefónica (BME:TEF, EUR), Verizon (NYSE:VZ,
USD) and T-Mobile US (NASDAQ:TMUS, USD). These connect from the visitor's browser
and preserve the provider's currency, timing and delay labels. They are separate
from reviewed financial-statement snapshots. e& was verified as unavailable for
external widget display and is not embedded; Saudi stc, Ooredoo Qatar, Vodafone
and Singtel are also outside current embedded quote coverage. No API keys or
paid data subscriptions are configured.

Source documentation: https://www.msx.om/snapshot.aspx?s=OTEL and
https://www.tradingview.com/widget-docs/faq/data/ .

## Five-year research and company monitoring

The research workspace covers nine groups for FY2021–FY2025, alongside separate 9M2026 disclosures. Every annual row has primary-source links and reporting-basis notes. IAS29, discontinued operations, acquisitions and exceptional gains must not be treated as organic growth. Cross-company charts use margins/growth; native-currency amounts are never added or ranked as a common currency.

`data/seed.json:intelligence` stores reviewed financial and strategy snapshots. `intelligence.js` calculates labelled comparisons locally. Missing comparisons remain null; scope breaks suppress misleading YoY calculations. The UI offers company/year/metric selection, five-year CSV, strategic priorities and analytical monitoring questions.

`feeds.json` configures English/Arabic Google News RSS searches for five Gulf groups, English searches for four global companies, the official e& newsroom and TeleGeography. Aggregators are explicitly labelled; title matching rejects unrelated search hits. Official e& HTML ingestion reads only dated headline links and fails visibly if markup changes. Company tags can include multiple groups. URL deduplication strips tracking parameters and preserves cross-feed history. A maximum 2000 archived headlines is published; this is bounded, best-effort monitoring, not exhaustive coverage. GitHub cache eviction and publisher indexing can cause gaps.

The existing30-minute GitHub Pages schedule refreshes news and delayed quotes. Financials and strategy are reviewed separately; the visible review date must only advance after source review. A daily ChatGPT automation checks new official disclosures and strategies and can update this repository after validation. It is separate from GitHub Actions and has not necessarily run merely because it is configured.

Validation: `python -m unittest -v test_live.py test_app.py test_deploy.py test_quotes.py test_intelligence.py` and `node test_intelligence.cjs`.

Operating intelligence adds Ooredoo's eight markets for 2021–2025 (ARPU, revenue, EBITDA and year-end customers), plus prepaid/postpaid ARPU for Qatar, Kuwait and Oman. Ooredoo ARPU is Q4 monthly in QAR for every market, not annual or local currency. Qatar's 2022 comparative is restated. e& UAE mobile/fixed ARPU is also Q4; Omantel/Zain report bases differ. The operating page separates domestic/market scope from consolidated financials and links metric-level sources. CapEx, company-defined FCF, CFO, subscriptions and debt are shown where verified; unavailable values remain null. CSV exports preserve scope and units.

Market analysis now provides a selectable-year Ooredoo eight-market matrix, revenue/ARPU/customer growth and EBITDA margin movements. Share links retain market, year and metric. Qatar 2022 ARPU growth and Omantel 2023 ARPU growth are suppressed for definition changes. Omantel FY2025 mobile/fixed ARPU and prepaid/postpaid detail are sourced from the 9 March 2026 full-year conference call (pages18–19); domestic total subscriptions stay separate from historical mobile including resellers. Metric definitions remain expandable in the UI. Growth is descriptive, not a causal attribution.

### Global comparison definitions

Comparison presets select all nine groups, the five Gulf groups, or the four global companies. Revenue growth is the default chart. The operating measure retains each company's exact definition: Deutsche Telekom Adjusted EBITDA AL, Verizon Consolidated Adjusted EBITDA, T-Mobile Core Adjusted EBITDA, and Telefónica reported OIBDA/EBITDA. These measures are not a normalized efficiency ranking. Deutsche Telekom consolidates T-Mobile, just as Omantel consolidates Zain; group totals must not be summed.

Telefónica FY2025 revenue growth uses its restated FY2024 continuing-operations comparator. Its FY2025 and 9M2026 profit margins are suppressed because total profit includes discontinued operations while revenue excludes them. Negative reported profits remain negative in the charts. Deutsche Telekom annual revenue follows the management approach, not a continuous audited continuing-operations series. Source notes identify one-off gains, acquisitions and changes of scope. Cash metrics retain company definitions, including FCF AL and adjusted FCF; no unavailable ARPU series is inferred.

## Financial indicators and automatic balance-sheet updates

`#indicators` adds a company selector, five-year indicator chart and table, interim column, category filters, peer comparisons and CSV. It includes sourced customers/connections, distinct domestic and account measures, gross borrowing and lease-inclusive debt, company-defined net debt, cash equivalents versus bank balances, assets, equity and cash-investment metrics. Reporting scope and metric definitions remain attached to every record. Not every company publishes every metric: missing values stay blank. Omantel consolidated customers are verified only for 2024–2025; stc Group customer totals remain unavailable, with KSA mobile/fixed shown separately. T-Mobile stops total-customer reporting from Q1 2026 and reports postpaid accounts separately.

`data/financial-indicators.json` is the reviewed source dataset. `financial_refresh.py` checks the SEC companyfacts API for Verizon and T-Mobile no more than once every six hours, including failure backoff. It accepts only supported USD instant facts in 10-K/10-Q filings, validates company identity and dates, and stores each accession and exact balance date. Latest filed comparatives may restate history. It does not infer customers, ARPU or company-defined net debt from SEC standard tags. `data/financial-auto.json` retains successful facts and status across failed requests and is cached by GitHub Actions. `indicator-data.json` and CSV combine reviewed rows with the automatic balance-sheet feed; no manual row is overwritten on disk.

The existing GitHub Pages job publishes changes; the existing daily 08:00 Asia/Muscat research automation reviews all nine companies and the indicator dataset. A schedule or successful source check does not imply a new disclosure. The UI separates latest filing/balance dates, source checks, and completed reviews. Browser Refresh loads the last published snapshot, not a new issuer report. Financial data is periodic, not live tick data. Tests include instant-versus-duration periods, currency isolation, failed-refresh retention, customer reporting changes and mixed-scope ratio suppression.

Additional validation: `python -m unittest -v test_financial_refresh.py` and `node test_indicators.cjs`.


## Oman TRA/NCSI observatory and Ooredoo details

`#oman-market` combines source-linked TRA open data, reviewed TRA market-share reports and NCSI monthly/yearbook statistics. It presents FY2021–2025, separate latest periods, prepaid/postpaid/M2M counts, mobile/fixed broadband, technology mix, penetration, investment, service revenue and service-specific ARPU. Annual revenue requires all four quarters; annual ARPU is Q4. Company definitions and source-vintage differences remain explicit. September 2026 NCSI totals and June 2026 TRA operator shares must never be multiplied together.

Vodafone mobile and Awasr fixed-broadband counts are estimates from the matching TRA period's total and rounded share, with formulas and rounding sensitivity, not direct company disclosures. H2 2025 mobile-broadband share and H1 2026 all-mobile share are different measures. Never allocate the residual after Omantel and Ooredoo to Vodafone. Reported Omantel domestic counts remain separately scoped.

`oman_refresh.py` checks five public TRA HTML tables at most daily, validates headers, periods, nonnegative values and component totals, and preserves the last successful data on failure. `data/oman-auto.json` is cached by the existing Pages workflow; reviewed sources are in `data/oman-market.json`. Build exports `oman-data.json` and `oman-market.csv`. NCSI PDFs, market-share reports and company details require actual source review through the existing daily research automation. A successful check is not a new observation, and financial/sector disclosures are periodic, not live ticks.

Ooredoo's operating page puts country selection and latest customer/ARPU cards first. Oman has exact five-year prepaid/postpaid/fixed-line counts and Q4 ARPU, six quarterly observations through Q3 2026, and separate 9M 2026 results. Eight markets can be compared. Ooredoo ARPU and financial schedules retain QAR even outside Qatar; Fixed Line preserves the issuer's definition. Consolidated group counts exclude IOH, and company-defined net debt is not reconstructed by subtracting the displayed cash from debt.

Validation: `python -m unittest -v test_oman.py test_deploy.py` and `node test_oman.cjs`.


### Calculated Oman growth analysis

`#oman-market?view=analysis` adds adjacent-month changes from the same NCSI publication, prepaid/postpaid reconciliation, fixed-broadband share movement and five-year annual changes/CAGR. Month comparisons require the exact preceding month, matching source vintage, scope and units. Share estimates use matched service definitions and each period's own denominator. The change interval accounts for rounding in both reported shares; it is not a confidence interval and can span zero. Vodafone mobile-broadband and all-mobile shares are intentionally not compared. Awasr's arithmetic decomposition separates the market-size and share terms without claiming causation. Ooredoo Oman adds annual mobile growth, postpaid mix and ARPU growth; postpaid mix is within its own base, not national market share. CSV exports preserve missing values and period bases. Test with `node test_oman_analysis.cjs`.
