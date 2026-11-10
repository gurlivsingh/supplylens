[← Back to README](../README.md)

# Data card: SupplyLens synthetic fixture v1

| | |
|---|---|
| Origin | Hand-authored by Team AlphaFire, November 2026. No scraping, no TBO data, no customer data. |
| License | MIT, same as the code. Free to redistribute. |
| Geography / language | Dubai (fictional properties and operators), English only |
| Suppliers | Atlas, Beacon, Corsa (fictional) with deliberately different naming, units and completeness |
| Images | None. The gallery shows labelled synthetic placeholders identified by a hash, so the de-duplication logic can be demonstrated without image rights. |
| Clock | Fixed demo time: 2026-12-15 10:00 (+04:00). Freshness limit: 36 h. |
| Query context | Hotels: check-in 2026-12-20, 2 nights, 1 room. Experiences: 2026-12-21. All offers belong to this context. |
| FX | One snapshot: 1 USD = 3.6725 AED, as of 2026-12-15 06:00 |

## Counts

| | Hotels | Sightseeing |
|---|---|---|
| Supplier records | 9 | 10 |
| True canonical entities (per labels) | 6 | 7 |
| Room / configuration variants | 11 rooms | 10 configurations |
| Offers | 12 (1 in USD) | 10 |
| Labelled identity pairs | 9 (4 match, 5 distinct; 3 of them hard negatives) | 9 (3 match, 6 distinct; 5 of them hard negatives) |
| Ranking intents | 3 validation + 5 test | 3 validation + 5 test |

## Deliberate difficulties

- Abbreviations ("Htl", "Rd"), a "The" prefix, phone number formats, and room sizes given in sqft vs m².
- The same hotel chain in two neighbourhoods; a similar name on a different street number.
- A conflicting star rating; descriptions and phone numbers missing.
- A bed type described as "subject to availability".
- A pickup safari vs the same operator's self-transfer safari; standard vs premium access; the same route from different operators, with and without a meal.
- A missing operator.
- A tax-exclusive price, an unknown cancellation policy, a stale price, an unavailable offer, and a foreign-currency offer.

## Labels and splits

Identity truth was written independently of the matcher. Ranking grades (0-3) were written before scores were inspected. The validation intents were used while the ranker was being designed. The test intents were written in one pass and were not used for tuning afterwards; their results include a known weakness (generic query words).

## Known biases and limits

The benchmark is very small (tens of records) and was written by the same team that built the matcher, so it is easier than real feeds. The reliability figures are synthetic, and Corsa deliberately has no history. Results describe this fixture only.
