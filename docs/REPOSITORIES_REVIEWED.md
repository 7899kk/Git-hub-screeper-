# Price-comparison repositories reviewed

Requested topic page: https://github.com/topics/price-comparison?l=php&o=asc&s=updated

Reviewed 10 October 2026. The page sorts by least recently updated; it is not a tested ranking of current scraper reliability. Code availability does not prove retailer coverage or provide an existing historical database.

| Repository | What the repository documents | Decision |
|---|---|---|
| https://github.com/amoldalwai/Price_Comparison_Website | PHP Simple DOM search across Amazon, Flipkart and Snapdeal; topic page shows 2020 update | Architecture reference only. Not a verified current all-platform adapter; no license displayed on the reviewed root. No code copied. |
| https://github.com/jez500/pricebuddy | Self-hosted URL tracking, scheduled price history, comparisons, API/CLI; Laravel and Docker | Strong reusable system reference. It attempts pages and configurable strategies; not proof of current Indian-source access. LICENSE.md says GPL-3.0 with modifications; preserve and review the complete terms before incorporating its implementation. No code copied. |
| https://github.com/FatimaAsif1211/omni-price-tracker | Laravel/Node/MySQL aggregation for PriceOye, Daraz, Naheed in Pakistan | Multi-provider design reference; not a replacement for Indian retailer connectors. No code copied. |

The original PricePulse connector interface, source-isolated collection and exact-variant comparison remain in this repo. We added authenticated `/api/v1/` endpoints and a small JavaScript SDK rather than merging unrelated PHP applications. See CONNECT_YOUR_APP.md for the actual app connection. The backend must run on a server; a GitHub repo URL is not the API base URL.

These projects were researched through their primary README, topic listings and license where available. Third-party runtime compatibility and live retailer access were not verified. We have not imported their scraped records or promised all-platform support.
