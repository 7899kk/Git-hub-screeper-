# Architecture and extension

The browser talks to one API origin. The API queries SQLite and dispatches separate platform collectors. The worker claims persisted due jobs and uses the same collectors. Notifications are generated transactionally with successful live observations, then polled by the browser.

## Connector contract

`Connector.collect(URL_or_ID) -> Observation`, `Connector.search(query, limit) -> (observations, errors)`; failures use typed `CollectionError(code, message, retryable)`. Each platform module defines its own domains, routes and product path rule. The shared parser supports JSON-LD Product/Offer, graph nesting and explicit price metadata. It requires currency and a positive single selling price; AggregateOffer ranges, multiple structured products and multiple offers are rejected. Unknown fields stay nullable.

All 18 currently use shared structured extraction, with independent discovery routes. These are not 18 thoroughly reverse-engineered HTML parsers. Add platform-specific overrides to `parse`, `search`, `resolve` and `product_path` as live evidence justifies them. Add captured, sanitized platform fixtures before deploying each parser update. Authorized catalog/feed integration is preferable when HTML is unavailable.

A new source requires a module subclass, domain allowlist, name, discovery route/path rule, parser override if necessary, registry entry and fixtures. Do not accept arbitrary user-controlled external domains. HTTPS redirects are revalidated. HTTP errors, challenges, robots denials, payload bounds and timeouts produce source statuses rather than prices. Transport injection supports deterministic tests without bypassing runtime checks.

Requests are capped at 2 MB with a per-host one-second start gap. robots.txt is cached for one hour per process. Production adapters should also honor applicable crawl-delay/feed terms and use larger intervals where required. Retailer search discovers at most two products per source in the API; this is bounded discovery, not complete catalog ingestion.

## Matching and history

Known variant conflicts and brand conflicts prevent a merge. Exact model or GTIN can group listings only when supplied variants agree and are sufficiently represented. Title similarity is review-only. Empty variants require review. Decisions are recorded but no human adjudication UI is included yet.

Observations are append-only except explicit future retention changes. `(listing_id, observed_at)` prevents duplicate ingestion. Different check times remain separate even when prices stay equal. Latest prices use the newest observation, so out-of-order writes cannot overwrite a newer price. Failed refreshes mark retained prices stale; records older than 24 hours are also marked stale by the API. This fixed age threshold is deliberately conservative for weekly monitoring.

Historical extrema use all recorded observations for a listing; change percentage uses first/last in the selected window. Sample and live observations use separate namespaces and query modes. No extrapolation or synthetic live backfill.

## Queue

Each registered live listing has one persistent job, initially due in six hours. `BEGIN IMMEDIATE` serializes claims. Leases last five minutes and recover after a worker crash. One batch claims at most eight jobs, groups by source and processes up to four groups concurrently. Temporary failures back off exponentially; three attempts pause a job. Repeated failures open a 24-hour source circuit; nonretryable failures pause immediately. Paused jobs require operator review and `manage resume` rather than endless retry.

Watchlist settings can update shared listing intervals; shortest owner interval wins when settings are saved. The API itself does not start a hidden scheduler. Run the separate worker continuously or run `--once` from a host cron every minute.

## Scale and limitations

SQLite WAL, foreign keys, model/GTIN/history/job indexes and bounded request sizes suit one small server. Large catalog scans, unpaginated listing queries, anonymous sessions and an in-process source throttle do not constitute a production million-product architecture. Use durable authenticated identities, PostgreSQL, distributed rate limits, paginated queries, a queue broker and data-source contracts before that scale.
