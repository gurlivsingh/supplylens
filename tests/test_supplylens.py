"""Acceptance cases from the master plan (sections 08-11, 14). Run: pytest -q"""
import pytest
from fastapi.testclient import TestClient

from supplylens import engine as E
from supplylens import evaluate
from supplylens.app import app


@pytest.fixture(autouse=True)
def clean_reviews():
    E.REVIEWS.clear()
    yield
    E.REVIEWS.clear()


def group_of(vertical, rid):
    groups, _ = E.resolve(vertical)
    return next(g for g in groups if rid in g)


def entity(vertical, rid, q=None):
    return next(e for e in E.build_entities(vertical, q) if rid in e["records"])


# identity
def test_same_hotel_abbreviated_names_merge():
    assert group_of("hotels", "A-H101") == ["A-H101", "B-77812", "C-DXB-5531"]


def test_same_chain_other_neighbourhood_stays_separate():
    assert "B-90211" not in group_of("hotels", "A-H205")


def test_similar_name_different_building_goes_to_review_not_merge():
    assert group_of("hotels", "A-H310") == ["A-H310"]
    d = E.decide("hotels", E.RECORDS["hotels"]["A-H310"], E.RECORDS["hotels"]["C-DXB-7104"])
    assert d["decision"] == "review"


def test_pickup_tour_not_merged_with_self_transfer():
    assert group_of("experiences", "A-X11") == ["A-X11", "B-T4410"]


def test_standard_and_premium_access_stay_distinct():
    assert "C-SS-310" not in group_of("experiences", "A-X20")


def test_missing_operator_goes_to_review():
    d = E.decide("experiences", E.RECORDS["experiences"]["C-SS-420"], E.RECORDS["experiences"]["A-X42"])
    assert d["decision"] == "review"


def test_review_merge_is_reversible_and_audited():
    E.review("experiences", "C-SS-420", "A-X42", "match")
    assert group_of("experiences", "A-X42") == ["A-X42", "C-SS-420"]
    E.review("experiences", "C-SS-420", "A-X42", "reset")
    assert group_of("experiences", "A-X42") == ["A-X42"]
    assert E.AUDIT[-1]["to"] is None


def test_cluster_requires_all_pairs_compatible():
    # reviewer forces a link that conflicts with an existing member: the pair alone is not enough
    E.review("hotels", "A-H205", "B-90211", "match")
    assert "B-90211" not in group_of("hotels", "A-H205")


# rooms and content
def test_room_units_normalised_and_bed_types_kept_apart():
    rooms, pairs = E.map_rooms([E.RECORDS["hotels"][r] for r in ("A-H101", "B-77812")])
    fam = {(r["supplier"], r["code"]): r["family"] for r in rooms}
    assert fam[("Atlas", "DLX-K")] == fam[("Beacon", "K-DLX")]  # 32 sqm == 344 sqft
    assert fam[("Atlas", "DLX-T")] != fam[("Beacon", "K-DLX")]  # twin vs king
    assert any(p["relation"] == "possible" for p in pairs)  # "subject to availability" bed


def test_content_conflict_flagged_and_images_deduplicated():
    c = entity("hotels", "A-H101")["content"]
    assert c["fields"]["stars"]["conflict"] is True
    assert c["images_removed_as_duplicates"] == 2
    alone = E.enrich([E.RECORDS["hotels"]["C-DXB-5531"]])["fields"]
    assert alone["phone"]["value"] is None and alone["description"]["value"] is None  # unknown stays unknown


# offers
def test_tax_exclusive_price_is_never_cheapest():
    offers = entity("hotels", "A-H101")["offers"]
    o3 = next(o for o in offers if o["id"] == "o3")
    assert not o3["eligible"] and o3["labels"] == []


def test_unknown_policy_is_not_free_cancellation():
    offers = entity("hotels", "A-H101", {"refundable": True})["offers"]
    o5 = next(o for o in offers if o["id"] == "o5")
    assert not o5["eligible"] and "cancellation policy not supplied" in o5["ineligible_reasons"]
    assert "most flexible" not in o5["labels"]


def test_stale_and_unavailable_offers_excluded():
    res = E.search("hotels", "")
    hidden = {x["id"]: x["reasons"] for x in res["excluded"]}
    assert any("stale" in r for r in hidden["C-DXB-7104"])


def test_currency_converted_with_snapshot():
    o12 = next(o for o in entity("hotels", "B-50400")["offers"] if o["id"] == "o12")
    assert o12["converted"] and o12["total_aed"] == round(160 * 3.6725)


def test_dominance_blocked_by_unknowns():
    a = {"total_aed": 100, "refundable": None, "cancel_deadline": None, "payment": "pay now"}
    b = {"total_aed": 200, "refundable": False, "cancel_deadline": None, "payment": "pay now"}
    assert not E.dominates(a, b)


# ranking
def test_query_constraints_are_hard_filters():
    res = E.search("experiences", "evening activity with hotel pickup and flexible cancellation")
    assert res["results"] and all(e["config"]["pickup"] for e in res["results"])
    assert all(e["best_offer"]["refundable"] is True for e in res["results"])


def test_relevance_not_overridden_by_cheap_offer():
    top = E.search("experiences", "dinner cruise")["results"][0]
    assert top["id"] == "A-X31"  # pricier dinner cruise beats cheaper cruise without dinner


def test_evaluation_has_no_harmful_merges_or_rule_violations():
    r = evaluate.run()["verticals"]
    for v in E.VERTICALS:
        assert r[v]["matching"]["supplylens"]["harmful_merges"] == 0
        assert r[v]["offers"]["rule_violations"] == []


# API
def test_api_smoke_and_validation():
    c = TestClient(app)
    assert c.get("/healthz").json() == {"ok": True}
    assert c.get("/api/search", params={"vertical": "hotels", "q": "beach"}).status_code == 200
    assert c.get("/api/search", params={"vertical": "cars"}).status_code == 422
    assert c.get("/api/entity/hotels/A-H101").json()["records"] == ["A-H101", "B-77812", "C-DXB-5531"]
    assert c.post("/api/review", json={"vertical": "hotels", "a": "A-H101", "b": "nope", "decision": "match"}).status_code == 404
    assert c.post("/api/review", json={"vertical": "hotels", "a": "A-H101", "b": "B-77812", "decision": "merge"}).status_code == 422
    assert c.get("/").status_code == 200
