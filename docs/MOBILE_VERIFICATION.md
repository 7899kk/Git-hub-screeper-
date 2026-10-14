# Mobile verification — 14 October 2026

The new Expo application is live-only. There is no demo mode or release seed dataset.
Nothing has been publicly hosted or submitted to an app store. Publication is blocked
on the external prerequisites listed below.

| Check | Observed result |
| --- | --- |
| Existing repository tests | 71 passed |
| New FastAPI/domain/provider tests | 37 passed |
| Mobile logic tests | 3 passed |
| TypeScript typecheck | Passed |
| ESLint | Passed |
| New backend Ruff checks | Passed |
| Expo web export | Passed |
| Android JavaScript/Hermes export | Passed; this is not an APK or AAB |
| Expo native prebuild | Passed; generated Android text-share intent inspected |
| PostgreSQL 17 migrations | Applied through revision 003 |
| PostgreSQL-backed API functional checks | Health, device sessions, empty live catalogue and unsupported resolver passed |
| Docker image | Built; non-root UID 10001; PostgreSQL-backed health request passed |
| Chromium at mobile viewport | Onboarding, settings, live empty states, 18 retailer statuses, unsupported links, watchlists, alerts, search, disclosures and offline errors passed without runtime errors |
| Isolated product UI tests | Exact comparison, separate history/statistics/range selection, recommendation, save and target alert flows passed without runtime errors |
| Real IKEA collection | Failed: egress proxy denied access with 403; no observation was created |
| QuickCommerce live request | Unrun: secure key binding and reviewed response schema unavailable; domain denied by current runtime policy |
| ExtraPe integration | Unverified/unconfigured; no official app/affiliate API documentation available |
| Expo Snack publication | Unrun; domain denied by current runtime policy |
| Native debug APK compilation | Attempted; blocked fetching React Native 0.86.3 from repo.reactnative.dev (403) |
| Signed AAB / EAS build / store submission | Unrun |
| Physical Android/share testing | Unrun |

Synthetic fixtures are confined to test code and a temporary browser-test database. Product
UI fixture results are not claims of real retailer access. The production service starts
with an empty catalogue and preserves actual source failures. The original root app remains
available separately; it is not the new mobile service or its database.

The native build used Java 17, Gradle 9.3.1, Android SDK/target 36, NDK 27.1.12297006,
CMake 3.22.1, arm64-v8a and two Gradle workers. The official command-line tool archive
checksum was verified. Java proxy and managed CA trust were configured without disabling
TLS verification. The remaining native failure is a confirmed denied dependency host,
not a demonstrated source compilation success or defect. No APK is presented as complete.

Warnings seen: Starlette's test client warns that the installed httpx integration is
being deprecated; tests completed. Expo offline installation cannot consult React Native
Directory. Gradle/Android tooling reports upstream deprecations and an SDK XML format
warning. None is represented as a successful native build.

Saved environment draft changes include updated install/start instructions, reviewed
retailer/Expo/provider/dependency domain requirements and the PULSE_QUICKCOMMERCE_KEY
requirement. A draft save does not apply networking, supply a credential or publish a
snapshot. Current live access must be rechecked after the owner saves relevant settings.

To resume the blocked work: save the domain changes; securely provide a rotated
QuickCommerce key; provide official QuickCommerce response documentation or a sanitized
response; provide ExtraPe integration documentation; deploy the actual HTTPS backend;
rerun native compilation and device testing; configure signing, a public privacy policy
and a support address. See MOBILE_RELEASE.md for build and deployment commands.
