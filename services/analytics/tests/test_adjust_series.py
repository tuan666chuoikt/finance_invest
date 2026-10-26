"""Golden runner for tests/golden/adjust/*.json (G1-G9, G11, G12) + no-look-ahead and determinism guards.

Case keys: hand[], op (adjusted | reconstruct), events[{ex_date, type, ratio_a, ratio_b, cash_per_share,
issue_price, fetched_at}]; adjusted: symbol, bars_fetched_at, nominal{date: close}, as_of; reconstruct:
src{date: A}, observed{date: close}; expected: factors{ex_date: f}, adj / nominal {date: value},
absent[dates], snapshot.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from finvest_analytics.adjust.series import (
    cumulative,
    events_by_ex_date,
    forward_factors,
    reconstruct,
)
from finvest_analytics.domain.models import AdjBar, CorporateAction, DailyBar, Factor, NominalBar
from finvest_analytics.fixtures import FixtureView
from finvest_rules import CaEvent

CASES = sorted((Path(__file__).parent / "golden" / "adjust").glob("*.json"))
D = date.fromisoformat


def actions(spec: dict) -> list[CorporateAction]:
    return [
        CorporateAction(
            "FPT",
            D(e["ex_date"]),
            CaEvent(
                e["type"], e.get("ratio_a"), e.get("ratio_b"), e.get("cash_per_share"), e.get("issue_price")
            ),
            datetime.fromisoformat(e["fetched_at"]),
        )
        for e in spec["events"]
    ]


def run(spec: dict) -> dict:
    """Execute a case and return everything it computed as strings (stable, JSON-serialisable)."""
    acts = actions(spec)
    if spec["op"] == "reconstruct":
        src = [AdjBar("FPT", D(d), Decimal(a)) for d, a in spec["src"].items()]
        observed = {D(d): c for d, c in spec["observed"].items()}
        nominal, factors = reconstruct(src, events_by_ex_date(acts), observed)
        return {
            "nominal": {str(b.trading_date): b.c for b in nominal},
            "kinds": sorted({b.nominal_kind for b in nominal}),
            "factors": {str(f.ex_date): str(f.f) for f in factors},
        }
    fetched = datetime.fromisoformat(spec["bars_fetched_at"])
    bars = [DailyBar("FPT", D(d), c, c, c, c, 1, "nominal", fetched) for d, c in spec["nominal"].items()]
    as_of = D(spec["as_of"])
    view = FixtureView({"FPT": bars}, {}, fetched, "nominal", {"FPT": acts})
    nominal_bars = [
        NominalBar("FPT", b.trading_date, b.c, "observed") for b in bars if b.trading_date <= as_of
    ]
    factors = forward_factors("FPT", nominal_bars, events_by_ex_date([a for a in acts if a.ex_date <= as_of]))
    return {
        "factors": {str(f.ex_date): str(f.f) for f in factors},
        "adj": {
            str(b.trading_date): str(b.c) for b in view.adjusted_close("FPT", date.min, date.max, as_of=as_of)
        },
        "snapshot": view.snapshot(as_of).isoformat(),
    }


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.stem)
def test_golden(case: Path):
    spec = json.loads(case.read_text())
    got = run(spec)
    for key, want in spec["expected"].items():
        if key == "absent":
            assert not set(want) & set(got.get("adj", got.get("nominal", {}))), key
        elif isinstance(want, dict) and key == "factors":
            assert got[key] == want, key  # factors are compared whole: no stray or missing ex-date
        elif isinstance(want, dict):
            assert {k: got[key][k] for k in want} == want, key
        else:
            assert got[key] == want, key
    assert json.dumps(run(spec), sort_keys=True) == json.dumps(got, sort_keys=True)  # R4/R9: same bytes


def test_reconstructed_rows_are_flagged_and_events_after_last_bar_ignored():
    spec = json.loads((CASES[0].parent / "007-g7-reconstruct-cash.json").read_text())
    spec["events"].append(
        {
            "ex_date": "2026-11-02",
            "type": "cash_dividend",
            "cash_per_share": 500,
            "fetched_at": "2026-10-26T16:14:00+07:00",
        }
    )  # the source could not know it (R6)
    got = run(spec)
    assert got["kinds"] == ["reconstructed"]
    assert list(got["factors"]) == ["2026-10-05"]


def test_no_look_ahead_shifted_future_changes_nothing():
    spec = json.loads((CASES[0].parent / "006b-g6-as-of-between.json").read_text())
    base = run(spec)
    spec["nominal"]["2026-10-07"] *= 3  # future bar and future ex-date move; as_of 10-06 must not notice
    spec["events"][1]["ratio_b"] = 9
    assert run(spec) == base


def test_cumulative_uses_stored_rows_and_open_lower_bound():
    fs = [
        Factor("X", date(2026, 10, 5), Decimal("0.98")),
        Factor("X", date(2026, 10, 7), Decimal("0.769230769231")),
    ]
    assert cumulative(fs, date(2026, 10, 5), date(2026, 10, 9)) == Decimal(
        "0.769230769231"
    )  # ex-date itself excluded
    assert cumulative(fs, date(2026, 10, 4), date(2026, 10, 6)) == Decimal("0.980000000000")
