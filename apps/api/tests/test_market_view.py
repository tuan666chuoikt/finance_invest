"""SqlMarketView on SQLite; the Postgres-only dedupe is in test_market_view_db.py."""
from datetime import date, datetime
from decimal import Decimal

import pytest
from finvest_api.market_view import SqlMarketView
from finvest_market_data.infrastructure.tables import bars_1d_src, index_1d, metadata
from sqlalchemy import create_engine, insert

D = date


@pytest.fixture
def eng():
    e = create_engine("sqlite://")
    metadata.create_all(e)
    return e


def put_index(eng, code, days):
    with eng.begin() as c:
        c.execute(insert(index_1d), [dict(index_code=code, trading_date=d, o=1, h=1, l=1,
                                          c=Decimal("1260.0"), v=1) for d in days])


def put_bar(eng, sym, d, fetched, adj_c=93_500):
    with eng.begin() as c:
        c.execute(insert(bars_1d_src).values(symbol=sym, trading_date=d, source="vci", fetched_at=fetched,
                                             adj_o=adj_c, adj_h=adj_c, adj_l=adj_c, adj_c=adj_c, v=10))


def test_calendar_rules_range_skips_weekend(eng):
    got = SqlMarketView(eng).calendar(D(2026, 10, 16), D(2026, 10, 20))
    assert got == [D(2026, 10, 16), D(2026, 10, 19), D(2026, 10, 20)]


def test_calendar_outside_rules_uses_vnindex(eng):
    put_index(eng, "VNINDEX", [D(2016, 1, 4), D(2016, 1, 5), D(2016, 1, 6), D(2016, 1, 7)])
    put_index(eng, "VN30", [D(2016, 1, 8)])  # other indices are not sessions
    assert SqlMarketView(eng).calendar(D(2016, 1, 4), D(2016, 1, 8)) == [D(2016, 1, d) for d in (4, 5, 6, 7)]


def test_calendar_joins_both_sources(eng):
    put_index(eng, "VNINDEX", [D(2024, 12, 30), D(2024, 12, 31)])  # 2024-12-29 has no row
    got = SqlMarketView(eng).calendar(D(2024, 12, 29), D(2025, 1, 3))
    assert got == [D(2024, 12, 30), D(2024, 12, 31), D(2025, 1, 2), D(2025, 1, 3)]  # 2025-01-01 holiday


def test_index_1d_decimal_and_as_of(eng):
    put_index(eng, "VNINDEX", [D(2026, 10, 14), D(2026, 10, 15)])
    got = SqlMarketView(eng).index_1d("VNINDEX", D(2026, 10, 1), D(2026, 10, 31), as_of=D(2026, 10, 14))
    assert [b.trading_date for b in got] == [D(2026, 10, 14)]
    assert got[0].c == Decimal("1260.00") and str(got[0].c) == "1260.00"


def test_first_bar_date(eng):
    put_bar(eng, "FPT", D(2026, 10, 14), datetime(2026, 10, 15, 8))
    put_bar(eng, "FPT", D(2026, 10, 13), datetime(2026, 10, 15, 8))
    v = SqlMarketView(eng)
    assert v.first_bar_date("FPT") == D(2026, 10, 13)
    assert v.first_bar_date("ZZZ") is None


def test_snapshot_is_max_fetched_at_of_served_rows(eng):
    put_bar(eng, "FPT", D(2026, 10, 13), datetime(2026, 10, 15, 8))
    put_bar(eng, "FPT", D(2026, 10, 14), datetime(2026, 10, 16, 8))
    v = SqlMarketView(eng)
    b = v.bars_1d("FPT", D(2026, 10, 1), D(2026, 10, 31), as_of=D(2026, 10, 13))
    assert [(x.c, x.price_basis) for x in b] == [(93_500, "source_adjusted")]
    assert v.snapshot().replace(tzinfo=None) == datetime(2026, 10, 15, 8)  # hidden 10-14 bar not served
    v.bars_1d("FPT", D(2026, 10, 1), D(2026, 10, 31), as_of=D(2026, 10, 14))
    assert v.snapshot().replace(tzinfo=None) == datetime(2026, 10, 16, 8)
    assert v.price_basis() == "source_adjusted"
