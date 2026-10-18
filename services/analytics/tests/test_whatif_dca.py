"""Monthly DCA: schedule, look-ahead per contribution, curve steps, flags, `how` (numbers: golden 005-007)."""

import json
from dataclasses import replace
from datetime import date, timedelta

from finvest_analytics.domain.models import WhatIfRequest
from finvest_analytics.sim import run_whatif
from finvest_analytics.sim.dca import schedule
from test_golden import build_view
from test_whatif_lumpsum import walk

VIEW = {
    "symbol": "FPT",
    "start": "2026-01-01",
    "end": "2026-06-30",
    "close": 93500,
    "last_close": 100000,
    "snapshot": "2026-06-30T15:30:00",
}
REQ = {
    "symbol": "FPT",
    "amount_vnd": 2_000_000,
    "buy_date": "2026-01-15",
    "sell_date": "2026-06-30",
    "style": "dca",
}


def run(req=None, view=None):
    return run_whatif(WhatIfRequest(**{**REQ, **(req or {})}), view or build_view(VIEW))


def every_day(start: date, end: date) -> list[date]:
    return [start + timedelta(i) for i in range((end - start).days + 1)]


def test_schedule_clamps_day_and_drops_after_end():
    cal = every_day(date(2026, 1, 1), date(2027, 3, 31))
    got = [a for _, a in schedule(date(2026, 1, 31), date(2026, 5, 31), cal)]
    assert got == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
        date(2026, 5, 31),
    ]
    # leap year: day 31 clamps to Feb 29; year wraps December -> January
    assert date(2028, 2, 29) in [
        a
        for _, a in schedule(
            date(2027, 12, 31), date(2028, 2, 29), cal + every_day(date(2027, 4, 1), date(2028, 3, 31))
        )
    ]
    shifts: list[dict] = []
    weekdays = [d for d in cal if d.weekday() < 5]
    assert schedule(date(2026, 1, 31), date(2026, 5, 29), weekdays, shifts)[-1] == (
        date(2026, 4, 30),
        date(2026, 4, 30),
    )
    assert shifts[-1] == {
        "field": "contribution",
        "from": "2026-05-31",
        "to": "2026-06-01",
        "reason": "after_end",
    }


def test_no_look_ahead_per_contribution():
    base = run()["result"]
    for i, c in enumerate(base["contributions"]):
        t, view = date.fromisoformat(c["date"]), build_view(VIEW)
        view.bars["FPT"] = [
            b if b.trading_date <= t else replace(b, o=b.o * 2, h=b.h * 2, l=b.l * 2, c=b.c * 2)
            for b in view.bars["FPT"]
        ]
        moved = run(view=view)["result"]["contributions"]
        assert moved[: i + 1] == base["contributions"][: i + 1], t


def test_equity_curve_invested_steps_on_contribution_days():
    r = run()["result"]
    steps = [
        (a["date"], a["invested"])
        for a, b in zip(r["equity_curve"], r["equity_curve"][1:] + [None])
        if b is None or a["invested"] != b["invested"]
    ]
    assert [s[1] for s in steps] == [2_000_000 * k for k in range(1, 7)]
    assert r["equity_curve"][0]["invested"] == 2_000_000 and r["equity_curve"][-1]["invested"] == 12_000_000
    by_day = {c["date"]: c["invested"] for c in r["equity_curve"]}
    assert by_day["2026-02-13"] == 2_000_000 and by_day["2026-02-16"] == 4_000_000


def test_dca_note_how_and_reproducible():
    r = run()["result"]
    assert r["returns"]["cagr_pct"] is None and "no IRR" in r["returns"]["cagr_note"]["text"]
    for f in walk(r):
        assert f["how"]["formula"] and f["how"]["inputs"] and f["how"]["as_of"], f
    assert json.dumps(run(), sort_keys=True) == json.dumps(run(), sort_keys=True)


def test_rules_unverified_flags_on_both_styles_and_fee_override():
    want = ["rules_unverified:buy_fee_rate", "rules_unverified:sell_fee_rate"]
    assert [f for f in run()["flags"] if f.startswith("rules_")] == want
    assert [f for f in run({"style": "lump_sum"})["flags"] if f.startswith("rules_")] == want
    assert not [f for f in run({"fee_rate": "0.001"})["flags"] if f.startswith("rules_")]


def test_contribution_day_without_bar_moves_forward():
    r = run(view=build_view({**VIEW, "drop": ["2026-04-15"]}))
    assert r["result"]["contributions"][3]["date"] == "2026-04-16"
    assert {"field": "contribution", "from": "2026-04-15", "to": "2026-04-16", "reason": "no_bar"} in r[
        "result"
    ]["dates"]["shifts"]
