# API

All routes return JSON. Money fields are **integer paise**. Timestamps are UTC ISO 8601. Watchlist/alert/settings routes use an HttpOnly anonymous session cookie; clients must retain it. No cross-origin API access is granted. POST accepts JSON objects up to 16 KB. Errors use `{ "error": "message" }` and HTTP 400/403/404/429/500 as appropriate.

| Route | Method | Input / result |
|---|---|---|
| `/api/health` | GET | version and health |
| `/api/products?q=samsung&sample=0` | GET | persisted matching listings; live by default |
| `/api/search` | POST | `{ "query": "product URL or text" }`; independent source statuses and persisted listings |
| `/api/platforms` | GET | source availability, last live success, error, circuit |
| `/api/history?id=LISTING_ID&days=30` | GET | actual observations, recorded extrema, first tracking, change; days 7/30/90/180/365 |
| `/api/watchlist` | GET | current browser's saved listings |
| `/api/watchlist` | POST | `{ "listing_id": "..." }` or add `"remove": true` |
| `/api/alerts` | GET | current browser's target alerts |
| `/api/alerts` | POST | `{ "listing_id": "...", "target": "25000.00" }`; target input is rupees |
| `/api/alerts` | POST | `{ "delete": "ALERT_ID" }`; owner scoped |
| `/api/notifications` | GET | latest 100 notifications, owner scoped |
| `/api/notifications` | POST | `{}` marks this browser's notifications read |
| `/api/settings` | GET/POST | `{ "interval_seconds": 21600, "notifications": true }`; range 900–604800 |

Source searches are limited to one per browser every 15 seconds and two simultaneous whole searches per process; four source threads per search. Edge IP/session limits are still needed before public deployment. Search is synchronous in this version; configure a several-minute upstream timeout. Existing verified records remain queryable during collection.

Lowest verified badge excludes stale, synthetic and unavailable listings. Comparison groups use exact product variant IDs; candidate title matches are never automatically grouped.

`GET /api/imports` returns up to 500 sourced history records; `?url=EXACT_PRODUCT_URL` filters by the original source listing URL. All rows retain external-unverified status, original reported timestamps and attribution. This endpoint never substitutes external prices for `/api/products` or `/api/history` values. Sourced history charts and live history are separate UI flows.
