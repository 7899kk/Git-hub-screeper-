# Live-only FastAPI service

Run installation and Alembic migration commands from the repository root; see
[mobile setup](../mobile/README.md) and [production deployment](../docs/MOBILE_RELEASE.md).
PostgreSQL is the production database. SQLite is supported for independent local
work and isolated tests. No samples are seeded into this service.

## API

Except `/health` and creation of `/sessions`, endpoints require a private device token
in `Authorization: Bearer <token>`. The server stores its hash, not the bearer value.
Do not embed retailer keys in the app. Money is integer INR paise. Timestamped observations
are retained per listing, and failed collection is never replaced by a mock response.

| Method and route | Behavior |
| --- | --- |
| GET `/health` | Database readiness and live-only mode |
| POST `/sessions` | Create a random private device credential |
| DELETE `/sessions` | Delete this device's saved products/alerts and revoke its token |
| GET `/retailers` | Directory, actual source states and candidate integrations |
| POST `/resolve` | Validate `{url}`, identify a cached observation or queue a permitted collection |
| GET `/collection/{job_id}` | Persistent job status, source failures and resulting listing |
| GET `/products?q=...` | Search observed titles, up to 100 results |
| GET `/products/{id}` | Listing data, condition, source, freshness and match confidence |
| GET `/products/{id}/comparison` | Comparable and uncertain candidates classified separately |
| POST `/products/{id}/discover` | Queue bounded equivalent-product discovery across implemented retailers |
| POST `/products/{id}/refresh` | Queue one supported collector refresh |
| GET `/products/{id}/history?days=30` | Separate retailer history; ranges 7,30,90,180,0 (all) |
| GET `/products/{id}/analysis?days=30` | Explained rule-based buying recommendation |
| GET `/watchlist` | Device-private saved listings |
| PUT/DELETE `/watchlist/{id}` | Save/remove a listing idempotently |
| GET/PUT `/alerts` | Read targets or save `{listing_id,target}` in integer paise |
| DELETE `/alerts/{alert_id}` | Remove this device's target |
| POST `/products/{id}/outbound` | Validated original product URL; affiliate tracking unavailable until configured |
| POST `/providers/quickcommerce/search` | Reviewed QuickCommerce integration using `{q,platform,lat,lon}` |

`/openapi.json` exposes the generated request contract. `/docs` is the framework's
Swagger page; its external UI assets were not verified in this restricted environment.
Business errors use FastAPI `{detail: ...}` with 401,404,422,429,502 or503 as appropriate.

Scheduled feed refresh, persistent queued collection, interrupted-job recovery and price
alerts are handled by `python -m pulse_api.worker`, separate from the API process. Current
feed imports should use one worker. A collector observation's unknown condition remains
unknown. Unknown retailer domains are candidates, not arbitrary fetch destinations.

Provider contracts and setup are in [MOBILE_INTEGRATIONS.md](../docs/MOBILE_INTEGRATIONS.md).
ExtraPe is deliberately unconfigured until official documentation is supplied.
