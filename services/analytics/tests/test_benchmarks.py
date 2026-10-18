"""F-048 benchmarks: n/a handling, Decimal exactness, look-ahead, no recursion (numbers: golden 008-010)."""

import json

from finvest_analytics.domain.models import WhatIfRequest
from finvest_analytics.sim import run_whatif
from test_golden import build_view
from test_whatif_lumpsum import REQ, VIEW, walk

ETF = {"symbol": "E1VFVN30", "start": "2026-10-01", "end": "2026-10-15", "close": 20000, "last_close": 21000}
IDX = {"VNINDEX": {"2026-10-12": "1200.00", "2026-10-15": "1260.00"}}


def bench(*, etf=None, index=IDX, req=None, **vk):
    view = {**VIEW, "index": index, **vk}
    if etf is not False:
        view["extra"] = [{**ETF, **(etf or {})}]
    env = run_whatif(WhatIfRequest(**{**REQ, **(req or {})}), build_view(view))
    return env, env["result"]["benchmarks"]


def test_both_available_and_flags_not_duplicated():
    env, (v, e) = bench()
    assert v["available"] and e["available"] and v["investable"] is False and e["investable"] is True
    assert env["flags"] == sorted(set(env["flags"]))
    assert env["flags"].count("approximate") == 1


def test_etf_starting_after_buy_is_na_without_value():
    _, (v, e) = bench(etf={"start": "2026-10-13"})
    assert e == {"name": "E1VFVN30", "investable": True, "available": False, "first_available": "2026-10-13"}
    assert v["available"]  # the index is unaffected


def test_etf_gap_on_contribution_day_is_na_not_shifted():
    _, (_, e) = bench(etf={"drop": ["2026-10-12"]})
    assert e["available"] is False and e["first_available"] == "2026-10-01" and "value_vnd" not in e


def test_etf_missing_entirely_is_na_without_first():
    _, (_, e) = bench(etf=False)
    assert e["available"] is False and e["first_available"] is None


def test_vnindex_missing_bar_on_buy_or_sell_is_na_with_first_date():
    for gone in ("2026-10-12", "2026-10-15"):
        _, (v, _) = bench(
            index={
                "VNINDEX": {k: x for k, x in IDX["VNINDEX"].items() if k != gone} | {"2026-10-05": "1100.00"}
            }
        )
        assert v == {
            "name": "VN-Index",
            "investable": False,
            "available": False,
            "first_available": "2026-10-05",
        }


def test_vnindex_two_decimals_move_value_by_exact_ratio():
    # 10,000,000 x 1,234.57 / 1,234.56 = 10,000,081.0005 -> half-up 10,000,081
    _, (v, _) = bench(index={"VNINDEX": {"2026-10-12": "1234.56", "2026-10-15": "1234.57"}})
    assert v["value_vnd"]["value"] == "10000081"
    _, (v, _) = bench(
        index={"VNINDEX": {"2026-10-12": "1000.00", "2026-10-15": "1000.03"}}, req={"amount_vnd": 5_000_000}
    )
    assert v["value_vnd"]["value"] == "5000150"


def test_future_index_bar_is_not_used():
    _, (v, _) = bench(index={"VNINDEX": {**IDX["VNINDEX"], "2026-10-16": "9999.00"}}, end="2026-10-16")
    assert v["value_vnd"]["value"] == "10500000"


def test_figures_have_how_and_result_is_reproducible():
    env, bs = bench()
    figs = list(walk(bs))
    assert len(figs) == 6
    for f in figs:
        assert f["how"]["formula"] and f["how"]["inputs"] and f["how"]["cite"] == "PR-034", f
    assert bench()[0] == env
    assert json.dumps(bench()[0], sort_keys=True) == json.dumps(env, sort_keys=True)
