# Live connector coverage

One live search for `samsung` was attempted per source on 10 October 2026, with at most one product page per source. This snapshot tests discovery and structured extraction, not every product URL or layout. Fixtures are separate from live results.

| Platform | Observed live outcome |
|---|---|
| amazon | http: HTTP 503 |
| flipkart | no_verified_price: no successful price |
| myntra | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| ajio | live_price_extracted: one out-of-stock price extracted |
| tatacliq | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| meesho | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| snapdeal | blocked: HTTP 403 |
| jiomart | page_size: Page exceeds 2 MB |
| croma | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| reliancedigital | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| vijaysales | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| nykaa | internal: got more than 100 headers |
| firstcry | blocked: HTTP 403 |
| shoppersstop | blocked: HTTP 403 |
| pepperfry | robots_denied: Source disallows this collection path |
| urbanladder | page_size: Page exceeds 2 MB |
| ikea | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |
| decathlon | search_unavailable: No crawlable product links; use a direct URL or authorized catalog feed |

AJIO returned a live structured price for a Samsung watch with `out_of_stock` availability. It must not be highlighted as a purchasable lowest offer. See `live-probe.json` for exact timestamps and evidence. Do not load this snapshot as a current price database.

Independent routes and shared JSON-LD parsing exist for all 18 modules. Most sources still require validated platform-specific HTML/rendered/API/feed adapters. Domain availability does not imply collection success. Missing coupons, bank benefits, exchange amounts, seller, MRP and shipping stay unknown.

Nykaa’s response exceeded the Python HTTP header limit. The transport subsequently maps such protocol failures to a typed `network` error instead of an internal exception. That handling fix is not a claim of live Nykaa support.

Run `python -m backend.live_probe` for a new snapshot. Reports reflect the network/IP and source response at the time of execution.
