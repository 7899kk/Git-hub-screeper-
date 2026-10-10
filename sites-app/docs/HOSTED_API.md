# Connected hosted API

Base URL: https://pricepulse-india.karthik-konijedu.chatgpt.site/api/v1

The Sites app now uses POST `/collect` for real product-link collection. The Worker calls our own connector engine and stores successful observations in durable Cloudflare D1. It opens the returned listing automatically. The **API connection** screen tests `/health`, displays database connectivity and recorded listings, provides a live Flipkart test link, and shows the last collection response in that browser session. Errors remain visible; missing historical periods remain unknown.

Endpoints: GET `/health`, GET `/platforms`, POST `/collect` with `{ "url": "https://..." }`, POST `/search` with `{ "query": "...", "platforms": ["flipkart","amazon"] }`, GET `/history?id=LISTING_ID&days=30`, GET `/compare?ids=ID1,ID2`. Prices are integer INR paise. Each collection response includes `listings`, `currency`, `price_unit`, `verified_at` and `cached`.

## Access from another app

This deployment remains owner-private. The hosted PricePulse browser app uses its signed-in Sites session without any secret in browser code. In an Android WebView, loading this Site and signing in preserves this access boundary. A separate server integration uses the existing supported Sites service-access token as `OAI-Sites-Authorization: Bearer SERVER_SECRET`; retain it only on your app backend. Get/manage service access through Sites, never embed it in a public APK or front-end bundle. A plain anonymous fetch from another app will not work against a private Site. Cross-origin browser mutations are rejected; proxy requests through your authenticated app backend. Do not change the Site's audience just to bypass sign-in.

Root Python `/api/v1` uses `Authorization` with `PRICEPULSE_API_KEY`, which is a separate deployment/authentication option. Do not interchange the two headers or assume the root Python service runs inside Sites. The cloud source is under `sites-app/` in GitHub.

## Verification

`node --test tests/api.test.mjs` exercises the compiled Worker API and D1 migrations using fixtures. `node scripts/live-api-acceptance.mjs` makes real retailer requests through the compiled Worker API against an isolated database; its JSON report distinguishes this from production or browser testing. A successful result is one observation from the time checked, not older-year backfill. The production Sites database can be inspected separately. No unattended schedule or Android push service is active.

### Source-pause recovery

Only a source access block (`BLOCKED`, such as HTTP 403/429 or a challenge page) pauses the whole platform, for 15 minutes. A redirect, missing product or unsupported layout no longer pauses unrelated products. Up to three HTTPS redirects within exact approved retailer hosts are followed after product identity checks. Cross-host and variant-changing redirects remain rejected. Existing legacy redirect pauses do not block a manual product-link collection.

Recently verified cached prices may be returned before a source circuit check, with `cached: true` and the original timestamp. **Retry this link** sends `{ "url": "...", "retry": true }`, performs one fresh request even when a source is cooling down, and enforces a 30-second delay after the last failure. It does not reset every background job. A fresh failure remains visible and never creates a price observation. Successful collection clears the source failure status.
