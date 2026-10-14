# PricePulse Android (live-only)

React Native, TypeScript and Expo Router application. Production source has no demo switch,
seeded products, synthetic history or fallback prices. Synthetic provider responses exist
only in automated tests and the explicitly isolated browser-test service.

## Run without Android Studio

Requires Node 22.13+ and Python 3.12. From the repository root:

```sh
python -m venv .venv-pulse
.venv-pulse/bin/pip install -r pulse_api/requirements.lock
mkdir -p data
.venv-pulse/bin/alembic -c pulse_api/alembic.ini upgrade head
.venv-pulse/bin/python -m uvicorn pulse_api.app:app --host 0.0.0.0 --port 8010
```

In another terminal, from the same root:

```sh
.venv-pulse/bin/python -m pulse_api.worker
```

Then:

```sh
cd mobile
npm ci
npm run web
```

For local development, set the Backend URL in Settings to your machine's API address.
The web development server and API use separate ports; configure `PULSE_CORS_ORIGINS`
with the exact web origin if you change the default Expo port. HTTP connections are
accepted only by development builds. Production requires HTTPS.

For an Android phone, install Expo Go, run `npm start`, and scan the QR code **printed
by that command on your own machine**. The phone and computer must share a network.
Use your computer's reachable LAN IP for the backend address, not the phone's loopback
address. Use an Expo Go version compatible with this project's pinned SDK 57. Incoming
Android share registration requires a native development or standalone build; pasting
share text works in Expo Go. No iOS deliverable is included.

Snack could not be reached during implementation because the environment proxy denied
that domain. No Snack project was published, and no hosted URL or remotely usable QR
code was generated. This is a complete multi-file Expo Router project. Expo Go is the
reliable fallback; importing a single App.tsx into Snack would lose the routing and backend.

## Real data

Paste a supported product link. The API queues a permitted collection through the
original repository connectors. The worker records a price only if the source returns
an explicit price. Robots restrictions, challenges and network failures are retained.
Unknown retailer domains are recorded as candidates without fetching arbitrary pages.

On a product screen, Search other retailers requests bounded searches across the
implemented connectors. Each source is independent, at most one candidate is collected
per retailer, and four source threads run concurrently. Results are classified by exact
identifiers and variants; similar and incomplete products never become exact offers.
Cached products and searches do not imply exhaustive retailer coverage.

The new service uses a **separate database** from the root sample app. Do not point it
at `data/pricepulse.db`; its default is `data/pulse-api.db`. Retained data includes actual
observations and private device watchlists/targets. An empty catalogue is expected until
real collection or an authorized feed succeeds.

QuickCommerce and ExtraPe setup: [integrations](../docs/MOBILE_INTEGRATIONS.md).
Backend deployment, signing and store prerequisites: [release](../docs/MOBILE_RELEASE.md).
Executed checks and remaining blockers: [verification](../docs/MOBILE_VERIFICATION.md).

## Checks

From `mobile`:

```sh
npm run typecheck
npm run lint
npm test
npm run build:web
npm run build:android
```

`build:android` exports the Android JavaScript/Hermes bundle; it does not create an APK.
From repository root: `.venv-pulse/bin/python -m pytest pulse_api/tests -q`.

Browser scripts under `mobile/tests/` use Python Playwright and Chromium. The navigation
script expects the development web server on port 8082 and the empty live API on port
8010. For product/history UI tests, separately run:

```sh
.venv-pulse/bin/python -m uvicorn pulse_api.tests.browser_service:app --port 8011
python mobile/tests/browser_product.py
```

That service uses a temporary, isolated database and TEST FIXTURE titles. Never deploy
it or configure the release app to use it. Product fixture screenshots verify UI behavior,
not live retailer access. Browser scripts do not test a physical Android phone.
