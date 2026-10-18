from datetime import date, timedelta
from decimal import Decimal

import pytest
from finvest_analytics.domain.models import Ctx, figure
from finvest_analytics.domain.money import fee, lot_cost_min, max_qty, pct, round_half_up
from hypothesis import given
from hypothesis import strategies as st

R = Decimal("0.0015")


def test_golden():
    assert max_qty(10_000_000, 93_500, 100, R) == 100
    assert fee(100, 93_500, R) == 14_025
    assert lot_cost_min(93_500, 100, R) == 9_364_025
    assert max_qty(5_000_000, 93_500, 100, R) == 0
    assert round_half_up(Decimal("2.5")) == 3 and round_half_up(Decimal("2.4")) == 2


def test_pct_and_figure():
    assert pct(1, 3) == Decimal("33.3333")
    with pytest.raises(ZeroDivisionError):
        pct(1, 0)
    f = figure(Decimal("1.23456"), "pct", "a/b", {"a": 1, "b": Decimal("2.5")}, Ctx("t", "v1"), "VN§5")
    assert f.value == "1.2346" and f.how.inputs == {"a": "1", "b": "2.5000"} and f.how.cite == "VN§5"


@given(st.integers(1, 10**11), st.integers(10, 10**6).map(lambda x: x * 10),
       st.decimals(0, Decimal("0.0045"), places=4))
def test_max_qty_property(cash, price, rate):
    q = max_qty(cash, price, 100, rate)
    assert q % 100 == 0
    assert q * price + fee(q, price, rate) <= cash
    assert (q + 100) * price + fee(q + 100, price, rate) > cash


@given(st.integers(0, 120), st.integers(0, 120), st.integers(0, 120))
def test_fixture_as_of_guard(a, b, c):
    from datetime import datetime

    from finvest_analytics.fixtures import FixtureView, constant_series
    d0 = date(2026, 1, 1)
    v = FixtureView({"X": constant_series("X", d0, d0 + timedelta(150), 100)}, {}, datetime(2026, 1, 1))
    as_of = d0 + timedelta(a)
    rows = v.bars_1d("X", d0 + timedelta(b), d0 + timedelta(b + c), as_of=as_of)
    assert all(r.trading_date <= as_of for r in rows)
