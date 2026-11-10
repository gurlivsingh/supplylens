# Risk and security note

## Boundaries

- **No bookings or payments.** There are no card fields and no supplier write calls. A production flow would re-check price and availability and ask the user to confirm before any booking.
- **No secrets.** The app needs no API keys or environment variables. `.env` is git-ignored in case one is added later.
- **No personal data.** There are no accounts and nothing is stored about users. Reviewer notes are capped at 200 characters and held in memory.
- **Synthetic data only.** This is labelled in the UI, the README and the data card.

## Input handling

- `vertical`, `sort` and `decision` are checked against fixed values (FastAPI/Pydantic `Literal`); anything else returns 422.
- Query text is limited to 200 characters, `adults` to 1-8, and record ids to 40 characters. An unknown record returns 404.
- The UI escapes every server value before inserting it into HTML.
- The review endpoint has no authentication. That is acceptable for a public demo with synthetic data and an in-memory state that resets on restart. A real deployment would need reviewer authentication and persistent audit storage.

## Decision risks and mitigations

| Risk | Mitigation |
|---|---|
| Two different products merged | Hard conflicts block auto-linking; mixed evidence goes to review; cluster-wide compatibility; regression tests for each hard negative |
| A cheaper but incomparable offer shown as best | Eligibility before scoring; tax-exclusive, stale, unavailable or unknown-policy offers can't win |
| Missing data read as an inclusion | Unknown values stay unknown and are labelled; no inference from a missing exclusion |
| A new supplier penalised | Neutral prior with the sample size shown |
| Over-claiming results | Metrics carry sample counts and baselines; the synthetic label is everywhere |

## Operational notes (Render free tier)

The service sleeps when idle, so the first request takes ~30-50 s. Restarts clear reviewer decisions. For the finale, use a local run or the recorded demo video as a backup.
