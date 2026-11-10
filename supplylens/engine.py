"""SupplyLens engine: identity matching, variant mapping, offer eligibility and listing ranking.

Three separate decisions (see docs/SOLUTION.md):
  1. identity    - are two supplier records the same hotel / experience product?
  2. equivalence - are two room variants interchangeable?
  3. recommendation - which eligible offer / listing is preferable for this query?
"""
import json
import math
import re
from datetime import datetime
from itertools import combinations
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
VERTICALS = ("hotels", "experiences")


def _load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


META = _load("suppliers")
NOW = datetime.fromisoformat(META["now"])
STORE = {v: _load(v) for v in VERTICALS}
RECORDS = {v: {r["id"]: r for r in STORE[v]["records"]} for v in VERTICALS}

# Reviewer decisions: {(vertical, a, b): "match"|"distinct"}, plus an append-only audit log.
# shortcut: in-memory, resets on restart; persist to SQLite if reviews must survive a redeploy.
REVIEWS = {}
AUDIT = []

# ---------------------------------------------------------------- normalization
ABBREV = {"htl": "hotel", "rd": "road", "st": "street", "dr": "drive", "&": "and", "apt": "apartment",
          "1br": "one bedroom", "residence": "residences"}
STOP = {"the", "and", "a", "an", "of", "with", "at", "in", "to", "for", "my", "me", "near", "i", "want", "-", "+", ":"}


def tokens(text):
    words = re.findall(r"[a-z0-9&]+", (text or "").lower())
    out = []
    for w in words:
        out.extend(ABBREV.get(w, w).split())
    return [w for w in out if w not in STOP]


def name_sim(a, b):
    ta, tb = set(tokens(a)), set(tokens(b))
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


def street_key(address):
    """'14 Harbour Walk, Dubai Marina' -> ('14', 'harbour walk'). Number + first two street words."""
    t = tokens(address.split(",")[0])
    num = next((w for w in t if w.isdigit()), None)
    words = [w for w in t if not w.isdigit()][:2]
    return num, " ".join(words)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def digits(phone):
    return re.sub(r"\D", "", phone or "") or None


def hours_old(ts):
    return (NOW - datetime.fromisoformat(ts)).total_seconds() / 3600


# ---------------------------------------------------------------- identity matching
def candidate_pairs(vertical):
    """Blocking: hotels within 2 km, experiences sharing an attraction. Matching never sees other pairs."""
    recs = list(RECORDS[vertical].values())
    for a, b in combinations(recs, 2):
        if a["supplier"] == b["supplier"]:
            continue
        if vertical == "hotels" and km(a, b) <= 2:
            yield a, b
        if vertical == "experiences" and a["attraction"] == b["attraction"]:
            yield a, b


def decide_hotel(a, b):
    ev, conflicts = [], []
    sim, dist = name_sim(a["name"], b["name"]), km(a, b)
    ev.append(f"name similarity {sim:.2f}")
    ev.append(f"{dist * 1000:.0f} m apart")
    ka, kb = street_key(a["address"]), street_key(b["address"])
    same_addr = ka == kb and ka[0] is not None
    if same_addr:
        ev.append(f"same street address ({ka[0]} {ka[1]})")
    elif ka[1] == kb[1] and ka[0] != kb[0]:
        conflicts.append(f"street number differs ({ka[0]} vs {kb[0]})")
    elif ka[1] != kb[1]:
        conflicts.append("different street")
    pa, pb = digits(a["phone"]), digits(b["phone"])
    if pa and pb:
        (ev if pa == pb else conflicts).append("same phone" if pa == pb else "phone differs")
    if a["area"] != b["area"]:
        conflicts.append(f"different area ({a['area']} vs {b['area']})")
    if dist > 0.3:
        conflicts.append("more than 300 m apart")

    if sim >= 0.5 and same_addr and not conflicts:
        return "match", ev, conflicts
    if sim >= 0.5 and dist <= 1 and a["area"] == b["area"]:
        return "review", ev, conflicts  # similar name nearby but evidence conflicts: a human decides
    return "distinct", ev, conflicts


EXP_ATTRS = ("pickup", "meal", "access", "private", "slot")


def decide_experience(a, b):
    ev, conflicts = [f"same attraction family ({a['attraction']})"], []
    for k in EXP_ATTRS:
        if a[k] is not None and b[k] is not None and a[k] != b[k]:
            yn = lambda v: {True: "yes", False: "no"}.get(v, v)
            conflicts.append(f"{k} differs ({yn(a[k])} vs {yn(b[k])})")
    da, db = a["duration_h"], b["duration_h"]
    if abs(da - db) / max(da, db) > 0.15:
        conflicts.append(f"duration differs ({da} h vs {db} h)")
    else:
        ev.append(f"duration compatible ({da} h / {db} h)")
    if a["operator"] and b["operator"]:
        if a["operator"] == b["operator"]:
            ev.append(f"same operator ({a['operator']})")
        else:
            conflicts.append(f"different operator ({a['operator']} vs {b['operator']})")
    if conflicts:
        return "distinct", ev, conflicts
    if not (a["operator"] and b["operator"]):
        ev.append("operator missing on one record")
        return "review", ev, conflicts
    return "match", ev, conflicts


def decide(vertical, a, b, use_reviews=True):
    """Machine decision for one pair, then reviewer override if one exists."""
    decision, ev, conflicts = (decide_hotel if vertical == "hotels" else decide_experience)(a, b)
    key = (vertical, *sorted((a["id"], b["id"])))
    machine = decision
    if use_reviews and key in REVIEWS:
        decision = REVIEWS[key]
    return {"a": a["id"], "b": b["id"], "decision": decision, "machine": machine,
            "reviewed": use_reviews and key in REVIEWS, "evidence": ev, "conflicts": conflicts}


def pair_decisions(vertical, use_reviews=True):
    return [decide(vertical, a, b, use_reviews) for a, b in candidate_pairs(vertical)]


def resolve(vertical, use_reviews=True):
    """Cluster records into canonical entities. A link is added only if it is compatible with
    every member already in both clusters (A~B and B~C does not prove A~C)."""
    decisions = pair_decisions(vertical, use_reviews)
    verdict = {frozenset((d["a"], d["b"])): d["decision"] for d in decisions}
    cluster = {rid: {rid} for rid in RECORDS[vertical]}
    for d in sorted(decisions, key=lambda d: d["decision"] != "match"):
        if d["decision"] != "match" or cluster[d["a"]] is cluster[d["b"]]:
            continue
        ca, cb = cluster[d["a"]], cluster[d["b"]]
        if all(verdict.get(frozenset((x, y))) == "match" for x in ca for y in cb):
            merged = ca | cb
            for rid in merged:
                cluster[rid] = merged
    groups = {frozenset(c) for c in cluster.values()}
    return [sorted(g) for g in sorted(groups, key=lambda g: sorted(g)[0])], decisions


# ---------------------------------------------------------------- hotel content and rooms
def sqm(room):
    return round(room["size"] * (0.092903 if room["size_unit"] == "sqft" else 1), 1)


def enrich(records):
    """Field-level provenance: pick the most common non-null value (ties -> most recent), flag conflicts."""
    fields = {}
    for f in ("name", "address", "stars", "phone", "description"):
        vals = [(r[f], r["supplier"], r["fetched_at"]) for r in records if r.get(f) not in (None, "")]
        if not vals:
            fields[f] = {"value": None, "sources": [], "conflict": False, "note": "not supplied"}
            continue
        norm = (lambda v: digits(v)) if f == "phone" else (lambda v: street_key(v) if f == "address" else v)
        counts = {}
        for v, s, t in vals:
            counts.setdefault(norm(v), []).append((v, s, t))
        best = max(counts.values(), key=lambda g: (len(g), max(t for _, _, t in g)))
        best = max(best, key=lambda x: x[2])
        fields[f] = {"value": best[0], "sources": sorted({s for _, s, _ in vals}),
                     "chosen_from": best[1], "conflict": len(counts) > 1 and f in ("stars", "address", "phone"),
                     "alternatives": [{"value": v, "supplier": s} for v, s, _ in vals if norm(v) != norm(best[0])]}
    amen = {}
    for r in records:
        for a in r["amenities"]:
            amen.setdefault(a, []).append(r["supplier"])
    images, seen = [], {}
    for r in records:
        for img in r["images"]:
            if img["hash"] in seen:
                seen[img["hash"]]["sources"].append(r["supplier"])
                continue
            seen[img["hash"]] = {"hash": img["hash"], "caption": img["caption"], "sources": [r["supplier"]],
                                 "synthetic_placeholder": True}
            images.append(seen[img["hash"]])
    raw_images = sum(len(r["images"]) for r in records)
    return {"fields": fields, "amenities": [{"name": k, "sources": v} for k, v in sorted(amen.items())],
            "images": images, "images_removed_as_duplicates": raw_images - len(images)}


def room_relation(x, y):
    reasons, diffs = [], []
    if x["occupancy"] != y["occupancy"]:
        diffs.append(f"occupancy {x['occupancy']} vs {y['occupancy']}")
    sx, sy = sqm(x), sqm(y)
    if abs(sx - sy) / max(sx, sy) > 0.1:
        diffs.append(f"size {sx} vs {sy} m²")
    else:
        reasons.append(f"size {sx} / {sy} m² (units normalized)")
    if x["view"] != y["view"]:
        diffs.append(f"view {x['view']} vs {y['view']}")
    vague = "subject to availability" in (x["bed"], y["bed"])
    if not vague and x["bed"] != y["bed"]:
        diffs.append(f"bed {x['bed']} vs {y['bed']}")
    if diffs:
        return "distinct", reasons, diffs
    if vague:
        return "possible", reasons + ["bed type not guaranteed by one supplier"], diffs
    return "equivalent", reasons + [f"same occupancy {x['occupancy']}, bed {x['bed']}, view {x['view']}"], diffs


def map_rooms(records):
    rooms = [dict(room, supplier=r["supplier"], record=r["id"], size_sqm=sqm(room)) for r in records for room in r["rooms"]]
    family = list(range(len(rooms)))
    pairs = []
    for i, j in combinations(range(len(rooms)), 2):
        if rooms[i]["record"] == rooms[j]["record"]:
            continue
        rel, reasons, diffs = room_relation(rooms[i], rooms[j])
        pairs.append({"a": f"{rooms[i]['supplier']}: {rooms[i]['name']}", "b": f"{rooms[j]['supplier']}: {rooms[j]['name']}",
                      "relation": rel, "reasons": reasons, "differences": diffs})
        if rel == "equivalent":
            old, new = family[j], family[i]
            family = [new if f == old else f for f in family]
    ids = {f: n + 1 for n, f in enumerate(dict.fromkeys(family))}
    for room, f in zip(rooms, family):
        room["family"] = f"Room family {ids[f]}"
    return rooms, pairs


# ---------------------------------------------------------------- offers
def to_aed(amount, cur):
    return round(amount * META["fx"]["rates"][cur])


def flex_rank(o):
    """Higher is more flexible. None means the policy is unknown, never treated as flexible."""
    if o["refundable"] is None:
        return None
    if not o["refundable"]:
        return 0
    return 1 + datetime.fromisoformat(o["cancel_deadline"]).timestamp() / 1e10


def evaluate_offer(vertical, o, q, rooms_by_key):
    rec = RECORDS[vertical][o["record"]]
    out = dict(o, supplier=rec["supplier"], total_aed=to_aed(o["total"], o["currency"]),
               converted=o["currency"] != "AED", hours_old=round(hours_old(o["fetched_at"]), 1))
    reasons = []
    if vertical == "hotels":
        room = rooms_by_key[(o["record"], o["room"])]
        out.update(room_name=room["name"], family=room["family"], bed=room["bed"])
        if room["occupancy"] < q.get("adults", 2):
            reasons.append("room too small for party")
        if q.get("breakfast") and o["meal"] != "breakfast":
            reasons.append("breakfast not included")
    else:
        out.update(pickup=rec["pickup"], meal_included=rec["meal"], access=rec["access"])
        if q.get("pickup") and rec["pickup"] is not True:
            reasons.append("no hotel pickup")
    if not o["available"]:
        reasons.append("unavailable")
    if out["hours_old"] > META["freshness_hours"]:
        reasons.append(f"stale price ({out['hours_old']:.0f} h old)")
    if not o["taxes_included"]:
        reasons.append("incomplete price: taxes not included, not comparable")
    if q.get("refundable") and o["refundable"] is not True:
        reasons.append("cancellation policy not supplied" if o["refundable"] is None else "non-refundable")
    out["eligible"] = not reasons
    out["ineligible_reasons"] = reasons
    out["policy_label"] = ("policy not supplied" if o["refundable"] is None else
                           f"free cancellation until {o['cancel_deadline'][:16].replace('T', ' ')}" if o["refundable"]
                           else "non-refundable")
    return out


def dominates(x, y):
    """x dominates y if no worse on every dimension and strictly better on one. Unknowns block the claim."""
    fx, fy = flex_rank(x), flex_rank(y)
    if fx is None or fy is None:
        return False
    px, py = x["payment"] != "pay now", y["payment"] != "pay now"
    no_worse = x["total_aed"] <= y["total_aed"] and fx >= fy and px >= py
    better = x["total_aed"] < y["total_aed"] or fx > fy or px > py
    return no_worse and better


def label_offers(offers):
    elig = [o for o in offers if o["eligible"]]
    for o in offers:
        o["labels"] = []
    if not elig:
        return
    for o in elig:
        o["non_dominated"] = not any(dominates(p, o) for p in elig if p is not o)
    min(elig, key=lambda o: o["total_aed"])["labels"].append("cheapest comparable")
    known = [o for o in elig if flex_rank(o) is not None]
    if known:
        max(known, key=lambda o: (flex_rank(o), o["payment"] != "pay now", -o["total_aed"]))["labels"].append("most flexible")
    lo = min(o["total_aed"] for o in elig)
    pool = [o for o in elig if o.get("non_dominated")] or elig
    best = min(pool, key=lambda o: o["total_aed"] / lo - 0.1 * (flex_rank(o) or 0) - 0.05 * (o["payment"] != "pay now"))
    best["labels"].append("balanced pick")


def supplier_reliability(name):
    s = META["suppliers"].get(name, {})
    if not s.get("bookings"):
        return {"score": 0.5, "label": "no history: neutral prior", "sample": 0}
    rate = s["confirmed"] / s["bookings"]
    return {"score": rate, "label": f"{rate:.0%} confirmed (n={s['bookings']}, synthetic)", "sample": s["bookings"]}


# ---------------------------------------------------------------- entities
def build_entities(vertical, q=None):
    q = q or {}
    groups, decisions = resolve(vertical)
    by_record = {}
    for d in decisions:
        by_record.setdefault(d["a"], []).append(d)
        by_record.setdefault(d["b"], []).append(d)
    entities = []
    for g in groups:
        recs = [RECORDS[vertical][rid] for rid in g]
        ent = {"id": g[0], "vertical": vertical, "records": g, "suppliers": sorted({r["supplier"] for r in recs})}
        rooms_by_key = {}
        if vertical == "hotels":
            ent["content"] = enrich(recs)
            rooms, room_pairs = map_rooms(recs)
            rooms_by_key = {(r["record"], r["code"]): r for r in rooms}
            ent.update(name=ent["content"]["fields"]["name"]["value"], area=recs[0]["area"], rooms=rooms, room_pairs=room_pairs,
                       variant_count=len({r["family"] for r in rooms}))
            doc = " ".join([ent["name"], recs[0]["area"], " ".join(a["name"] for a in ent["content"]["amenities"]),
                            " ".join(r["description"] or "" for r in recs), "hotel stay"])
        else:
            r0 = recs[0]
            ent.update(name=min((r["name"] for r in recs), key=len), area=r0["area"], attraction=r0["attraction"],
                       operator=next((r["operator"] for r in recs if r["operator"]), None),
                       config={k: r0[k] for k in ("duration_h", "pickup", "meal", "access", "slot", "language")},
                       variant_count=1, supplier_names=[{"supplier": r["supplier"], "name": r["name"]} for r in recs])
            inc = (["hotel pickup"] if r0["pickup"] else ["self transfer"]) + (["dinner meal"] if r0["meal"] else []) \
                + [r0["access"] + " access", r0["slot"], "activity tour experience"]
            # free text may say "no pickup": inclusion words come only from structured fields
            free = [t for r in recs for t in tokens(r["name"] + " " + (r["description"] or "")) if t not in ("pickup", "hotel", "transfers")]
            doc = " ".join(free + [r0["attraction"], r0["area"]] + inc)
        ent["doc_tokens"] = sorted({SYNONYMS.get(t, t) for t in tokens(doc)})
        offers = [evaluate_offer(vertical, o, q, rooms_by_key) for o in STORE[vertical]["offers"] if o["record"] in g]
        for fam in {o.get("family") for o in offers}:  # only offers for the same room family are comparable
            label_offers([o for o in offers if o.get("family") == fam])
        ent["offers"] = sorted(offers, key=lambda o: (not o["eligible"], o["total_aed"]))
        ent["review_pairs"] = [d for rid in g for d in by_record.get(rid, []) if d["decision"] == "review"]
        entities.append(ent)
    if vertical == "experiences":  # attraction family: discovery relationship, not identity
        for e in entities:
            e["related"] = [{"id": o["id"], "name": o["name"], "why_separate": _why_separate(e, o)}
                            for o in entities if o is not e and o["attraction"] == e["attraction"]]
    return entities


def _why_separate(e, o):
    d = decide("experiences", RECORDS["experiences"][e["id"]], RECORDS["experiences"][o["id"]])
    return d["conflicts"] or ["awaiting review: " + ", ".join(d["evidence"][-1:])]


# ---------------------------------------------------------------- ranking
SYNONYMS = {"flexible": "refundable", "cancellation": "refundable", "free": "refundable", "pick": "pickup",
            "transfers": "pickup", "souks": "souk", "souq": "souk", "beachfront": "beach", "deck": "observation",
            "cheap": "budget", "dinner": "dinner", "night": "evening", "sea": "beach"}
WEIGHTS = {"relevance": 0.40, "value": 0.25, "policy_fit": 0.15, "confidence": 0.10, "reliability": 0.10}


def query_tokens(text):
    out = [SYNONYMS.get(t, t) for t in tokens(text)]
    return list(dict.fromkeys(t for t in out if t not in ("refundable", "budget", "stay", "hotel", "ticket")))


def search(vertical, text="", refundable=False, breakfast=False, pickup=False, adults=2, sort="recommended"):
    q = {"refundable": refundable, "breakfast": breakfast, "pickup": pickup, "adults": adults}
    low = text.lower()  # stated requirements in the query become hard constraints
    q["refundable"] |= "flexible" in low or "free cancellation" in low or "refundable" in low
    q["breakfast"] |= vertical == "hotels" and "breakfast" in low
    q["pickup"] |= vertical == "experiences" and "pickup" in low
    ents = build_entities(vertical, q)
    qt = query_tokens(text)
    areas = {t for r in RECORDS[vertical].values() for t in tokens(r["area"])} - {"dubai"}
    want_area = [t for t in qt if t in areas]
    shown, excluded = [], []
    for e in ents:
        elig = [o for o in e["offers"] if o["eligible"]]
        if not elig:
            reasons = sorted({r for o in e["offers"] for r in o["ineligible_reasons"]})
            excluded.append({"id": e["id"], "name": e["name"], "reasons": reasons})
            continue
        doc = set(e["doc_tokens"])
        hits = [t for t in qt if t in doc]
        if want_area and not set(want_area) & set(tokens(e["area"])):
            excluded.append({"id": e["id"], "name": e["name"], "reasons": [f"outside requested area ({e['area']})"]})
            continue
        if qt and not hits:
            excluded.append({"id": e["id"], "name": e["name"], "reasons": ["no query term matched"]})
            continue
        e["relevance"] = len(hits) / len(qt) if qt else 1.0
        e["matched_terms"] = hits
        picks = [o for o in elig if "balanced pick" in o["labels"]] or elig
        e["best_offer"] = min(picks, key=lambda o: (-(flex_rank(o) or 0) if q["refundable"] else 0, o["total_aed"]))
        e["from_aed"] = min(o["total_aed"] for o in elig)
        shown.append(e)
    if shown:
        lo, hi = min(e["from_aed"] for e in shown), max(e["from_aed"] for e in shown)
        for e in shown:
            b = e["best_offer"]
            f = {"relevance": e["relevance"],
                 "value": 1.0 if hi == lo else 1 - (e["from_aed"] - lo) / (hi - lo),
                 "policy_fit": {None: 0.5, False: 0.0}.get(b["refundable"], 1.0),
                 "confidence": 1.0 if b["hours_old"] <= 12 else 0.6,
                 "reliability": supplier_reliability(b["supplier"])["score"]}
            e["factors"] = {k: round(v, 3) for k, v in f.items()}
            # secondary signals are scaled by relevance so a cheap but off-intent listing cannot outrank a relevant one
            e["score"] = round(WEIGHTS["relevance"] * f["relevance"]
                               + f["relevance"] * sum(WEIGHTS[k] * f[k] for k in WEIGHTS if k != "relevance"), 4)
            e["reasons"] = _reasons(e, b)
    key = (lambda e: e["from_aed"]) if sort == "price" else (lambda e: (-e["score"], e["from_aed"]))
    shown.sort(key=key)
    return {"vertical": vertical, "query": text, "constraints": q, "context": META["context"][vertical],
            "weights": WEIGHTS, "results": shown, "excluded": excluded,
            "raw_listing_count": sum(len(e["records"]) for e in ents), "entity_count": len(ents)}


def _reasons(e, b):
    r = []
    if e["matched_terms"]:
        r.append("matches " + ", ".join(f"“{t}”" for t in e["matched_terms"]))
    r.append(f"{len(e['suppliers'])} supplier{'s' if len(e['suppliers']) > 1 else ''} consolidated")
    r.append(b["policy_label"])
    if e["vertical"] == "experiences":
        r.append("includes hotel pickup" if e["config"]["pickup"] else "self-transfer (no pickup)")
    elif b["meal"] == "breakfast":
        r.append("breakfast included")
    r.append(f"best offer via {b['supplier']}: {supplier_reliability(b['supplier'])['label']}")
    return r


def review(vertical, a, b, decision, note=""):
    if decision not in ("match", "distinct", "reset"):
        raise ValueError("decision must be match, distinct or reset")
    if a not in RECORDS[vertical] or b not in RECORDS[vertical]:
        raise KeyError("unknown record")
    key = (vertical, *sorted((a, b)))
    before = REVIEWS.get(key)
    if decision == "reset":
        REVIEWS.pop(key, None)
    else:
        REVIEWS[key] = decision
    AUDIT.append({"at": datetime.now().isoformat(timespec="seconds"), "vertical": vertical, "pair": [a, b],
                  "from": before, "to": None if decision == "reset" else decision, "note": note[:200]})
    return AUDIT[-1]
