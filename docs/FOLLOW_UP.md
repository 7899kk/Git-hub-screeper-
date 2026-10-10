# Direct product validation and external history

Tests performed on 10 October 2026. See live-acceptance JSON files for exact check timestamps, API responses, actual observations, worker outcomes and import rejection reasons.

## Product checks

- Croma: https://www.croma.com/samsung-galaxy-a16-5g-8gb-ram-256gb-gold-/p/311654
  - Product: Samsung Galaxy A16 5G, 8GB RAM, 256GB, Gold.
  - Retrieved product HTML exposed an INR 20,499.00 Offer, but literal description newlines and an extra JSON closing brace caused the initial parser to discard the Product object.
  - Croma's own adapter now uses a constrained relaxed decoder for that observed defect. It still rejects unrelated trailing objects, ambiguity and invalid price/currency data. Storage and RAM remain separate.
  - The first full API acceptance run timed out. It is preserved in `live-acceptance.json`; a single retry with a 25-second Croma timeout is in `live-acceptance-croma-retry.json`. Neither successful fixture parsing nor a past HTTP fetch certifies uninterrupted access.
- IKEA: https://www.ikea.com/in/en/p/lack-side-table-white-10514792/
  - Product: LACK white 35×35 cm; SKU 105.147.92.
  - Live API returned INR 999 and `in_stock`; an immediate worker check produced a second real observation. Dimensions are now part of the variant, preventing 35×35 and 55×55 tables from being merged.

These worker observations occurred minutes apart, not on invented prior days. Monitoring remains interval-based and requires a running host worker; refresh is not a promise of instant retailer updates.

## Buyhatke comparison

Verified public browser page:
https://buyhatke.com/croma-samsung-galaxy-a16-5g-8gb-ram-256gb-gold-price-in-india-71-62051

The live browser displayed INR 20,499 for the same named Samsung variant and a claimed recorded low of INR 18,499. Its Max chart showed a long tracking period. Search-indexed content was older and showed INR 19,999 as its low; it must not replace the current browser observation.

Buyhatke's outgoing Croma link retained product number 311654 but used an inconsistent gas-stove slug. This warrants identity checking before data integration. We did not obtain a downloadable, timestamped history export or an authorized API response. Therefore, no guessed points or Buyhatke summary minimum were inserted into our recorded history. A chart image and an undated minimum are not a dated price dataset.

## External source history

The included MIT-attributed GitHub CSV offers a small set of older Amazon/Flipkart records. Its importer accepted 27 structurally valid platform rows and rejected missing/truncated rows. Imported timestamps have no specified timezone. Every accepted row is independently unverified and shown separately from the collector's history, with source attribution and grouped source-record charts. Identical product URLs with different inferred variants are kept in different chart groups.

These records do not contain past prices for the Croma/IKEA benchmark products. To populate those older histories, obtain a dated export or documented provider feed for those exact listings and variants. Source histories should be validated, attributed and retained separately until their accuracy and identity are established.

## Regression verification

50 automated tests pass, including Croma malformed JSON, trailing-object rejection, RAM/storage distinctions, furniture dimensions, import deduplication, invalid product URLs, and proof that imports cannot change live prices or jobs. JavaScript syntax and Python compilation also pass. Full browser QA of our app and Android device testing remain unperformed.
