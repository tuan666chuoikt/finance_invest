"""Lump-sum what-if: validation, look-ahead, reproducibility, `how` coverage, gaps (numbers: test_golden)."""

import json
from dataclasses import replace
from datetime import date, datetime

import pytest
from finvest_analytics.domain.models import WhatIfRequest
from finvest_analytics.domain.money import AnalyticsError
from finvest_analytics.sim import run_whatif
from test_golden import build_view

VIEW = {
    "symbol": "FPT",
    "start": "2026-10-01",
    "end": "2026-10-15",
    "close": 93500,
    "last_close": 100000,
    "snapshot": "2026-10-15T15:30:00",
}
REQ = {"symbol": "FPT", "amount_vnd": 10_000_000, "buy_date": "2026-10-12", "sell_date": "2026-10-15"}


def run(req=None, view=None, **vk):
    return run_whatif(WhatIfRequest(**{**REQ, **(req or {})}), view or build_view({**VIEW, **vk}))


def err(req=None, **vk):
    with pytest.raises(AnalyticsError) as e:
        run(req, **vk)
    return e.value


def test_validation_errors():
    assert err({"sell_date": "2026-10-09"}).code == "VALIDATION"
    e = err({"buy_date": "2026-09-30"})
    assert (e.code, e.details) == ("NO_DATA", {"first_available": "2026-10-01"})
    e = err({"buy_date": "2026-10-16", "sell_date": None})
    assert (e.code, e.details["last_available"]) == ("VALIDATION", "2026-10-15")
    assert err({"symbol": "XXX"}).code == "SYMBOL_UNKNOWN"
    # weekend buy and weekend sell around the same weekend: sell lands before buy after shifting
    assert err({"buy_date": "2026-10-10", "sell_date": "2026-10-11"}, end="2026-10-23").code == "VALIDATION"


def test_buy_day_without_bar_moves_forward():
    r = run(drop=["2026-10-12"])
    d = r["result"]["dates"]
    assert d["buy"] == "2026-10-13"
    assert {"field": "buy_date", "from": "2026-10-12", "to": "2026-10-13", "reason": "no_bar"} in d["shifts"]
    assert "fill_shifted" in r["flags"] and r["result"]["position"]["shares"]["value"] == "100"


def test_sell_none_uses_last_bar():
    assert run({"sell_date": None})["result"]["dates"]["sell"] == "2026-10-15"


def test_cagr_variants():
    # M = N + 365 days -> CAGR equals the plain return; M = N -> null with a note
    r = run({"sell_date": "2027-10-12"}, end="2027-10-12", snapshot="2027-10-12T15:30:00")["result"][
        "returns"
    ]
    assert r["cagr_pct"]["value"] == r["pl_pct"]["value"] == "6.1098"
    r = run({"sell_date": "2026-10-12"}, end="2026-10-12")["result"]["returns"]
    assert r["cagr_pct"] is None and r["cagr_note"]["how"]["formula"]


def test_no_look_ahead():
    view = build_view(VIEW)
    base = run_whatif(WhatIfRequest(**REQ), view)["result"]
    n = date(2026, 10, 12)
    view.bars["FPT"] = [
        b
        if b.trading_date <= n
        else replace(b, o=int(b.o * 1.3), h=int(b.h * 1.3), l=int(b.l * 1.3), c=int(b.c * 1.3))
        for b in view.bars["FPT"]
    ]
    moved = run_whatif(WhatIfRequest(**REQ), view)["result"]
    for k in ("contributions", "position"):
        assert moved[k] == base[k]
    assert moved["value"] != base["value"]


def test_reproducible():
    dump = lambda: json.dumps(run(), sort_keys=True)  # noqa: E731
    assert dump() == dump()


def walk(node):
    if isinstance(node, dict):
        if "value" in node and "unit" in node:
            yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def test_every_figure_has_how_and_cites():
    r = run()["result"]
    figs = list(walk(r))
    assert len(figs) >= 10
    for f in figs:
        assert f["how"]["formula"] and f["how"]["inputs"] and f["how"]["as_of"], f
    assert r["value"]["sell_fee_vnd"]["how"]["cite"] == r["value"]["sell_tax_vnd"]["how"]["cite"] == "VN§5"
    assert r["contributions"][0]["how"]["cite"] == "VN§5"
    assert r["position"]["shares"]["how"]["cite"] == "VN§4"


def test_nominal_basis_is_not_approximate():
    env = run(basis="nominal")
    assert env["approximate"] is False and "approximate" not in env["flags"]
    assert run()["price_basis"] == "source_adjusted"


def test_gap_carries_last_close():
    r = run(drop=["2026-10-14"])["result"]
    assert r["missing_sessions"] == ["2026-10-14"]
    assert {c["date"]: c["market_value"] for c in r["equity_curve"]}["2026-10-14"] == 9_985_975
    assert "missing_sessions" in run(drop=["2026-10-14"])["flags"]
    assert datetime.fromisoformat(run()["data_snapshot"]).utcoffset().total_seconds() == 7 * 3600
