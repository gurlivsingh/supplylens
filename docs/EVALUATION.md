# Evaluation report

Reproduce with `python -m supplylens.evaluate`. It writes [evaluation_results.json](evaluation_results.json), and the live app's **Evidence** tab recomputes the same numbers. Dataset: synthetic fixture v1 ([DATA_CARD.md](DATA_CARD.md)). Hotels and Sightseeing are reported separately, never combined.

## Identity matching

The baseline links two records when their name similarity (token Jaccard) is at least 0.5. SupplyLens links records only through the full decision plus the cluster compatibility check. "Assisted recall" counts true matches that were sent to review, assuming the reviewer decides correctly.

| Hotels (9 pairs, 4 true) | Auto-links | Precision | Auto recall | Assisted recall | Sent to review | Harmful merges |
|---|---|---|---|---|---|---|
| Name-only baseline | 7 | 57% | 100% | 100% | 0 | 3 |
| SupplyLens | 4 | 100% | 100% | 100% | 1 | **0** |

| Sightseeing (9 pairs, 3 true) | Auto-links | Precision | Auto recall | Assisted recall | Sent to review | Harmful merges |
|---|---|---|---|---|---|---|
| Name-only baseline | 5 | 40% | 67% | 67% | 0 | 3 |
| SupplyLens | 2 | 100% | 67% | 100% | 1 | **0** |

The baseline's harmful merges were: the same chain in Deira and Jumeirah (twice), Oasis Palm on two different street numbers, the pickup safari with the self-transfer safari, standard with premium tower access, and two different operators' cruises with and without dinner.

Candidate recall (true matches that survive blocking) is 100% in both verticals.

## Offer safety

Every recommended "best offer" across all 16 intents was checked against the eligibility, complete-price, freshness and availability rules. There were **0 violations** (14 hotel and 29 sightseeing recommendations checked).

## Listing ranking (mean NDCG@k, k = min(5, eligible pool))

| | Raw supplier order | Cheapest eligible | SupplyLens |
|---|---|---|---|
| Hotels, validation (3) | 0.395 | 0.836 | 0.938 |
| Hotels, test (5) | 0.615 | 0.962 | 0.962 |
| Sightseeing, validation (3) | 0.750 | 0.917 | 1.000 |
| Sightseeing, test (5) | 0.802 | 0.883 | 0.970 |

- The raw supplier order is penalised for duplicate crowding: a repeated listing of the same entity earns no gain.
- The cheapest-eligible baseline applies the same hard constraints and text match, sorted by price. It is a valid comparison, not an intentionally invalid one.
- On held-out hotels SupplyLens ties with cheapest-eligible. On this fixture most hotel queries leave only one or two eligible matches, so ordering has little room to help.
- **Observed failure:** "souk walking tour" and "camel ride experience" match every listing through the generic words "tour" and "experience". The ranking still put the right items first, but the result lists are crowded. We did not tune this away on the test set; it is listed as next work.

## Latency

In-process `search()` on the fixture took a median of ~0.3-0.6 ms, with a p95 under 1 ms (30 warm runs). This excludes the network and Render's free-tier cold start (~30-50 s after idle).

## What this does not show

- Real-feed performance, scale, or any conversion, margin or cancellation impact. Those need an authorized pilot with real supplier data.
- Statistical confidence: the samples are tiny. Zero harmful merges observed on 9 pairs is not proof of zero risk.
