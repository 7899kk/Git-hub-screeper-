# Preview PricePulse on GitHub

The new Expo app is live-only. Public frontend hosting does not run the FastAPI
collector service or provide retailer credentials. Missing live prices remain unavailable.

## View the interface now

These screenshots were captured from the actual running app in a phone-sized browser.
They contain no fabricated prices.

<img src="preview/home.png" alt="PricePulse home screen" width="360" />
<img src="preview/find.png" alt="Product-link input screen" width="360" />
<img src="preview/stores.png" alt="Retailer integration directory" width="360" />

## Interactive GitHub Pages preview

The Pages artifact is exported with the repository subpath and includes all main screen
entry points, a 404 fallback for dynamic product routes, and `.nojekyll` for Expo assets.
It is the same React Native web app; no demo dataset is added. The retailer directory
can display declared integrations with Setup required even before a backend is connected.

**Live preview:** https://7899kk.github.io/Git-hub-screeper-/

The site is published from the `gh-pages` branch, root directory. Its public HTML and
JavaScript returned HTTP 200, and its live onboarding, navigation, retailer directory,
refresh and product-link screen were tested using verified HTTPS responses.

The **Build mobile web preview** workflow checks the code and uploads a reusable
`pricepulse-github-pages` artifact. It does not deploy from `main`, which GitHub's
current Pages environment rules prohibit. Publish updated static files to `gh-pages`,
the approved deployment branch. No environment protection rules were removed.

To connect actual prices, set the non-secret repository variable
`PRICEPULSE_PREVIEW_API_URL` to the deployed HTTPS FastAPI backend and allow the Pages
origin in backend `PULSE_CORS_ORIGINS`. Never use a provider key as a public repository
variable or Expo public environment variable. GitHub Pages cannot host Python or PostgreSQL.

Groq-assisted extraction is implemented in the backend. Settings shows provider
configuration after connecting a live service, and product details show the actual
retailer price quote. No Groq key is configured in this environment yet; no live
Groq-price request has been verified. See [integration instructions](MOBILE_INTEGRATIONS.md#groq-page-extraction).

Local reproducible build:

```sh
cd mobile
npm ci
npm run build:pages
```

Publishing the `gh-pages` branch activated the repository's Pages site. The GitHub
integration could not create the site or alter its environment rules through the API;
the supported branch publishing route succeeded. The live browser preview remains
separate from backend hosting and a signed Android release.
