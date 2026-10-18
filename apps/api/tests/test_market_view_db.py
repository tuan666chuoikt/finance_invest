"""Postgres DISTINCT ON dedupe; needs FINVEST_DATABASE_URL (db name *_test), excluded from the kernel."""
import os
from datetime import UTC, date, datetime

import pytest
from finvest_api.market_view import SqlMarketView
from finvest_market_data.infrastructure.tables import bars_1d_src, metadata
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
