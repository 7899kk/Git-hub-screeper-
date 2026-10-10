# Product URL and calendar-year history

Start the server and open **History by year**. Paste a direct retailer product URL, select a year, and submit. It queries actual local observations and attributed imported data. Each source/price type/variant remains separate, with recorded extrema, timestamps, point chart and table. Missing years show `no_history`; a year does not imply complete daily coverage. This lookup does not refresh today's selling price: use universal search or a product's Refresh live price button for that.

## Try it without a paid provider

```sh
python -m backend.import_history --db data/pricepulse.db
python -m backend.server --db data/pricepulse.db
```

Use `https://www.amazon.in/dp/B0H2J3PRKV`, year **2026**: two repository-reported Samsung Galaxy S25 records. Select **2025**: no history. These are external claims, not independently verified retailer observations. The imported repository does not specify its timestamp timezone. ASIN matching works with an Amazon product slug or tracking parameters; other platform variants are not merged by title.

API: `POST /api/year-history` with `{"url":"https://www.amazon.in/dp/B0H2J3PRKV","year":2026,"provider":false}`. Returns source-separated `series`, integer INR paise prices, recorded extrema and `provider_status`. It excludes synthetic sample history. Years must be integers from 2000 through the current year.

## Optional Amazon India provider

Set `KEEPA_API_KEY` privately in the server's environment, restart, then check **Also query Keepa**. Do not put the key in browser code, GitHub, request bodies or app settings. Keepa requires a paid API subscription and token allowance; configure deployment access controls before exposing a token-consuming service publicly. This release has a concurrency limit and 24-hour shared ASIN cache, but not account-based usage billing or per-user provider quotas. Requests for different years reuse the same cached product history. It requests India marketplace/domain 10, raw history, no offers and no forced refresh. Failed requests do not fabricate data or update live observations. Errors do not reveal credentials. Provider records use `external_provider`, and unavailable price events remain null. Amazon retail and marketplace-new series are separate; MRP, used, bank, shipping and exchange prices are not substituted.

The adapter was implemented independently against the documented API structure; no scraper repository code was copied. Parser/cache fixtures and the HTTP lookup are tested. **A paid live Keepa request has not been tested because no API key is configured.** Provider coverage and past years depend on its actual records; this is not an all-platform historical archive.

## Sources and reusable code researched

- https://github.com/akaszynski/keepa — Apache-2.0 Python client and documented history examples; requires paid credentials. Our adapter remains standard-library-only.
- https://keepaapi.readthedocs.io/en/latest/product_history.html — history types, missing history and discontinuous price data.
- https://github.com/datawithsaurabh/Price-Tracker — MIT attributed dataset already bundled under `imports/`; external/unverified records, not adopted scraper code.
- https://pricing-intelligence.buyhatke.com/ — business historical-query offering; no usable public historical endpoint/export was obtained. No guessed Buyhatke API integrated.
- https://pricehistory.app/page/business — business API contact; needs a service agreement and documented credentials before integration.
- https://github.com/pricewatcha/pricewatcha-api — public API project researched; health/search requests returned HTTP 403 during evaluation, so no records imported.
- https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md — archive discovery reference. Not integrated: snapshots may be sparse or missing prices and need independently validated extraction. Archive captures must not be stamped as current retailer checks.

Repository source code cannot reconstruct prices never recorded. Future integrations should implement the same source-separated series contract and retain provenance, seller/variant differences, timestamp semantics and licensing. Running monitoring continuously records future history from successful checks.
