"""SupplyLens web API + demo UI. Run: uvicorn supplylens.app:app --reload"""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import engine as E
from . import evaluate

WEB = Path(__file__).resolve().parent.parent / "web"
Vertical = Literal["hotels", "experiences"]

app = FastAPI(title="SupplyLens", version="1.0.0",
              description="Explainable multi-supplier inventory layer. All data is synthetic.")


@app.get("/api/search")
def search(vertical: Vertical, q: str = Query("", max_length=200), refundable: bool = False,
           breakfast: bool = False, pickup: bool = False, adults: int = Query(2, ge=1, le=8),
           sort: Literal["recommended", "price"] = "recommended"):
    return E.search(vertical, q, refundable, breakfast, pickup, adults, sort)


@app.get("/api/entity/{vertical}/{entity_id}")
def entity(vertical: Vertical, entity_id: str, refundable: bool = False, breakfast: bool = False,
           pickup: bool = False, adults: int = Query(2, ge=1, le=8)):
    for e in E.build_entities(vertical, {"refundable": refundable, "breakfast": breakfast, "pickup": pickup, "adults": adults}):
        if entity_id in e["records"]:
            e["source_records"] = [E.RECORDS[vertical][r] for r in e["records"]]
            for o in e["offers"]:
                o["reliability"] = E.supplier_reliability(o["supplier"])
            return e
    raise HTTPException(404, "unknown entity")


@app.get("/api/raw/{vertical}")
def raw(vertical: Vertical):
    """Baseline view: every supplier record listed separately, as feeds deliver them."""
    return [{"id": r["id"], "supplier": r["supplier"], "name": r["name"], "area": r["area"]}
            for r in E.RECORDS[vertical].values()]


@app.get("/api/review")
def review_queue():
    items = []
    for v in E.VERTICALS:
        for d in E.pair_decisions(v):
            if d["machine"] == "review" or d["reviewed"]:
                d.update(vertical=v, a_record=E.RECORDS[v][d["a"]], b_record=E.RECORDS[v][d["b"]])
                items.append(d)
    return {"queue": items, "audit": E.AUDIT[::-1]}


class Review(BaseModel):
    vertical: Vertical
    a: str = Field(max_length=40)
    b: str = Field(max_length=40)
    decision: Literal["match", "distinct", "reset"]
    note: str = Field("", max_length=200)


@app.post("/api/review")
def post_review(r: Review):
    try:
        return E.review(r.vertical, r.a, r.b, r.decision, r.note)
    except KeyError:
        raise HTTPException(404, "unknown record")


@app.get("/api/eval")
def eval_report():
    return evaluate.run()


@app.get("/healthz")
def health():
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=WEB), name="static")
