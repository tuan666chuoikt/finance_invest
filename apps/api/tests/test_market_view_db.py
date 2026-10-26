"""Postgres DISTINCT ON dedupe; needs FINVEST_DATABASE_URL (db name *_test), excluded from the kernel."""
import os
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from finvest_api.market_view import SqlMarketView
from finvest_market_data.infrastructure.tables import (
    adj_factors,
    bars_1d,
    bars_1d_src,
    corporate_actions,
    metadata,
)
from sqlalchemy import create_engine, insert
from sqlalchemy.engine import make_url

URL = os.environ.get("FINVEST_DATABASE_URL")
pytestmark = [
    pytest.mark.db,
    pytest.mark.enable_socket,
    pytest.mark.skipif(not URL, reason="FINVEST_DATABASE_URL not set"),
    pytest.mark.skipif(bool(URL) and not (make_url(URL).database or "").endswith("_test"),
                       reason="db name must end in _test (the test drops its tables)"),
]


def test_newest_fetch_wins_and_as_of_hides_later_days():
    eng = create_engine(URL)  # type: ignore[arg-type]
    t = bars_1d_src
    metadata.drop_all(eng, tables=[t])
    metadata.create_all(eng, tables=[t])
    f1, f2 = datetime(2026, 10, 15, 8, tzinfo=UTC), datetime(2026, 10, 16, 8, tzinfo=UTC)
    d14, d15 = date(2026, 10, 14), date(2026, 10, 15)
    rows = [(d14, f1, 93_000), (d14, f2, 93_500), (d15, f1, 94_000)]
    with eng.begin() as c:
        c.execute(insert(t), [dict(symbol="FPT", trading_date=d, source="vci", fetched_at=f, adj_o=p,
                                   adj_h=p, adj_l=p, adj_c=p, v=1) for d, f, p in rows])
    v = SqlMarketView(eng)
    got = v.bars_1d("FPT", date(2026, 10, 1), date(2026, 10, 31), as_of=date(2026, 10, 14))
    assert [(b.trading_date, b.c) for b in got] == [(date(2026, 10, 14), 93_500)]  # 10-15 hidden by as_of
    assert v.snapshot() == f2
    assert len(v.bars_1d("FPT", date(2026, 10, 1), date(2026, 10, 31), as_of=date(2026, 10, 31))) == 2
    eng.dispose()


def test_a_day_only_in_bars_1d_is_served_and_moves_the_snapshot():
    eng = create_engine(URL)  # type: ignore[arg-type]
    metadata.drop_all(eng, tables=[bars_1d_src, bars_1d])
    metadata.create_all(eng, tables=[bars_1d_src, bars_1d])
    f1, f2 = datetime(2026, 10, 15, 8, tzinfo=UTC), datetime(2026, 10, 16, 9, tzinfo=UTC)
    d14, d15, d16 = date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)
    obs = dict(symbol="FPT", o=1, h=1, l=1, v=1, source="ssi", nominal_kind="observed")
    with eng.begin() as c:
        c.execute(insert(bars_1d_src), [dict(symbol="FPT", trading_date=d, source="vci", fetched_at=f1,
                                             adj_o=p, adj_h=p, adj_l=p, adj_c=p, v=1)
                                        for d, p in ((d14, 93_000), (d15, 94_000))])
        c.execute(insert(bars_1d), [dict(obs, trading_date=d15, c=99_000, fetched_at=f2),  # src row wins
                                    dict(obs, trading_date=d16, c=95_000, fetched_at=f2)])
    v = SqlMarketView(eng)
    got = v.bars_1d("FPT", date(2026, 10, 1), date(2026, 10, 31), as_of=date(2026, 10, 31))
    assert [(b.trading_date, b.c) for b in got] == [(d14, 93_000), (d15, 94_000), (d16, 95_000)]
    assert v.snapshot() == f2
    assert v.first_bar_date("FPT") == d14 and v.first_bar_date("NONE") is None
    eng.dispose()


T = [bars_1d, corporate_actions, adj_factors]
D1, D = date(2026, 10, 2), date(2026, 10, 5)  # D1 = last session before the ex-date D


def _seed_ca(eng, close=50_000, bar_at=datetime(2026, 10, 26, 9, 14, tzinfo=UTC),
             ca_at=datetime(2026, 10, 27, 9, 22, tzinfo=UTC)):
    """FPT observed close on D1, 1,000 VND cash dividend ex D, stored factor 0.98."""
    metadata.drop_all(eng, tables=[*T, bars_1d_src])
    metadata.create_all(eng, tables=[*T, bars_1d_src])
    with eng.begin() as c:
        c.execute(insert(bars_1d), [dict(symbol="FPT", trading_date=D1, o=close, h=close, l=close, c=close,
                                         v=1, source="ssi", nominal_kind="observed", fetched_at=bar_at)])
        c.execute(insert(corporate_actions), [dict(
            symbol="FPT", type="cash_dividend", ex_date=D, cash_per_share=1000, source="v5",
            source_event_id="1", fetched_at=ca_at)])
        c.execute(insert(adj_factors), [dict(symbol="FPT", ex_date=D, factor="0.980000000000", ca_id=1,
                                             rules_version="x")])


def test_adjusted_close_applies_factors_up_to_as_of_and_snapshot_follows_g11():
    eng = create_engine(URL)  # type: ignore[arg-type]
    _seed_ca(eng)
    ca_at, bar_at = datetime(2026, 10, 27, 9, 22, tzinfo=UTC), datetime(2026, 10, 26, 9, 14, tzinfo=UTC)
    v = SqlMarketView(eng)
    got = v.adjusted_close("FPT", D1, D, as_of=D)
    assert [(b.trading_date, b.c) for b in got] == [(D1, Decimal("49000.00"))]
    assert v.snapshot() == ca_at == datetime.fromisoformat("2026-10-27T16:22:00+07:00")
    v = SqlMarketView(eng)  # ex_date > as_of: not applied, does not move the snapshot
    assert [b.c for b in v.adjusted_close("FPT", D1, D, as_of=D1)] == [Decimal("50000.00")]
    assert v.snapshot() == bar_at == datetime.fromisoformat("2026-10-26T16:14:00+07:00")
    assert v.corporate_actions("FPT", date.min, D, as_of=D1) == []
    eng.dispose()


def test_bars_1d_serves_observed_close_on_the_source_adjusted_basis():
    eng = create_engine(URL)  # type: ignore[arg-type]
    _seed_ca(eng)
    v = SqlMarketView(eng)
    got = v.bars_1d("FPT", D1, D, as_of=D1)  # ex-date D is after as_of, but before today: the source has it
    assert [(b.trading_date, b.o, b.c) for b in got] == [(D1, 49_000, 49_000)]
    assert v.snapshot() == datetime(2026, 10, 27, 9, 22, tzinfo=UTC)
    [ca] = v.corporate_actions("FPT", date.min, D, as_of=D)
    assert (ca.ex_date, ca.event.cash_per_share) == (D, 1000)
    eng.dispose()
