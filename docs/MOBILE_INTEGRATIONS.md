# Mobile retailer and affiliate integrations

## Provider contracts

`pulse_api/providers.py` declares `ProductProvider.observations()` and
`AffiliateProvider.generate(destination)`. API consumers are private device sessions;
retailer and affiliate keys never go into Expo environment variables or mobile code.

The registry in `pulse_api/retailers.json` contains the existing 18 retailers. Their original
modules under `backend/connectors/` enforce exact HTTPS hosts, robots checks, source
throttling and structured single-offer extraction. No CAPTCHA or anti-bot bypass is added.
The API does not fetch unrecognized domains. Add new retailer capabilities through a
reviewed connector or licensed feed; `PULSE_RETAILERS_FILE` can add directory entries
without changing comparison UI. Candidate entries remain unsupported.

A fresh observation proves the observed listing price, not the completeness of a source,
shipping fees, condition or bank eligibility. Legacy page collectors leave condition
unknown, so their results cannot be classified as verified exact variants until an
appropriate authorized integration supplies that missing information. Compare carefully.

## Licensed feed

Set `PULSE_FEED_PATH` or a fixed `PULSE_FEED_URL` and `PULSE_FEED_LICENSE` only for data
you have permission to use. Optional `PULSE_FEED_TOKEN` stays on the server. Redirects
are not followed for credential-bearing feed requests. JSON is a list conforming to
`ListingInput` in `pulse_api/domain.py` (the Python model defines the complete observation contract).
Required fields include an immutable listing ID, retailer ID/name, title, canonical HTTPS
URL, variant attributes, condition, positive integer INR paise price, timezone-aware
observation timestamp and source. Unknown data stays unknown. Duplicate observations
deduplicate; changing the price at the same timestamp or mutating listing identity fails.

The worker refreshes feeds at six-hour intervals by default and processes a persistent
collector queue every five seconds. Collected page listings receive scheduled refreshes
at six-hour intervals. Failed collections never create observations. Queue leases recover
an interrupted job; retries and queue capacity are bounded. Run one worker per deployment
for the current feed import path. Multi-worker distributed feed ingestion is not claimed.

## QuickCommerce API

The supplied example specifies `GET https://api.quickcommerceapi.com/v1/search` with
`X-API-Key` and `q`, `platform=BlinkIt`, `lat`, `lon`. Those are the only documented request
facts currently available. Other platform identifiers, response fields, currency units,
access plans and affiliate behavior are not invented.

1. Rotate the credential posted in chat through the issuing service.
2. Add its replacement as `PULSE_QUICKCOMMERCE_KEY` in secure environment settings.
3. Save the requested domain access for `api.quickcommerceapi.com`.
4. Supply official response documentation or a sanitized successful response.
5. Review a response mapping file and set `PULSE_QUICKCOMMERCE_SCHEMA_FILE` to it.

The mapping format is internal configuration, **not an invented provider response**:
`results_path` selects the documented results list; `fields` maps our ListingInput field
names (`id`, `title`, `url`, `price`, plus documented identity/variant attributes) to real
provider paths; `price_unit` must be explicitly `rupees` or `paise`; `currency` must be
explicitly `INR`. Until reviewed mapping and credentials exist, the search endpoint
returns an actionable 503 instead of making up products or units. Mock response tests
use deliberately artificial field names and do not claim provider verification.

The app's Search screen accepts manually entered area coordinates. No Android location
permission is requested. Coordinates are transmitted only for a requested provider search;
they are not retained in plaintext. An area-derived identifier separates observations
from different delivery areas; it should not be considered an anonymization guarantee.
Local grocery prices from different areas are not interchangeable. QuickCommerce polling
by saved delivery area and background grocery refresh need a reviewed provider contract
and explicit persistence/consent design; this release does not claim that capability.

## Groq page extraction

Configure `PULSE_GROQ_KEY` securely on the backend and worker (the standard
`GROQ_API_KEY` is also supported when running outside Compose). Never put a Groq key
in the app, GitHub Pages, or an `EXPO_PUBLIC_` variable. Create a key through Groq's
official console: https://console.groq.com/keys. Optional `PULSE_GROQ_MODEL` defaults
to `llama-3.3-70b-versatile`; choose a model available to your account that supports
JSON object responses. The integration uses the official OpenAI-compatible
chat completions contract documented in https://github.com/groq/groq-python.

Groq runs only when a supported collector has fetched a permitted page but found
no structured price. Existing robots, exact-host, redirect, size and challenge
checks remain in force. Ambiguous structured products/offers and blocked pages
never reach the fallback. Cross-retailer discovery uses this same extraction path.
Only anonymous public product-page text is sent to Groq; shopping sessions and
account cookies are not used.

The fallback requires one product heading and one complete visible line explicitly
labelled Selling price, Sale price, Our price, Deal price or Price with INR/₹/Rs.
The server computes integer paise from that original line; AI cannot supply or alter
the amount. Returned title, price quote and all supplied detail strings are checked
against page text. Shipping needs a separate complete INR fee line; conditional
offers remain quoted, never applied. Multiple prices, missing currency, fabricated
fields, malformed/truncated model responses and provider failures create no observation.
Quoted text is evidence, not independent verification of every extracted attribute;
condition/stock remain unknown and AI-assisted results stay unverified for matching.

The app shows the retained retailer price quote. History still starts with actual
observations; Groq does not create past prices or predict future prices. A page that
requires JavaScript, login, or lacks unambiguous evidence still needs an authorized
API/feed. No universal coverage or complete delivery/discount details are claimed.

`GET /providers/status` reports configuration only, without keys. It does not claim
a successful live provider call. Current environment has no securely configured
Groq key; automated tests use mock responses. GitHub Pages still requires a deployed
HTTPS API, database and worker. Backend CORS must allow `https://7899kk.github.io`.

## ExtraPe

The user identified `https://www.extrape.com/my-account`. This account page is not an API
specification, and the current environment cannot access the authenticated account.
No publisher ID, API URL, affiliate redirect pattern or tracking parameter is assumed.

Open your own logged-in account and consult ExtraPe's official help/support for the exact
publisher/partner ID and permitted app integration or product-link-generation workflow.
If you cannot find an ID, ask ExtraPe support whether one is required. Some services use
an account-based link creator rather than a separately exposed publisher ID; we have not
verified which applies here. Share official integration documentation or a generated link
with personal tracking values removed. Do not send your login password or credentials.

`outbound()` currently returns the original validated product URL and explicitly labels
tracking unavailable. A future documented provider must preserve the intended product,
validate the network's redirect host, handle failures by retaining the original URL, keep
keys server-side and honor click-recording consent. There is currently no affiliate click
tracking or commission claim. Recommendations never read commission information.

## Matching and buying advice

All supplied brand, model/GTIN, condition, delivery-area and variant conflicts are checked
before accepting any shared identifier. Empty or missing variants require review. No
text-only similarity makes an exact product. Shipping and conditional offers never reduce
the listed comparison price without separately verified eligibility.

History ranges are 7/30/90/180 days and all available. Statistics use actual observations
for one listing. Rules default to 5 observations spanning 7 days, a price no older than
24 hours, in-stock availability and an exact match. At least 10% below the retailer's
observed average yields Good time to buy; more than 10% above or a cheaper fresh exact
listing elsewhere yields Consider waiting; otherwise Fair price. Incomplete evidence
returns Insufficient data. Thresholds are configurable function parameters in `analyze()`.
No rule predicts future prices. In-app targets update after successful observations;
closed-app phone push, email and SMS are not configured.
