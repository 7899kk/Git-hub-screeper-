# PricePulse India

Independent, mobile-first Indian shopping price collector and tracker. Original implementation; no third-party scraper repositories. Python 3.12+ standard library + SQLite + plain HTML/CSS/JavaScript. Includes an Android WebView client project.

**Release status: runnable first release, not complete live coverage of all 18 stores.** All 18 independent connector modules pass structured-data contract tests. The initial name-search probe extracted an out-of-stock AJIO price. Follow-up direct-link tests verified IKEA and revealed/fixed malformed Croma JSON-LD. Live API/worker acceptance reports are in `docs/live-acceptance*.json`; transient failures are preserved. Installed connectors must not be mistaken for verified retailer coverage. See [live probe](docs/live-probe.json) and [coverage](docs/COVERAGE.md).

## Start on a computer

1. Install Python 3.12 or newer from https://www.python.org/downloads/ . No pip packages are required.
2. Download this repository using **Code → Download ZIP**, extract it, and open a terminal inside the extracted folder. Alternatively:

```sh
git clone https://github.com/7899kk/Git-hub-screeper-.git
cd Git-hub-screeper-
```

3. Run the web app:

```sh
python -m backend.import_history
python -m backend.server --sample
```

4. Open http://127.0.0.1:8000 . The home screen starts in live mode with no preloaded live prices. Toggle **Show sample data** to explore synthetic examples. `--sample` creates sample history only; it does not fake real observations.
5. In a second terminal in the same folder, run monitoring:

```sh
python -m backend.worker
```

6. Paste a direct product URL or enter a product search. Live source requests can take a few minutes. A failed source cannot stop the others. Successful live collections enter the database and are scheduled at six-hour intervals. The worker continues while the browser is closed, as long as its server process is running.

No login is required. A private anonymous cookie identifies each browser's watchlist and alerts. Clearing the cookie or switching devices creates a new watchlist. There is no account synchronization in this release.

## Included

- Ten screen flows: home, search, comparison, product details, history, watchlist, alerts, categories, source status, settings. Search is integrated into comparison; history is integrated into product details.
- Eighteen independently configurable connectors using a shared request/extraction contract, host allowlists, HTTPS redirects, robots checks, failure reporting, throttling and structured offer parsing.
- Direct URLs on all supported hosts; ASIN input is implemented at connector level. Other platform identifiers need direct URLs. Universal search supports cached titles/brands/models/categories/GTINs and best-effort retailer name search; remote category/GTIN support depends on each retailer.
- Conservative matching by model/GTIN, known variants and brand. Title-only candidates require review and stay separate. Unknown variants require review. Matching decisions are stored.
- Integer-paise prices; conditional benefits never reduce listed prices. Shipping/MRP/discount fields are nullable and stay unknown when not extracted. A separate payable calculator only runs with explicit shipping, verified fixed discounts and fulfilled conditions.
- Immutable observations, indexed history windows, recorded extrema and percent changes. No backfilled live history. Identical ingestion timestamps deduplicate; unchanged prices at later successful checks are preserved.
- SQLite-backed queue: atomic claims, recovery leases, retries, source cooldowns, paused jobs, stale-price markers, local operator resume command.
- Private watchlists, target alerts, rearming and one notification per target crossing. Browser notifications while the page is open, when supported and permission is granted. No email/SMS/closed-app push delivery yet.
- Lightweight UI, SVG history chart with observation tooltips, tabular history, explicit samples, source timestamps and store links.
- Tests, GitHub CI, opt-in live-probe workflow, Docker deployment files, Android source and manual APK build workflow.

## Tests

```sh
python -m unittest discover -s tests -v
node --check frontend/app.js
python -m backend.live_probe
```

Live probes are opt-in network checks, not unit tests. Never interpret fixture tests as live verification. The committed probe is a dated snapshot and will become outdated.

## Structure

```text
backend/
  connectors/          separate modules for 18 platforms + common contract
  migrations/          relational schema, indexes, constraints
  models.py            validated observations, money normalization
  matching.py          conservative product / variant matching
  pricing.py           explicit conditional-payable calculation
  categories.py        best-effort title categorization
  database.py          transactions, observations, history, alerts, claims
  server.py            HTTP API, per-browser sessions, static frontend
  worker.py            background monitoring and retry handling
  manage.py            operator resume / backup / error pruning
  live_probe.py        opt-in source diagnostics
  sample.py            unmistakable synthetic examples
frontend/              responsive UI, SVG charts, web manifest
android/               online Android WebView client
 tests/                automated contract, engine, database and API tests
.github/workflows/     tests, manual probes, manual Android APK build
Dockerfile
compose.yaml
 docs/                 architecture, API, deployment, coverage, Android, costs
```

Read [API](docs/API.md), [architecture](docs/ARCHITECTURE.md), [deployment](docs/DEPLOYMENT.md), [Android](docs/ANDROID.md), and [costs](docs/COSTS.md).

## Boundaries before a public launch

This is a working first release for small self-hosted tracking, not a claim that every store can be scraped reliably. Most sources still need platform-specific live page investigation or authorized feeds. Browser-rendered pages are not executed. Multiple products/offers are rejected rather than guessed. Coupons, MRP, bank and exchange benefits are not currently extracted by platform-specific rules. No anti-bot bypass is implemented.

The standard-library web server is intended for small controlled deployments behind TLS and edge request limits, not large public workloads. Before a broad launch, add durable accounts, a production HTTP server, pagination, richer verified adapters/feeds, matching review administration and cloud push. Move to PostgreSQL and a distributed queue for multiple servers. Do not promise unlimited free collection or millions of tracked products.

No browser visual QA, physical Android device test, Android compilation, or hosted deployment was performed in the initial build. Automated API and extraction checks are the available verification.

## Follow-up: live refresh and previous data

Product details now include **Refresh live price**. Run `python -m backend.import_history` to load the included, attributed historical CSV, then open **Sourced history**. Imported records, source timestamps and source-recorded charts remain explicitly external/unverified; they do not alter live prices, observations, matching or alerts. Some source product titles/variants are inconsistent and need review. The file is not a universal history database and contains no previous history for the Croma/IKEA benchmark products. See [follow-up validation](docs/FOLLOW_UP.md).

### Look up a product's price history by year

Open **History by year**, paste a product URL and choose a calendar year. Existing verified observations and attributed repository records are shown separately. Optional Keepa integration supports Amazon India history when a server-side paid API key is configured. Unknown years stay unknown. See [year-history setup, sources and limits](docs/YEAR_HISTORY.md).
