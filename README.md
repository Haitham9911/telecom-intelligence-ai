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

The supplied seed contains Zain Group 9M/Q3 2026 figures and source links.
Other covered companies have no invented peer figures. Reported EBITDA margin
is used because rounded revenue is unsuitable for deriving an exact margin.
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
