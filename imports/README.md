# Attributed external history

`datawithsaurabh-price-history.csv` was retrieved from:
https://github.com/datawithsaurabh/Price-Tracker/blob/main/Price-Tracker/data/price_history.csv

The repository's MIT license is preserved in `datawithsaurabh-LICENSE.txt`. Only the CSV and license were copied; no scraper code was reused.

Run `python -m backend.import_history`. This layout-specific importer creates separate `sourced_history` records. It keeps source identity, file hash, license, original local timestamp, original product URL, title, inferred attributes and an `external_unverified` status. It never manufactures a timezone, overwrites a current price, schedules a job, triggers an alert, or assumes cross-platform rows with the same source Product_ID are equivalent variants.

The imported dataset contains a small set of dated Amazon/Flipkart records, not a complete catalogue or independently verified retail history. 27 platform records passed structural validation; missing or truncated records are rejected. Structurally accepted records still need quality review. The source contains examples of mismatched titles/URL slugs and differing cross-platform variants.

Another inspected source, `itsCharan05/E-Commerce-Price-Scraper/price_history.csv`, was not imported because its product names were `Unknown` and URLs were category/search pages rather than specific products. Its README also documents a mock fallback. Those rows cannot establish trustworthy history for a particular listing.
