[← Back to README](../README.md)

# Demo guide

**Start:** `uvicorn supplylens.app:app`, or open the Render URL. Wait for the first load if the service was idle.
**Reset:** restart the server. Reviewer decisions are in memory only.
**Notice:** every screen states that the data is synthetic.

## 5-minute walkthrough

1. **Raw supplier feed** tab: 19 listings. Point out Marina Pearl appearing three times under three names.
2. **Search → Hotels →** "marina hotel with breakfast, free cancellation".
   - One Marina Pearl card: 3 suppliers, room families, and the reasons for its ranking.
   - Hidden by hard constraints: the stale Oasis Palm price, the unavailable Dune View Inn, and other areas.
   - Detail panel: sourced fields with their suppliers, the stars conflict flagged, 2 duplicate images removed.
   - Room mapping: 32 m² = 344 sqft, King ≠ Twin, "Double or Twin" is only *possible*.
   - Offers: the cheapest headline price (Corsa, AED 1,580) is struck through because taxes are excluded; the unknown policy is excluded because free cancellation is required.
3. **Sightseeing →** "evening activity with hotel pickup and flexible cancellation".
   - The Red Dune pickup safari is one product from 2 suppliers; the self-transfer version is listed under "Same attraction, different product" with its reason.
   - The Old Dubai walk shows a "possible duplicate under review" badge.
4. **Sightseeing →** "dinner cruise": the dinner cruise ranks above the cheaper cruise without dinner.
5. **Review queue:** mark the Old Dubai pair *Same product*, then search again: it is now one product with 2 suppliers. Show the audit log, then click *Undo*.
6. **Evidence** tab: the baseline makes 3 harmful merges per vertical and SupplyLens makes 0. Show the NDCG table and say plainly that it is a small synthetic benchmark.

## Expected outcomes

| Scenario | Expected |
|---|---|
| Marina Pearl | 3 records → 1 entity, 4 room families, star conflict flagged |
| Saffron Courtyard | Deira (2 suppliers) and Jumeirah remain separate |
| Oasis Palm | in the review queue, not merged; the Corsa price is hidden as stale |
| Red Dune safari | pickup version from 2 suppliers; self-transfer kept separate |
| Skyline Tower | standard admission from 2 suppliers; premium skip-the-line kept separate |
| No-result query (e.g. hotels + "casino") | an empty list with an explanation instead of an unsuitable result |
