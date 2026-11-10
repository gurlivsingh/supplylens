[← Back to README](../README.md)

# Solution note

## The brief, mapped

| TBO brief requirement | SupplyLens response | Code |
|---|---|---|
| Identify duplicate or equivalent sightseeing products | Same attraction + same operator + compatible configuration → match; missing operator → review | `engine.decide_experience` |
| Preserve inclusions, transfers, meals, options, duration, access, cancellation | Any difference in pickup, meal, access, private/shared, slot, or >15% duration is a hard conflict; cancellation stays on each offer | `EXP_ATTRS`, `evaluate_offer` |
| Consolidate duplicate hotel listings | Name similarity + same street number and street + phone + distance; same chain in another area stays separate | `engine.decide_hotel` |
| Map equivalent room types | Occupancy, bed, size (sqft→m²), view; "subject to availability" bed → *possible*, never guaranteed | `engine.room_relation` |
| Enrich content and images | Field-level provenance; majority value, ties → most recent; conflicts flagged; image dedupe by hash with sources kept | `engine.enrich` |
| Compare bookable options on price, availability, cancellation, payment, reliability | Eligibility first, then labels within a room family; dominance needs all dimensions known | `evaluate_offer`, `label_offers`, `dominates` |
| Rank listings for relevance and recommendation | Hard constraints → relevance → value, policy, freshness, reliability; reasons shown | `engine.search` |

## Three separate decisions

1. **Identity:** is this the same property or product? (`match` / `review` / `distinct`)
2. **Equivalence:** are these room variants interchangeable? (`equivalent` / `possible` / `distinct`)
3. **Recommendation:** which eligible offer or listing is best for the stated need?

A "yes" to identity never implies a "yes" to equivalence. A refundable room and a prepaid non-refundable room can sit in the same room family, but they remain separate offers.

## Records

- **Canonical entity:** a cluster of supplier records. Its id is the smallest member record id.
- **Variant:** a hotel room family, or an experience configuration (each experience entity is one configuration; a different configuration is a different product within the same attraction family).
- **Offer:** a supplier price for a variant in a declared context (dates, party). It carries the currency, whether taxes are included, the meal plan, the refund policy and deadline, the payment timing, availability and the fetch time.

## Safety rules (each one has a test)

- No auto-merge on name similarity alone. A hard conflict blocks the merge, and mixed evidence goes to review.
- A cluster only grows when every new pair is compatible with every existing member.
- Unknown stays unknown: a missing policy is shown as "policy not supplied", never as free cancellation, and a missing field is never invented.
- A tax-exclusive or stale price can't win on price. An unavailable offer is never recommended.
- Currency is converted with one documented FX snapshot. The original amount stays visible.
- A supplier with no history gets a neutral prior, labelled as such.
- Reviewer decisions are reversible and every change is written to the audit log.

## Ranking

```
score = 0.40·relevance + relevance · (0.25·value + 0.15·policy_fit + 0.10·freshness + 0.10·reliability)
```

Relevance is the share of query terms found in the entity's text and structured inclusions. Requirements stated in the query ("flexible", "breakfast", "pickup") or a named area ("marina") become hard filters. Listings that a filter removes are listed under "Hidden by hard constraints" together with the reason. The weights come from master plan §11 and were not learned; there is no booking history to learn from.

## Architecture

One FastAPI process, JSON fixtures held in memory, and a static single-page UI. There's no database, queue or model service; the plan's guidance is to add those only when a measured need justifies them. Searches are deterministic and take under a millisecond in-process on the fixture.
