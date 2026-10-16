"""Needs the compose db via FINVEST_DATABASE_URL; excluded from the kernel (-m "not db")."""

import os
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import Tick
from finvest_market_data.infrastructure import repositories as repo
from finvest_market_data.infrastructure.tables import ticks
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

URL = os.environ.get("FINVEST_DATABASE_URL")
pytestmark = [
    pytest.mark.db,
    pytest.mark.enable_socket,
    pytest.mark.skipif(not URL, reason="FINVEST_DATABASE_URL not set"),
    # the fixture runs `alembic downgrade base` (drops every table): never on the real db
    pytest.mark.skipif(
        bool(URL) and not (make_url(URL).database or "").endswith("_test"),
        reason="db name must end in _test (tests drop all tables)",
    ),
]
INI = Path(__file__).parents[3] / "apps" / "api" / "alembic.ini"
D = date(2026, 10, 15)
T0 = datetime(2026, 10, 15, 2, 0, 0, tzinfo=UTC)


def tick(seq: int, price: int = 25_000, side: str | None = "B") -> Tick:
    return Tick("FPT", T0, seq, price, 100, side, "kbs")  # type: ignore[arg-type]


@pytest.fixture(scope="module")
def eng():
    cfg = Config(str(INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    e = repo.engine(URL)  # type: ignore[arg-type]
    yield e
    e.dispose()


@pytest.fixture
def conn(eng):
    with eng.begin() as c:
        for t in ("ticks", "crawl_runs", "crawl_sessions", "data_anomalies"):
            c.execute(text(f"TRUNCATE {t}"))
        yield c


def test_migration_round_trip_and_timescale(eng):
    cfg = Config(str(INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    with eng.connect() as c:
        assert c.execute(
            text("SELECT hypertable_name FROM timescaledb_information.hypertables")
        ).scalars().all() == ["ticks"]
        jobs = (
            c.execute(
                text("SELECT proc_name FROM timescaledb_information.jobs WHERE hypertable_name='ticks'")
            )
            .scalars()
            .all()
        )
        assert "policy_compression" in jobs
    command.downgrade(cfg, "-1")  # 0002 round-trips on its own
    with eng.connect() as c:
        cols = text("SELECT 1 FROM information_schema.columns WHERE column_name='symbols_no_trades'")
        assert not c.execute(cols).first()
    command.upgrade(cfg, "head")


def test_upsert_ticks_idempotent_and_counts_changes(conn):
    rows = [tick(1), tick(2), tick(3, side=None)]
    assert repo.upsert_ticks(conn, rows) == 0
    assert repo.upsert_ticks(conn, rows) == 0
    assert conn.execute(text("SELECT count(*) FROM ticks")).scalar_one() == 3
    assert repo.upsert_ticks(conn, [tick(1), tick(2, price=26_000), tick(3, side=None)]) == 1
    assert conn.execute(text("SELECT price FROM ticks WHERE seq=2")).scalar_one() == 26_000
    assert conn.execute(text("SELECT count(*) FROM ticks")).scalar_one() == 3


def test_upsert_ticks_spans_batches(conn):
    n = repo.BATCH + 7
    assert repo.upsert_ticks(conn, [tick(i) for i in range(1, n + 1)]) == 0
    assert conn.execute(text("SELECT count(*) FROM ticks")).scalar_one() == n


def test_side_check(conn):
    with pytest.raises(IntegrityError), conn.begin_nested():
        conn.execute(
            ticks.insert().values(symbol="X", ts=T0, seq=1, price=1, volume=1, side="X", source="kbs")
        )


def manifest(status: str) -> Manifest:
    skipped = (("ABC", "http_429"),)
    return Manifest("ticks", D, "kbs", T0, T0, status, None, 10, 3, "sha256:ab", 2, skipped, ("XYZ",))


def test_crawl_session_upsert_and_status(conn):
    assert repo.session_status(conn, "ticks", D) is None
    repo.upsert_crawl_session(conn, manifest("partial"))
    repo.upsert_crawl_session(conn, manifest("complete"))
    assert conn.execute(text("SELECT count(*) FROM crawl_sessions")).scalar_one() == 1
    assert repo.session_status(conn, "ticks", D) == "complete"
    assert conn.execute(text("SELECT symbols_skipped, symbols_no_trades FROM crawl_sessions")).one() == (1, 1)


def test_fail_unfinished_runs(conn):
    rid = repo.insert_crawl_run(conn, "ticks", D, T0)
    assert repo.fail_unfinished_runs(conn, "ticks", D) == 1
    assert conn.execute(
        text("SELECT status, reason, finished_at IS NOT NULL FROM crawl_runs WHERE id=:i"), {"i": rid}
    ).one() == ("failed", "interrupted", True)
    assert repo.fail_unfinished_runs(conn, "ticks", D) == 0


def test_crawl_run_and_anomaly(conn):
    rid = repo.insert_crawl_run(conn, "ticks", D, T0)
    repo.finish_crawl_run(conn, rid, "ok", None, 5, 3, "data/raw/ticks/2026-10-15/_manifest.json")
    assert conn.execute(
        text("SELECT status, finished_at IS NOT NULL FROM crawl_runs WHERE id=:i"), {"i": rid}
    ).one() == ("ok", True)
    repo.insert_anomaly(conn, "FPT", D, "duplicate_tick", "seq=2")
    assert conn.execute(text("SELECT rule FROM data_anomalies")).scalar_one() == "duplicate_tick"
