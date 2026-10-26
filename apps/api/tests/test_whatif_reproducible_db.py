"""F-023: same inputs + snapshot + rules_version give byte-identical /whatif JSON on the SQL view."""
import json
import os
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from finvest_api.deps import get_engine
from finvest_api.main import app
from finvest_market_data.infrastructure.tables import (
    adj_factors,
    bars_1d,
    bars_1d_src,
    corporate_actions,
    index_1d,
    metadata,
)
from finvest_rules.costs import RULES_VERSION
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


def test_whatif_twice_is_byte_identical_with_bars_and_a_ca():
    eng = create_engine(URL)  # type: ignore[arg-type]
    tables = [bars_1d_src, bars_1d, corporate_actions, adj_factors, index_1d]
    metadata.drop_all(eng, tables=tables)
    metadata.create_all(eng, tables=tables)
    f = datetime(2026, 10, 15, 8, tzinfo=UTC)
    src = dict(symbol="FPT", source="vci", fetched_at=f, adj_o=93_500, adj_h=93_500, adj_l=93_500,
               adj_c=93_500, v=1)
    obs = dict(symbol="FPT", trading_date=date(2026, 10, 14), o=100_000, h=100_000, l=100_000, c=100_000, v=1,
               source="ssi", nominal_kind="observed", fetched_at=f)
    ca = dict(symbol="FPT", type="cash_dividend", ex_date=date(2026, 10, 15), cash_per_share=2000,
              source="v5", source_event_id="1", fetched_at=f)
    fac = dict(symbol="FPT", ex_date=date(2026, 10, 15), factor="0.980000000000", ca_id=1,
               rules_version=RULES_VERSION)
    with eng.begin() as c:
        c.execute(insert(bars_1d_src), [dict(src, trading_date=date(2026, 10, d)) for d in (12, 13)])
        # observed 100,000 on the 14th, ex-date the 15th: served as 98,000
        c.execute(insert(bars_1d), [obs])
        c.execute(insert(corporate_actions), [ca])
        c.execute(insert(adj_factors), [fac])
    app.dependency_overrides[get_engine] = lambda: eng
    try:
        body = {"symbol": "FPT", "amount_vnd": 10_000_000, "buy_date": "2026-10-12",
                "sell_date": "2026-10-14"}
        a, b = (TestClient(app).post("/api/whatif", json=body) for _ in range(2))
    finally:
        app.dependency_overrides.clear()
        eng.dispose()
    assert a.status_code == b.status_code == 200, a.text
    assert json.dumps(a.json(), sort_keys=True) == json.dumps(b.json(), sort_keys=True)
    assert a.json()["rules_version"] == RULES_VERSION
    # hand: cash 635,975 + 100 x 98,000 - fee 14,700 - tax 9,800 (the 100,000 observed close x 0.98)
    assert a.json()["result"]["value"]["liquidation_vnd"]["value"] == "10411475"
