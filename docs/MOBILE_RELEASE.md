# Android release and backend deployment

This document describes a deployable live-only project. It is not a claim that an APK,
AAB, hosted backend, Snack preview, retailer integration or store listing has been published.
See MOBILE_VERIFICATION.md for executed results and outstanding release prerequisites.

## Production backend

Use Python 3.12+ and PostgreSQL 17. `compose.mobile.yaml` provides an API, a separate
scheduler/collector worker, a persistent PostgreSQL volume and health checks. It requires
a database password from secure deployment configuration. No provider secrets are included.

```sh
# Set PULSE_DB_PASSWORD securely; do not commit it.
docker compose -f compose.mobile.yaml up --build -d
```

If the Docker daemon cannot reach PyPI through your environment proxy, download the
pinned wheels through the host's verified TLS/proxy route first:

```sh
bash pulse_api/build-image.sh
```

Wheels in `pulse_api/vendor` are ignored by Git. The Dockerfile installs them offline when
present; a normal Internet-enabled build installs the same pinned packages from PyPI.
Do not disable TLS or package integrity checks. The current wheel cache targets Python
3.12 on Linux x86_64. Refresh it for other architectures; do not reuse incompatible wheels.

The API listens on loopback port 8010. Put a TLS reverse proxy in front of it on your
actual domain. Configure request size limits (16 KB), per-IP limits and upstream timeouts.
Native clients use HTTPS and a private device token; web origins must exactly match
`PULSE_CORS_ORIGINS`. No wildcard credentialed CORS is enabled. The API applies a local
180-request/minute/IP guard; distributed rate limits belong at the edge. Use one worker
for the current feed ingestion path and persistent database backups. Do not expose
PostgreSQL publicly. The database is separate from the legacy Python app database.

Example location inside your existing TLS server configuration:

```nginx
location / {
    client_max_body_size 16k;
    proxy_pass http://127.0.0.1:8010;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
}
```

Configure trusted proxy addresses explicitly before trusting forwarded client IPs.
Restrict server egress to reviewed retailer/feed/API domains. Do not add wildcard egress.
Migrations run before API startup; the worker waits for API health. `/health` verifies
database access. A successful health request does not verify live retailer access.

## Android builds

Dependencies are pinned by `mobile/package-lock.json`. The package ID is
`in.pricepulse.mobile`; confirm it is yours and available before a first store submission.
`app.json` includes original PricePulse icon assets, Android text-sharing configuration,
and blocked location/contact/audio/storage/overlay permissions. Device tokens use native
SecureStore. Share integration still needs device testing.

Set `EXPO_PUBLIC_API_URL` to the **real deployed HTTPS backend** in your build environment.
This is a public endpoint URL, never a key. `app.config.ts` rejects EAS production builds
without an HTTPS endpoint. Keep retailer/affiliate secrets exclusively on the backend.

For a local debug APK, after installing the official Android SDK and required Java 17:

```sh
cd mobile
npm ci
npx expo prebuild --platform android --no-install
cd android
./gradlew --no-daemon --max-workers=2 :app:assembleDebug -PreactNativeArchitectures=arm64-v8a
```

A debug APK is for testing, not a Play Store submission. `npm run build:android` only exports
the JavaScript bundle. For Expo's managed build service, use your existing authorized
Expo account and review its current free quotas before requesting a build. No account
was created or paid plan accepted during this task.

```sh
cd mobile
npx eas-cli@latest build --platform android --profile preview
npx eas-cli@latest build --platform android --profile production
```

The preview profile requests an APK; production requests an Android App Bundle. EAS project
ownership, signing credentials and the actual backend URL must be configured by the owner.
Do not upload a debug-signed bundle as a production app. No EAS build or submission was run.
For this cloud toolchain, `python mobile/scripts/build_android_cloud.py` preserves the
existing proxy and machine-managed Java CA trust. The required React Native artifact
host must first be allowed. Java/SDK paths are retained under `/workspace`; no TLS
verification bypass is used.

Local signed builds are also possible with your securely stored keystore and Android SDK;
never place signing passwords or keystore files in Git or app frontend configuration.

## Before store publication

The outstanding concrete prerequisites are: deployed HTTPS backend and persistent database;
at least one successfully validated live data integration; provider-approved product and
image usage; rotated QuickCommerce key and reviewed response mapping; native Android build,
physical-device/share-flow testing and owner-controlled signing; a public privacy policy
and support contact; and a store listing reflecting actual supported coverage. ExtraPe
commission claims require its official integration first. Do not claim all retailers,
background phone push, fabricated older history or guaranteed future prices.

In-app targets are implemented. Phone push/email/SMS delivery is not configured. The app
supports device-private saved data, not synchronized accounts. Saved data can be erased
from Settings. The public policy must describe device tokens, saved products, targets,
product observation retention, provider searches and area-derived identifiers accurately.

No backend was purchased, no subscription was started, and nothing was pushed, hosted,
submitted to a store or publicly published by this task.
