# Telecom Intelligence AI

Arabic telecom research dashboard deployed through GitHub Pages.

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
JSON/CSV. Alert switches are browser-local preferences, not push notifications.

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
