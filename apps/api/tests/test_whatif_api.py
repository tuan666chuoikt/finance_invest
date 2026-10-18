import time
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from finvest_analytics.fixtures import FixtureView, constant_series
from finvest_api.main import app
from finvest_api.routes.whatif import get_market_view
from test_market_view import put_bar

SNAP = datetime(2026, 10, 15, 15, 30)
GOLDEN_001 = {"symbol": "FPT", "amount_vnd": 10_000_000, "buy_date": "2026-10-12", "sell_date": "2026-10-15"}


@pytest.fixture
def post():
    def go(body, bars=None):
        bars = bars or constant_series(
            "FPT", date(2026, 10, 1), date(2026, 10, 15), 93_500, last_close=100_000)
        app.dependency_overrides[get_market_view] = lambda: FixtureView({"FPT": bars}, {}, SNAP)
        return TestClient(app).post("/api/whatif", json=body)

    yield go
    app.dependency_overrides.clear()


def test_golden_001(post):
    r = post(GOLDEN_001)
    assert r.status_code == 200
    j = r.json()
    assert j["result"]["value"]["liquidation_vnd"]["value"] == "10610975"  # hand-computed in golden 001
    assert j["approximate"] is True


@pytest.mark.parametrize("body", [{**GOLDEN_001, "amount_vnd": 0}, {**GOLDEN_001, "fill_rule": "open"}])
def test_bad_body_is_400(post, body):
    r = post(body)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION"


def test_unknown_symbol_422(post):
    r = post({**GOLDEN_001, "symbol": "NOPE"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "SYMBOL_UNKNOWN"


def test_buy_before_first_bar_422(post):
    r = post({**GOLDEN_001, "buy_date": "2026-09-01"})
    assert r.status_code == 422
    e = r.json()["error"]
    assert e["code"] == "NO_DATA"
    assert e["details"]["first_available"] == "2026-10-01"


def test_budget_20_requests_under_2s(post):  # N2
    bars = constant_series("FPT", date(2016, 1, 4), date(2026, 1, 4), 50_000)
    body = {"symbol": "FPT", "amount_vnd": 100_000_000, "buy_date": "2016-01-04", "sell_date": "2026-01-02"}
    post(body, bars)  # installs the override; also warms imports
    c = TestClient(app)
    t0 = time.perf_counter()
    for _ in range(20):
        assert c.post("/api/whatif", json=body).status_code == 200
    dt = time.perf_counter() - t0
    print(f"N2 budget: 20 requests in {dt:.3f}s")
    assert dt < 2


@pytest.fixture
def sql_eng():
    """Real SqlMarketView on SQLite: FPT bars 14-16 Oct, nothing served yet (live L1)."""
    from finvest_market_data.infrastructure.tables import metadata
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    metadata.create_all(eng)
    for d in (14, 15, 16):
        # naive local time: SQLite drops tzinfo and iso_vn reads naive as Asia/Ho_Chi_Minh
        put_bar(eng, "FPT", date(2026, 10, d), datetime(2026, 10, 17, 10, 0))
    yield eng


@pytest.fixture
def sql_post(sql_eng):
    from finvest_api.market_view import SqlMarketView

    app.dependency_overrides[get_market_view] = lambda: SqlMarketView(sql_eng)
    yield lambda body: TestClient(app).post("/api/whatif", json=body)
    app.dependency_overrides.clear()


SQL_BODY = {"symbol": "FPT", "amount_vnd": 10_000_000, "buy_date": "2026-10-14",
            "sell_date": "2026-10-16", "style": "lump_sum"}


def test_sql_view_first_request_ok(sql_post):
    r = sql_post(SQL_BODY)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["result"]["dates"]["buy"] == "2026-10-14"
    assert j["data_snapshot"] == "2026-10-17T10:00:00+07:00"


def test_sql_view_no_calendar_is_400(sql_post, sql_eng):
    # a 2024 bar passes the first-bar check; no VNINDEX rows for 2024 -> empty calendar
    put_bar(sql_eng, "FPT", date(2024, 1, 2), datetime(2026, 10, 17, 10, 0))
    r = sql_post({**SQL_BODY, "buy_date": "2024-01-02"})
    assert r.status_code == 400
    assert r.json()["error"]["details"]["reason"] == "no_trading_day_near_buy"
