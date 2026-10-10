# Connect an app to this scraper repository

This repository is a price-service backend. GitHub hosts its code, not an always-running scraping API. Deploy the root Docker/Python backend on an HTTPS server with persistent `/app/data` storage, and run the separate worker from `compose.yaml` for monitoring. Your app calls that server's base URL. The existing Sites preview has a different owner-private API and is not a public mobile API key endpoint.

Set `PRICEPULSE_API_KEY` to a long random server secret. Never commit it or include it in public browser JavaScript or a distributed APK. Your app backend can keep the secret and proxy requests; a public native app needs authenticated user accounts on that backend, not a shared embedded secret. If making browser requests in a private controlled installation, set `PRICEPULSE_APP_ORIGINS=https://your-app.example` (comma-separated exact origins; no wildcard). Default is no external browser CORS.

| Endpoint | Input | Result |
|---|---|---|
| POST `/api/v1/collect` | `{ "url": "https://dl.flipkart.com/dl/..." }` | Per-source status and recorded listings |
| POST `/api/v1/search` | `{ "query": "Samsung S25" }` | Accessible source results; no exhaustive catalogue guarantee |
| GET `/api/v1/compare?ids=id1,id2` | Up to 50 listing IDs | Separate exact-variant groups, sorted prices, lowest fresh available listing |
| GET `/api/v1/history?id=id1&days=30` | Recorded listing ID | Actual collector history |
| POST `/api/v1/year-history` | `{ "url": "https://...", "year": 2026 }` | Source-labelled yearly recorded data; unknown years remain empty |
| GET `/api/v1/platforms` | None | Availability and latest errors |

All `/api/v1/` endpoints require `Authorization: Bearer YOUR_SERVER_KEY`; they return 503 before a key is configured and 401 for an invalid key. The original same-origin UI endpoints remain available for the self-hosted frontend. External apps share one 15-second search cooldown and a global collection concurrency limit. Source failures stay separate from successes. Do not interpret a cached stale price as current. Prices are integer INR paise; divide by 100 to display rupees. Listed selling price excludes unverified conditional discounts.

Example (Node app backend):

```js
import {PricePulseClient} from '../sdk/pricepulse.mjs';
const pulse = new PricePulseClient(process.env.PRICEPULSE_BASE_URL, process.env.PRICEPULSE_API_KEY);
const result = await pulse.collect(productURL);
const comparison = await pulse.compare(result.listings.map(p => p.id));
```

Deploying the Dockerfile alone starts the API, not monitoring. Use the API and worker services with the same persistent database. Pass API environment variables to the API container using your host's secret configuration. No paid services or scraped API keys are required for our own accessible-page collectors. All-platform access and historical coverage are not guaranteed.
