"""Offline evaluation on the synthetic benchmark. Run: python -m supplylens.evaluate

Reports Hotels and Sightseeing separately. Small synthetic samples: results are exploratory, not production claims.
"""
import json
import math
import time

from . import engine as E

LABELS = json.loads((E.DATA / "labels.json").read_text(encoding="utf-8"))


def _ratio(n, d):
    return round(n / d, 3) if d else None  # None = N/A (e.g. no auto-links)


def matching(vertical):
    groups, decisions = E.resolve(vertical, use_reviews=False)  # evaluate the machine, not reviewer overrides
    entity = {rid: i for i, g in enumerate(groups) for rid in g}
    decided = {frozenset((d["a"], d["b"])): d["decision"] for d in decisions}
    recs = E.RECORDS[vertical]
    out = {}
    for method in ("name_only_baseline", "supplylens"):
        tp = fp = fn = review = review_true = 0
        harmful = []
        for p in LABELS["pairs"][vertical]:
            key = frozenset((p["a"], p["b"]))
            if method == "name_only_baseline":
                linked, rev = E.name_sim(recs[p["a"]]["name"], recs[p["b"]]["name"]) >= 0.5, False
            else:
                linked = entity[p["a"]] == entity[p["b"]]
                rev = not linked and decided.get(key) == "review"
            truth = p["truth"] == "match"
            tp += linked and truth
            fp += linked and not truth
            fn += not linked and truth
            review += rev
            review_true += rev and truth
            if linked and not truth:
                harmful.append(f"{p['a']} + {p['b']}" + (f" ({p['note']})" if p.get("note") else ""))
        n_true = sum(p["truth"] == "match" for p in LABELS["pairs"][vertical])
        out[method] = {"pairs": len(LABELS["pairs"][vertical]), "true_matches": n_true, "auto_links": tp + fp,
                       "auto_link_precision": _ratio(tp, tp + fp), "auto_only_recall": _ratio(tp, n_true),
                       "assisted_recall": _ratio(tp + review_true, n_true), "sent_to_review": review,
                       "harmful_merges": len(harmful), "harmful_merge_examples": harmful}
    cands = {frozenset((a["id"], b["id"])) for a, b in E.candidate_pairs(vertical)}
    true_pairs = [frozenset((p["a"], p["b"])) for p in LABELS["pairs"][vertical] if p["truth"] == "match"]
    out["candidate_recall"] = _ratio(sum(t in cands for t in true_pairs), len(true_pairs))
    return out


def ndcg(ranked_ids, grades, pool_ids, k_max=5):
    k = min(k_max, len(pool_ids))
    ideal = sorted((grades.get(i, 0) for i in set(pool_ids) | set(ranked_ids)), reverse=True)[:k]
    idcg = sum(g / math.log2(n + 2) for n, g in enumerate(ideal))
    if not idcg:
        return None, k
    dcg = sum(grades.get(i, 0) / math.log2(n + 2) for n, i in enumerate(ranked_ids[:k]))
    return round(dcg / idcg, 3), k


def ranking(vertical):
    rows = []
    for it in LABELS["intents"][vertical]:
        adults = it.get("adults", 2)
        res = E.search(vertical, it["q"], adults=adults)
        ent_of = {rid: e["id"] for e in E.build_entities(vertical) for rid in e["records"]}
        grades = {}
        for rid, g in it["grades"].items():
            grades[ent_of[rid]] = max(grades.get(ent_of[rid], 0), g)
        # pool = entities with an eligible offer under the same hard constraints, regardless of text match
        pool = [e["id"] for e in E.search(vertical, "", adults=adults, **{k: v for k, v in res["constraints"].items() if k != "adults"})["results"]]
        proposed = [e["id"] for e in res["results"]]
        cheapest = [e["id"] for e in E.search(vertical, it["q"], adults=adults, sort="price")["results"]]
        # raw supplier feed order: every record listed separately; repeats of an entity earn no gain
        qt = set(E.query_tokens(it["q"]))
        raw, seen = [], set()
        for rid, r in E.RECORDS[vertical].items():
            if qt & set(E.tokens(r["name"] + " " + (r.get("description") or ""))):
                raw.append(ent_of[rid] if ent_of[rid] not in seen else f"dup:{rid}")
                seen.add(ent_of[rid])
        row = {"split": it["split"], "query": it["q"], "pool": len(pool), "shown": len(proposed)}
        for name, order in (("raw_supplier_order", raw), ("cheapest_eligible", cheapest), ("supplylens", proposed)):
            row[name], row["k"] = ndcg(order, grades, pool)
        row["top_result"] = res["results"][0]["name"] if res["results"] else "no result"
        rows.append(row)
    summary = {}
    for split in ("validation", "test"):
        part = [r for r in rows if r["split"] == split]
        for m in ("raw_supplier_order", "cheapest_eligible", "supplylens"):
            vals = [r[m] for r in part if r[m] is not None]
            summary[f"{split}_{m}_mean_ndcg"] = round(sum(vals) / len(vals), 3) if vals else None
        summary[f"{split}_intents_scored"] = sum(r["supplylens"] is not None for r in part)
    return {"intents": rows, "summary": summary}


def offers_check(vertical):
    """Safety rules every recommendation must obey, checked over all intents."""
    violations = []
    for it in LABELS["intents"][vertical]:
        for e in E.search(vertical, it["q"], adults=it.get("adults", 2))["results"]:
            b = e["best_offer"]
            if not b["eligible"] or not b["taxes_included"] or b["hours_old"] > E.META["freshness_hours"] or not b["available"]:
                violations.append(f"{it['q']}: {b['id']}")
    return {"recommendations_checked": sum(len(E.search(vertical, it["q"])["results"]) for it in LABELS["intents"][vertical]),
            "rule_violations": violations}


def latency(vertical, runs=30):
    times = []
    for _ in range(runs):
        t = time.perf_counter()
        E.search(vertical, "evening hotel with pool and pickup")
        times.append((time.perf_counter() - t) * 1000)
    times.sort()
    return {"runs": runs, "median_ms": round(times[len(times) // 2], 2), "p95_ms": round(times[int(runs * 0.95) - 1], 2)}


def run():
    return {"dataset": "synthetic fixture v1 (see docs/DATA_CARD.md)",
            "verticals": {v: {"matching": matching(v), "ranking": ranking(v), "offers": offers_check(v), "latency": latency(v)}
                          for v in E.VERTICALS}}


if __name__ == "__main__":
    report = run()
    (E.DATA.parent / "docs" / "evaluation_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
