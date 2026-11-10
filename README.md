# SupplyLens

**Team AlphaFire · TBO VoyageHack 4.0 · Multi Supplier Optimization**

> SupplyLens makes fragmented hotel and sightseeing inventory comparable without erasing what makes each option different.

SupplyLens is an explainable multi-supplier inventory layer for **Hotels** and **Sightseeing**. It

1. **groups the same underlying product** across suppliers (one listing per hotel or experience, not one per feed),
2. **keeps meaningful differences apart** (room bed types, meal plans, pickup vs self-transfer, standard vs skip-the-line, cancellation terms),
3. **compares only genuinely comparable offers** (complete total price, same context, known policy, fresh availability), and
4. **ranks listings for the stated intent** with the reasons shown, and an audit trail for anything uncertain.

It is not a chatbot or a cheapest-price sorter. It does not make bookings.

**Live demo:** https://supplylens-alphafire.onrender.com (Render free tier: the first request after idle can take ~30-50 s to wake up)

**All data is synthetic.** Suppliers (Atlas, Beacon, Corsa), properties, operators, prices, availability and reliability are fictional. See [docs/DATA_CARD.md](docs/DATA_CARD.md).

---

## Run it locally

Requires Python 3.11+.

```bash
git clone https://github.com/gurlivsingh/supplylens.git
cd supplylens
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn supplylens.app:app --reload
```

Open http://localhost:8000. API docs at http://localhost:8000/docs.

| Task | Command |
|---|---|
| Run tests (19 acceptance cases) | `pytest -q` |
| Run the offline evaluation | `python -m supplylens.evaluate` (writes `docs/evaluation_results.json`) |
| Reset reviewer decisions | restart the server (decisions are kept in memory on purpose for a deterministic demo) |

## What to try

| Story (master plan §14) | Where |
|---|---|
| 1. Hotel identity and enrichment: 3 supplier records of *Marina Pearl* become 1 property, with sourced fields, a flagged star-rating conflict and 2 duplicate images removed | Search → Hotels → `marina hotel with breakfast, free cancellation` |
| 2. Room and policy preservation: *Deluxe King* (32 m²) = *Deluxe Room King Bed* (344 sqft); *Deluxe Twin* stays separate; "Double or Twin, subject to availability" is only a *possible* match | Same property → Room mapping |
| 3. Sightseeing near-duplicate rejection: the pickup safari (2 suppliers) stays separate from the self-transfer safari | Sightseeing → `evening activity with hotel pickup and flexible cancellation` |
| 4. Better offer choice: the cheapest headline price (Corsa, AED 1,580) loses because taxes are excluded; an unknown cancellation policy is never called flexible | Marina Pearl → Supplier offers |
| 5. Relevant listing order: the dinner cruise outranks a cheaper cruise without dinner | Sightseeing → `dinner cruise` |
| 6. Trust under uncertainty: *Oasis Palm Residences* vs *Residence* (same name, different street number) waits in the review queue; a 53-hour-old price is excluded | Review queue · Hidden by hard constraints |

The **Raw supplier feed** tab shows the baseline (19 listings as feeds deliver them). The **Evidence** tab recomputes every metric live.

## How it works

```
supplier records → normalize (names, units, phones, addresses, FX)
  → candidate blocking (hotels ≤2 km apart, experiences sharing an attraction)
  → identity decision: match / review / distinct, with evidence and hard conflicts
  → cluster-wide compatibility check (A~B and B~C does not prove A~C)
  → variants: room families (occupancy, bed, size in m², view) · experience configurations
  → offers: eligibility (context, availability, freshness, complete price, required policy)
            → labels within comparable groups: cheapest comparable · most flexible · balanced pick
  → listing ranking: hard constraints → relevance → value, policy fit, freshness, reliability
  → explanations + reviewer decisions with audit log
```

Ranking weights (documented, not learned): relevance 0.40, value 0.25, policy fit 0.15, data freshness 0.10, evidenced reliability 0.10. Secondary signals are scaled by relevance, so a cheap but off-intent listing cannot outrank a relevant one. A supplier with no history gets a neutral 0.5, not a penalty.

More: [docs/SOLUTION.md](docs/SOLUTION.md).

## Results on the synthetic benchmark

Small, hand-authored benchmark: exploratory evidence, not production performance. Full report: [docs/EVALUATION.md](docs/EVALUATION.md).

| | Hotels | Sightseeing |
|---|---|---|
| Labelled pairs (true matches) | 9 (4) | 9 (3) |
| Harmful merges: name-only baseline → SupplyLens | 3 → **0** | 3 → **0** |
| Auto-link precision: baseline → SupplyLens | 57% → **100%** | 40% → **100%** |
| Recall, auto-only / reviewer-assisted | 100% / 100% | 67% / 100% |
| Held-out ranking NDCG@k: raw feed / cheapest eligible / SupplyLens (5 intents) | 0.62 / 0.96 / **0.96** | 0.80 / 0.88 / **0.97** |
| Recommended offers breaking eligibility rules | 0 of 14 | 0 of 29 |

## Repository layout

```
supplylens/engine.py     matching, room mapping, enrichment, offers, ranking, review
supplylens/evaluate.py   offline evaluation (baselines, NDCG, safety checks, latency)
supplylens/app.py        FastAPI: /api/search, /api/entity, /api/review, /api/eval, UI
web/                     single-page UI (no build step)
data/                    synthetic fixtures and labels
tests/                   acceptance tests from the master plan
docs/                    solution note, data card, evaluation, demo guide, risk note
submission/              decks (PDF/PPTX) and videos for both rounds
render.yaml              Render blueprint
```

## Deploy on Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/gurlivsingh/supplylens)

The repo includes `render.yaml`. Click the button above, or in Render: **New → Blueprint → connect this repository → Apply**. Or create a Web Service manually:
build `pip install -r requirements.txt`, start `uvicorn supplylens.app:app --host 0.0.0.0 --port $PORT`, health check `/healthz`. No secrets or environment variables are required.

## Scope and limits

- No bookings, payments, live supplier APIs or customer data.
- Reviewer decisions live in memory and reset on restart.
- Lexical relevance only: generic words such as "tour" or "experience" match every listing (visible in the test intents). Semantic matching is stretch work.
- Thresholds were set by hand on the fixture; the benchmark is too small to tune or to claim conversion impact.

See [docs/RISK_SECURITY.md](docs/RISK_SECURITY.md).

## Credits and disclosure

Built by Team AlphaFire for TBO VoyageHack 4.0. AI coding assistance (Claude) was used to write code, documentation and submission material, which the team reviewed. Fonts: Inter, Source Serif 4, JetBrains Mono (SIL Open Font License, via Google Fonts). No third-party data or images are included.

License: MIT.
