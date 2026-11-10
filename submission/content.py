"""Slide and narration content for both rounds. Rendered by build.py."""

REPO = "github.com/gurlivsingh/supplylens"
LIVE = "supplylens-alphafire.onrender.com"


def flow(steps):
    return '<div class="flow">' + "".join(f'<div class="step"><b>{a}</b><span>{b}</span></div>' for a, b in steps) + "</div>"


LAYERS = """
<div class="layers">
  <div class="layer"><p class="k">Entity</p><h3>Marina Pearl Hotel</h3><p>3 supplier records: “Marina Pearl Hotel” · “Marina Pearl Htl &amp; Spa” · “The Marina Pearl”</p></div>
  <div class="arrow">→</div>
  <div class="layer"><p class="k">Variants</p><h3>Room families</h3><p>Deluxe King 32 m² (= 344 sqft) · Deluxe Twin · Superior King 45 m² · “Double or Twin, subject to availability” → only <i>possible</i></p></div>
  <div class="arrow">→</div>
  <div class="layer"><p class="k">Offers</p><h3>Comparable only</h3><p>AED 1,720 breakfast, free cancellation ✓<br>AED 1,650 non-refundable<br><s>AED 1,580</s> taxes excluded: not comparable</p></div>
</div>
<div class="layers small">
  <div class="layer"><p class="k">Sightseeing</p><h3>Red Dune evening safari</h3><p>Same operator and itinerary from 2 suppliers → one product</p></div>
  <div class="arrow">≠</div>
  <div class="layer"><p class="k">Kept separate</p><h3>Same safari, self-transfer</h3><p>No hotel pickup, 5 h vs 6 h: a different product, never priced against the pickup version</p></div>
</div>"""

IDEA = [
    {"layout": "cover",
     "html": f"""<p class="kicker">TBO VoyageHack 4.0 · Multi Supplier Optimization · Team AlphaFire</p>
     <h1 class="display">SupplyLens</h1>
     <p class="lead">Make hotel and sightseeing inventory comparable, without losing what makes each option different.</p>""",
     "say": "Hi, we are Team AlphaFire. Our idea for Multi Supplier Optimization is SupplyLens. It makes hotel and sightseeing inventory from many suppliers comparable, without erasing what makes each option different."},
    {"layout": "content", "kicker": "Content 1 of 2 · Potential impact and innovation",
     "html": f"""<h1>One trustworthy listing per product. Every meaningful option kept.</h1>
     <div class="cols3">
       <div class="card"><p class="k">The problem</p><p>The same hotel arrives from several suppliers under different names, so listing pages fill with duplicates. Naive deduplication goes the other way: it merges a pickup tour with a self-transfer one, or compares a tax-exclusive price with a full one.</p></div>
       <div class="card wide">{LAYERS}</div>
       <div class="card"><p class="k">Impact</p><ul><li>Cleaner listing pages: one card per product, with supplier and variant counts</li><li>Price competitiveness: the best <i>eligible</i> offer, not the lowest headline</li><li>Fewer wrong merges, so fewer post-booking surprises</li></ul>
       <p class="k" style="margin-top:20px">Innovation</p><ul><li>Variant-safe consolidation</li><li>Traceable reasons and a reviewer path</li><li>One model for both verticals</li></ul></div>
     </div>""",
     "say": "Today the same hotel arrives from three suppliers under three names, and the listing page fills with duplicates. But naive deduplication is just as harmful. It merges a tour with hotel pickup into one without pickup, or compares a price without taxes against a full price. SupplyLens separates three things. The entity: the same physical hotel or the same experience. The variants: room families, transfers, meals, access. And the offers: each supplier's price and policy. So one listing per product, with every meaningful option kept. The innovation is variant-safe consolidation, the best eligible offer instead of the lowest headline price, and visible reasons for every decision."},
    {"layout": "content", "kicker": "Content 2 of 2 · Implementation, technical feasibility and adoption risk",
     "html": f"""<h1>Simple, deterministic, explainable, and safe to adopt.</h1>
     {flow([("1 · Normalize", "names, units, phones, addresses, FX, with source kept"), ("2 · Match", "match / review / distinct with hard conflicts"), ("3 · Map variants", "rooms by occupancy, bed, size, view"), ("4 · Compare offers", "eligibility first: tax, freshness, policy"), ("5 · Rank and explain", "intent, value, policy fit, reliability"), ("6 · Review", "uncertain pairs, reversible, audited")])}
     <div class="cols2">
       <div class="card"><p class="k">Feasibility</p><ul><li>Python + FastAPI, no heavy infrastructure, millisecond searches</li><li>Rules and similarity over fields suppliers already send; no model training needed</li><li>An early end-to-end prototype already runs on synthetic data for both verticals</li></ul>
       <p class="k" style="margin-top:20px">Proof plan (per vertical)</p><p>Auto-link precision, harmful-merge suite, offer-correctness cases, and NDCG against raw-feed and cheapest-price baselines. Early synthetic check: <b>0</b> harmful merges vs <b>3</b> for name-only matching (9 labelled pairs each).</p></div>
       <div class="card"><p class="k">Adoption risks and answers</p>
       <table><tr><td><b>False merges</b></td><td>Hard conflicts block them; mixed evidence goes to a review queue; every decision is reversible</td></tr>
       <tr><td><b>Missing data</b></td><td>Unknown stays unknown, with field-level sources; never shown as “included”</td></tr>
       <tr><td><b>Stale or partial prices</b></td><td>Excluded from “best”, with the reason shown</td></tr>
       <tr><td><b>Integration</b></td><td>Offline evaluation on TBO sample feeds, then a controlled pilot</td></tr></table></div>
     </div>""",
     "say": "Implementation is a deterministic pipeline. Normalize names, units and currencies, keeping the source of every field. Match records into match, review, or distinct, where hard conflicts like a different street number, a missing pickup, or premium access block a merge. Map room variants by occupancy, bed, size and view. Compare only eligible offers, with complete prices, fresh availability, and the required policy. Then rank for the traveller's intent and explain why. It runs on Python and FastAPI with no heavy infrastructure, and an early prototype already works end to end on synthetic data. For adoption, false merges go to a reversible review queue, missing data stays visibly unknown, and stale prices can never win. We will prove it per vertical with precision, harmful-merge tests and ranking baselines. In an early synthetic check, name-only matching made three harmful merges per vertical. SupplyLens made zero."},
    {"layout": "cover",
     "html": f"""<p class="kicker">Thank you</p>
     <h1 class="display">Comparable, not flattened.</h1>
     <p class="lead">Team AlphaFire · SupplyLens<br><span class="mono">{REPO}</span></p>""",
     "say": "SupplyLens. Comparable, not flattened. Thank you."},
]


def screen(img, caption):
    return f'<figure class="shot"><div class="screen"><img src="assets/{img}.png" alt=""></div><p class="cap">{caption}</p></figure>'


PROTO = [
    {"layout": "cover",
     "html": f"""<p class="kicker">TBO VoyageHack 4.0 · Multi Supplier Optimization · Team AlphaFire · Prototype</p>
     <h1 class="display">SupplyLens</h1>
     <p class="lead">An explainable multi-supplier inventory layer for Hotels and Sightseeing: one trustworthy listing per product, distinct options kept, and the best eligible offer with its reasons.</p>
     <p class="mono">{REPO} · {LIVE}</p>""",
     "say": "This is SupplyLens, by Team AlphaFire, for Multi Supplier Optimization. It is an explainable inventory layer for hotels and sightseeing. It gives one trustworthy listing per product, keeps distinct options, and recommends the best eligible offer with its reasons."},
    {"layout": "split", "kicker": "2 · The problem",
     "html": f"""<div><h1>Feeds repeat products and hide differences.</h1>
     <ul class="big"><li>Marina Pearl arrives three times under three names</li><li>A pickup safari and a self-transfer safari look identical by name</li><li>The lowest headline price can exclude taxes, or have no refund at all</li><li>Name-only deduplication causes 3 harmful merges per vertical on our benchmark</li></ul></div>
     {screen("raw", "Raw supplier feed: 19 listings, synthetic")}""",
     "say": "Supplier feeds repeat the same product and hide the differences that matter. Here, the same hotel arrives three times under three names. A safari with hotel pickup and one without look identical by name. And the cheapest headline price may exclude taxes or have no refund at all."},
    {"layout": "content", "kicker": "3 · Approach and differentiation",
     "html": f"""<h1>Entity → variants → offers, with safeguards.</h1>{LAYERS}
     <div class="cols3 tight"><div class="card"><b>Variant-safe consolidation</b><p>Identity never erases bed, meal, transfer, access or policy.</p></div>
     <div class="card"><b>Best eligible, not lowest</b><p>Tax-exclusive, stale, unavailable or unknown-policy offers can't win.</p></div>
     <div class="card"><b>Traceable and reversible</b><p>Reasons on every card; uncertain pairs wait for a reviewer, and every decision is logged.</p></div></div>""",
     "say": "Our approach separates three decisions. Identity: is it the same product. Equivalence: are these room or activity variants interchangeable. And recommendation: which eligible offer is best for this traveller. Identity never erases bed, meal, transfer, access or policy differences."},
    {"layout": "content", "kicker": "4 · Architecture and data governance",
     "html": f"""<h1>One small service, deterministic and auditable.</h1>
     {flow([("Ingest", "supplier ids, raw records and timestamps kept"), ("Normalize", "abbreviations, sqft→m², phones, FX snapshot"), ("Block", "hotels ≤2 km · experiences by attraction"), ("Decide", "match / review / distinct with evidence and conflicts"), ("Cluster", "every pair must be compatible"), ("Offers and rank", "eligibility → labels → weighted, explained score")])}
     <div class="cols2"><div class="card"><p class="k">Stack</p><p>Python 3.12 · FastAPI · in-memory JSON fixture · single-page UI without a build step · Render blueprint. 19 automated tests. No secrets, no customer data, no bookings.</p></div>
     <div class="card"><p class="k">Governance</p><p>Field-level provenance; unknown stays unknown; synthetic data labelled on every screen; reviewer overrides in an append-only audit log; images are placeholders, deduplicated by hash.</p></div></div>""",
     "say": "Architecture is one small FastAPI service. Records are normalized, blocked into candidates, and decided as match, review or distinct, with evidence and conflicts. A cluster only grows if every pair is compatible. Offers are checked for eligibility before any score. Everything is deterministic, sourced, and auditable."},
    {"layout": "split", "kicker": "5 · Hotel workflow",
     "html": f"""<div><h1>3 records → 1 property. 4 room families kept.</h1>
     <ul class="big"><li>Sourced fields; the star-rating conflict is flagged, not hidden</li><li>2 duplicate images removed, attribution kept</li><li>32 m² = 344 sqft → same family; King ≠ Twin</li><li>“Subject to availability” bed → only <i>possible</i></li></ul></div>
     {screen("hotel_detail", "Marina Pearl: sourced content and gallery")}""",
     "say": "For hotels, three supplier records become one property. Every field shows which supplier it came from, and the star rating conflict is flagged rather than hidden. Duplicate images are removed with attribution kept. Room sizes in square feet and square metres are normalized, so the King rooms match, while Twin stays separate, and a bed that is subject to availability is only a possible match."},
    {"layout": "split", "kicker": "6 · Sightseeing workflow",
     "html": f"""<div><h1>Same product merged. Look-alike kept apart.</h1>
     <ul class="big"><li>Red Dune safari: 2 suppliers, same operator and itinerary → 1 product</li><li>Self-transfer version: pickup and duration differ → separate, with the reason shown</li><li>Standard vs skip-the-line tower access: separate</li><li>Missing operator → review queue, not a guess</li></ul></div>
     {screen("exp_detail", "Red Dune evening safari: configuration preserved")}""",
     "say": "For sightseeing, the Red Dune safari from two suppliers becomes one product. The self-transfer version from the same operator stays separate, because pickup and duration differ, and the screen says why. Standard and skip-the-line access stay separate too, and a record with a missing operator goes to review instead of being guessed."},
    {"layout": "split", "kicker": "7 · Supplier comparison and listing ranking",
     "html": f"""<div><h1>Best eligible offer, then relevant order.</h1>
     <ul class="big"><li>Cheapest headline AED 1,580 loses: taxes excluded</li><li>Unknown policy is never “free cancellation”</li><li>Labels compare within one room family: cheapest comparable · most flexible · balanced pick</li><li>Score = 0.40 relevance + relevance × (value, policy fit, freshness, reliability); new suppliers get a neutral prior</li></ul></div>
     {screen("hotel_offers", "Offers: ineligible rows struck through, with the reason")}""",
     "say": "Offers are compared only when they are comparable. The cheapest headline price loses here because taxes are excluded, and an unknown policy is never shown as free cancellation. Listings are ranked with a documented score where relevance comes first, so a cheap but off-intent result cannot win. A new supplier gets a neutral prior, not a penalty."},
    {"layout": "content", "kicker": "8 · Evaluation (synthetic benchmark, per vertical)",
     "html": """<h1>Zero harmful merges. Better ranking than both baselines.</h1>
     <div class="cols2">
     <div class="card"><p class="k">Identity matching · 9 labelled pairs per vertical</p><table class="num">
     <tr><th></th><th>Hotels baseline</th><th>Hotels SupplyLens</th><th>Sightseeing baseline</th><th>Sightseeing SupplyLens</th></tr>
     <tr><td>Auto-link precision</td><td>57%</td><td><b>100%</b></td><td>40%</td><td><b>100%</b></td></tr>
     <tr><td>Harmful merges</td><td>3</td><td><b>0</b></td><td>3</td><td><b>0</b></td></tr>
     <tr><td>Recall, auto / assisted</td><td>100 / 100%</td><td>100 / 100%</td><td>67 / 67%</td><td>67 / 100%</td></tr>
     <tr><td>Sent to review</td><td>0</td><td>1</td><td>0</td><td>1</td></tr></table>
     <p class="note">Baseline: name similarity ≥ 0.5. Candidate recall 100%. Offer rules: 0 violations in 43 recommendations. p95 search &lt; 1 ms in-process.</p></div>
     <div class="card"><p class="k">Listing ranking · mean NDCG@k, held-out test intents (5 per vertical)</p><table class="num">
     <tr><th></th><th>Raw feed</th><th>Cheapest eligible</th><th>SupplyLens</th></tr>
     <tr><td>Hotels</td><td>0.62</td><td>0.96</td><td><b>0.96</b></td></tr>
     <tr><td>Sightseeing</td><td>0.80</td><td>0.88</td><td><b>0.97</b></td></tr></table>
     <p class="note">Validation intents (3 per vertical) were used for design: hotels 0.94, sightseeing 1.00. Small hand-labelled synthetic benchmark: exploratory, not production performance. Known failure: generic words like “tour” match every listing.</p></div></div>""",
     "say": "We measured it on a small, hand-labelled synthetic benchmark, separately per vertical. Name-only matching made three harmful merges in each vertical. SupplyLens made zero, with one uncertain pair per vertical sent to review. On held-out ranking intents, SupplyLens matched or beat both the raw feed and the cheapest-price baseline. These samples are small, so we treat them as exploratory, and we report the failures too."},
    {"layout": "content", "kicker": "9 · Business value, feasibility and integration path",
     "html": f"""<h1>A low-risk path into TBO’s supplier pipeline.</h1>
     <div class="cols3"><div class="card"><p class="k">Value mechanisms</p><ul><li>Fewer duplicate cards → faster, clearer choice</li><li>Best eligible offer surfaced → price competitiveness</li><li>Policy differences visible → fewer post-booking disputes</li><li>Review queue focuses human effort on the uncertain few</li></ul></div>
     <div class="card"><p class="k">Feasibility</p><ul><li>Uses fields suppliers already send</li><li>Deterministic, under 1 ms per search on the fixture</li><li>No training data or GPU needed</li><li>Runs as a sidecar service before the listing page</li></ul></div>
     <div class="card"><p class="k">Proposed pilot</p><ol><li>Offline run on authorized TBO sample feeds, one city</li><li>Label 200 pairs; freeze thresholds</li><li>Shadow-rank against the live order</li><li>Controlled A/B on a slice of traffic; measure conversion there, not here</li></ol></div></div>""",
     "say": "The business value comes from clear mechanisms. Fewer duplicate cards, the best eligible offer surfaced, and policy differences made visible. It uses fields suppliers already send, needs no training data, and can run as a sidecar before the listing page. We propose a pilot: an offline run on authorized TBO feeds for one city, then shadow ranking, then a controlled test where conversion is actually measured."},
    {"layout": "content", "kicker": "10 · Recap, limitations and next step",
     "html": f"""<h1>Works today on synthetic data. Ready for a real-feed pilot.</h1>
     <div class="cols2"><div class="card"><p class="k">Works in the submitted build</p><ul><li>Hotel consolidation, enrichment, room mapping</li><li>Sightseeing matching with preserved configurations</li><li>Eligible-offer comparison and explained ranking</li><li>Review queue with audit log; live evaluation tab; 19 tests</li></ul></div>
     <div class="card"><p class="k">Not yet validated</p><ul><li>Real supplier feeds and scale</li><li>Lexical relevance only; no semantic or multilingual matching</li><li>Reviewer decisions held in memory; no authentication</li><li>No conversion claims without a live pilot</li></ul></div></div>
     <p class="ask"><b>Our ask:</b> authorized sample feeds for one destination, and a reviewer to label 200 pairs.</p>
     <p class="mono">{REPO} · {LIVE}</p>""",
     "say": "To recap. Hotel consolidation, room mapping, sightseeing matching, eligible-offer comparison, explained ranking and a review queue all work today, on synthetic data. Real feeds, scale and semantic matching are not yet validated, and we make no conversion claims. Our ask is authorized sample feeds for one destination, so we can run the pilot. Thank you."},
]

# Demo video: screen-led walkthrough of the running app (~3 minutes)
DEMO = [
    {"layout": "cover", "html": f"""<p class="kicker">Prototype walkthrough · Team AlphaFire</p><h1 class="display">SupplyLens</h1><p class="lead">Hotels and sightseeing from three synthetic suppliers, made comparable.</p><p class="mono">{LIVE}</p>""",
     "say": "This is a walkthrough of the SupplyLens prototype. All suppliers, prices and availability in it are synthetic."},
    {"layout": "full", "html": screen("raw", "Raw supplier feed: what suppliers send"),
     "say": "First, the raw supplier feed. Nineteen listings from three suppliers. The same Marina Pearl hotel appears three times under three different names, and the Red Dune safari appears twice."},
    {"layout": "full", "html": screen("hotel_top", "Hotels · “marina hotel with breakfast, free cancellation”"),
     "say": "Now a hotel search: a marina hotel with breakfast and free cancellation. Breakfast, free cancellation and the marina area become hard constraints. Marina Pearl appears once, with three suppliers consolidated, and every card says why it ranks where it does. Hotels in other areas, without breakfast, unavailable, or with a stale price are hidden, and the reason is listed."},
    {"layout": "full", "html": screen("hotel_detail", "Sourced content, conflict flag, gallery de-duplication"),
     "say": "Opening the property shows sourced content. Each field shows the supplier it came from. The star rating disagrees between suppliers, so it is flagged for review. Two duplicate images are removed, and the source of each image is kept."},
    {"layout": "full", "html": screen("hotel_rooms", "Room mapping across suppliers"),
     "say": "Room mapping. Thirty-two square metres and three hundred forty-four square feet are the same size, so the two King rooms are one family. Twin stays separate. And a room whose bed is subject to availability is only a possible match."},
    {"layout": "full", "html": screen("hotel_offers", "Supplier offers: eligibility before price"),
     "say": "Here are the supplier offers. The cheapest headline price, from Corsa, excludes taxes, so it is struck through as not comparable. Offers without breakfast, non-refundable, or with an unknown policy are not eligible. The Beacon offer is the cheapest comparable, most flexible, and balanced pick."},
    {"layout": "full", "html": screen("exp_top", "Sightseeing · “evening activity with hotel pickup and flexible cancellation”"),
     "say": "Now sightseeing: an evening activity with hotel pickup and flexible cancellation. Only products that really include pickup and a known refundable policy are shown."},
    {"layout": "full", "html": screen("exp_detail", "Same product merged; self-transfer kept separate"),
     "say": "The Red Dune safari is one product from two suppliers, with its configuration preserved. The self-transfer version from the same operator is kept separate, because pickup and duration differ."},
    {"layout": "full", "html": screen("cruise", "Ranking: relevance before price"),
     "say": "Ranking puts relevance first. For dinner cruise, the cruise that includes dinner ranks above a cheaper cruise without it."},
    {"layout": "full", "html": screen("review", "Review queue: uncertain stays visible"),
     "say": "Uncertain pairs go to the review queue. The two Oasis Palm records share a name but have different street numbers. The Old Dubai walk is missing an operator. A reviewer decides, and every decision is logged and can be undone."},
    {"layout": "full", "html": screen("evidence", "Evidence tab: metrics recomputed live"),
     "say": "Finally, the evidence tab recomputes the evaluation live. Name-only matching makes three harmful merges in each vertical; SupplyLens makes zero. Ranking beats the raw feed and the cheapest-price baseline on held-out intents. The benchmark is small and synthetic, so these results are exploratory."},
    {"layout": "cover", "html": f"""<p class="kicker">Limits and next step</p><h1 class="display">Ready for a real-feed pilot.</h1><p class="lead">Synthetic data only · lexical relevance · in-memory review state · no bookings. Next: authorized sample feeds for one destination.</p><p class="mono">{REPO}</p>""",
     "say": "Limits: synthetic data, lexical relevance only, and review decisions kept in memory. Next, we want authorized sample feeds for one destination to run a real pilot. The code, documentation and setup steps are on GitHub. Thank you."},
]
