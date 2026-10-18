import os

import pytest

OK = {"name": "FPT test", "symbol": "fpt", "style": "lump_sum", "amount_vnd": 10_000_000,
      "buy_date": "2025-10-12", "sell_date": None}


def _bad(c, field, **kw):
    r = c.post("/api/scenarios", json={**OK, **kw})
    assert r.status_code == 400, (field, r.json())
    assert r.json()["error"] == {**r.json()["error"], "code": "VALIDATION", "details": {"field": field}}


def test_crud(make_client):
    c = make_client()
    r = c.post("/api/scenarios", json=OK)
    assert r.status_code == 201
    a = r.json()
    assert a["symbol"] == "FPT" and a["created_at"].endswith("+07:00")
    b = c.post("/api/scenarios", json={**OK, "name": "second"}).json()
    assert [s["id"] for s in c.get("/api/scenarios").json()] == [b["id"], a["id"]]
    r = c.put(f"/api/scenarios/{a['id']}", json={**OK, "amount_vnd": 5_000_000})
    assert r.status_code == 200 and r.json()["amount_vnd"] == 5_000_000
    assert r.json()["updated_at"] > a["updated_at"] and r.json()["created_at"] == a["created_at"]
    assert c.delete(f"/api/scenarios/{a['id']}").status_code == 204
    for r in (c.delete(f"/api/scenarios/{a['id']}"), c.put(f"/api/scenarios/{a['id']}", json=OK)):
        assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_validation(make_client):
    c = make_client()
    _bad(c, "name", name="x" * 61)
    _bad(c, "amount_vnd", amount_vnd=0)
    _bad(c, "amount_vnd", amount_vnd=100_000_000_001)
    _bad(c, "amount_vnd", amount_vnd=1e11 + 1)
    _bad(c, "amount_vnd", amount_vnd="10,000,000")
    _bad(c, "amount_vnd", amount_vnd=1.5)
    _bad(c, "sell_date", sell_date="2025-10-11")
    assert c.get("/api/scenarios").json() == []


def test_symbol(make_client):
    c = make_client()
    r = c.post("/api/scenarios", json={**OK, "symbol": "ZZZ"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "SYMBOL_UNKNOWN" and r.json()["error"]["details"] == {"symbol": "ZZZ"}
    assert c.post("/api/scenarios", json={**OK, "symbol": "FPTX"}).status_code == 201  # delisted ok


@pytest.mark.db
@pytest.mark.skipif(not os.environ.get("FINVEST_DATABASE_URL"), reason="needs FINVEST_DATABASE_URL")
def test_migration_round_trip():
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")
    command.upgrade(cfg, "head")
