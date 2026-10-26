"""Golden runner for tests/golden/adjust/*.json (G1-G9, G11-G13b) + no-look-ahead and determinism guards.

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
from finvest_analytics.adjust.recon import reconcile
from finvest_analytics.adjust.series import (
    cumulative,
    events_by_ex_date,
    forward_factors,
    reconstruct,
)
from finvest_analytics.domain.models import AdjBar, CorporateAction, DailyBar, Factor, NominalBar
from finvest_analytics.fixtures import FixtureView
from finvest_rules import CaEvent
from hypothesis import given
from hypothesis import strategies as st

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
        src_last = spec.get("src_last", {})  # per-row version `last` (R6a), optional
        src = [
            AdjBar("FPT", D(d), Decimal(a), D(src_last[d]) if d in src_last else None)
            for d, a in spec["src"].items()
        ]
        observed = {D(d): c for d, c in spec["observed"].items()}
        nominal, factors = reconstruct(src, events_by_ex_date(acts), observed)
        rec = reconcile(nominal, factors, src)  # no observed rows -> self-consistency, each day exact
        return {
            "recon_exact": f"{rec.exact_days}/{rec.checked}",
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
        "snapshot": view.snapshot().isoformat(),
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


def test_snapshot_ignores_unapplied_future_ca_row():
    fetched = datetime.fromisoformat("2026-10-26T16:14:00+07:00")
    late = CorporateAction(
        "FPT",
        D("2026-10-05"),
        CaEvent("cash_dividend", None, None, 1000, None),
        datetime.fromisoformat("2026-10-27T16:22:00+07:00"),
    )
    bars = [DailyBar("FPT", D("2026-10-02"), 50000, 50000, 50000, 50000, 1, "nominal", fetched)]
    view = FixtureView({"FPT": bars}, {}, fetched, "nominal", {"FPT": [late]})
    view.adjusted_close("FPT", date.min, date.max, as_of=D("2026-10-02"))
    assert view.snapshot() == fetched


RECON_CASES = [c for c in CASES if json.loads(c.read_text())["op"] == "reconstruct"]


@given(st.integers(0, 3), st.sampled_from(RECON_CASES))
def test_property_two_versions_reconstruct_same_nominal(overlap, case):
    """Split a golden `src` in two (R6a): V0 = rows before the first ex-date (last_v = its last day, so
    nominal itself), V1 = the rest plus `overlap` earlier days, each adjusted by the factors up to its own
    last_v. The newest row per date is read, as the crawler does: same nominal."""
    spec = json.loads(case.read_text())
    if spec["observed"] or "src_last" in spec:
        return
    acts = actions(spec)
    dates = sorted(D(d) for d in spec["src"])
    first_ex = min(a.ex_date for a in acts)
    pre = [d for d in dates if d < first_ex]
    if not pre or first_ex not in dates:  # nothing before it, or an event the source never saw
        return
    base = run(spec)
    nominal = {D(d): c for d, c in base["nominal"].items()}
    factors = [Factor("FPT", D(d), Decimal(f)) for d, f in base["factors"].items()]
    cut = max(0, len(pre) - overlap)
    v0 = [AdjBar("FPT", d, Decimal(nominal[d]), pre[-1]) for d in pre[:cut]]
    v1 = [
        AdjBar(
            "FPT", d, (nominal[d] * cumulative(factors, d, dates[-1])).quantize(Decimal("0.01")), dates[-1]
        )
        for d in dates[cut:]
    ]
    got, _ = reconstruct(v0 + v1, events_by_ex_date(acts), {})
    assert {b.trading_date: b.c for b in got} == nominal
