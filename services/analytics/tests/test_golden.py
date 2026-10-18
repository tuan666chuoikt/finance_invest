"""Generic golden runner: tests/golden/sim/*.json -> run_whatif -> compare `expected` leaves.

Case keys: view (symbol,start,end,close[,last_close,closes{date: close},drop,snapshot,basis]), request,
expected {dotted.path: str},
optional approx {path: tolerance}, flags_contain [..], error {code, details}. Paths resolve against `result`,
then against the envelope; digits index lists.
"""

import json
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from finvest_analytics.domain.models import WhatIfRequest
from finvest_analytics.domain.money import AnalyticsError
from finvest_analytics.fixtures import FixtureView, constant_series
from finvest_analytics.sim import run_whatif

CASES = sorted((Path(__file__).parent / "golden" / "sim").glob("*.json"))


def build_view(spec: dict) -> FixtureView:
    start, end = date.fromisoformat(spec["start"]), date.fromisoformat(spec["end"])
    drop = {date.fromisoformat(d) for d in spec.get("drop", [])}
    over = {date.fromisoformat(d): c for d, c in spec.get("closes", {}).items()}
    bars = [
        replace(
            b, o=over[b.trading_date], h=over[b.trading_date], l=over[b.trading_date], c=over[b.trading_date]
        )
        if b.trading_date in over
        else b
        for b in constant_series(spec["symbol"], start, end, spec["close"], last_close=spec.get("last_close"))
        if b.trading_date not in drop
    ]
    return FixtureView(
        {spec["symbol"]: bars},
        {},
        datetime.fromisoformat(spec["snapshot"]),
        spec.get("basis", "source_adjusted"),
    )


def dig(env: dict, path: str):
    node = env["result"] if path.split(".")[0] in env["result"] else env
    for k in path.split("."):
        node = node[int(k)] if k.isdigit() else node[k]
    return node


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.stem)
def test_golden(case: Path):
    spec = json.loads(case.read_text())
    view, req = build_view(spec["view"]), WhatIfRequest(**spec["request"])
    if "error" in spec:
        with pytest.raises(AnalyticsError) as e:
            run_whatif(req, view)
        assert e.value.code == spec["error"]["code"]
        assert e.value.details == spec["error"].get("details", {})
        return
    env = run_whatif(req, view)
    for flag in spec.get("flags_contain", []):
        assert flag in env["flags"]
    for path, want in spec["expected"].items():
        got = dig(env, path)
        if path in spec.get("approx", {}):
            assert abs(Decimal(str(got)) - Decimal(want)) <= Decimal(spec["approx"][path]), path
        else:
            assert str(got) == want, path
