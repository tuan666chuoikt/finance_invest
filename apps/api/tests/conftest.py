from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from finvest_api.deps import get_engine
from finvest_api.main import app
from finvest_market_data.infrastructure import tables
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
def make_client():
    """Factory: client over a fresh in-memory SQLite; `seed=False` leaves the tables empty."""
    def make(seed=True):
        eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        tables.metadata.create_all(eng)
        if seed:
            t = datetime(2026, 10, 14, 11, 0, tzinfo=UTC)
            def sym(s, vi, en, d=False):
                return dict(symbol=s, exchange="HOSE", type="STOCK", name_vi=vi, name_en=en, is_delisted=d,
                            delisted_at=date(2025, 1, 2) if d else None, source="vci", fetched_at=t)

            def bar(d, f):
                return dict(symbol="FPT", trading_date=d, source="vci", fetched_at=f,
                            adj_o=1, adj_h=1, adj_l=1, adj_c=1, v=1)

            with eng.begin() as c:
                c.execute(tables.symbols.insert(), [
                    sym("FPT", "FPT Corp", "FPT Corporation"), sym("FPTX", "FPT cũ", "FPT old", True),
                    sym("VNM", "Sữa Việt Nam", "Vinamilk")])
                c.execute(tables.bars_1d_src.insert(), [
                    bar(date(2026, 10, 14), t), bar(date(2026, 10, 15), t),
                    bar(date(2026, 10, 16), t),
                    bar(date(2026, 10, 16), datetime(2026, 10, 17, 3, 0, tzinfo=UTC)),
                ])
        app.dependency_overrides[get_engine] = lambda: eng
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()
