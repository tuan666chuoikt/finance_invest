"""Needs the compose db via FINVEST_DATABASE_URL; excluded from the kernel (-m "not db")."""

import os
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import Bar, IndexBar, SymbolRecord, Tick
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
        for t in ("ticks", "crawl_runs", "crawl_sessions", "data_anomalies", "symbols", "bars_1d_src",
                  "index_1d"):
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
    command.downgrade(cfg, "0003")  # 0004 round-trips on its own
    with eng.connect() as c:
        got = c.execute(text("SELECT to_regclass('bars_1d_src'), to_regclass('index_1d')")).one()
        assert got == (None, None)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0002")  # 0003 round-trips on its own
    with eng.connect() as c:
        assert c.execute(text("SELECT to_regclass('symbols')")).scalar_one() is None
    command.downgrade(cfg, "0001")  # and so does 0002
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


def sym(symbol: str, exchange="HOSE", delisted=False, delisted_at=None) -> SymbolRecord:
    return SymbolRecord(symbol, exchange, "STOCK", "Tên", "Name", "5500", delisted, "vci",  # type: ignore[arg-type]
                        None, delisted_at)


def test_upsert_symbols_keeps_exchange_and_delisted_at(conn):
    repo.upsert_symbols(conn, [sym("AAA", "HNX"), sym("BBB")], T0)
    d1, d2 = date(2026, 10, 15), date(2026, 10, 16)
    # V3 lists AAA as delisted without an exchange (placeholder UPCOM): the stored HNX stays
    repo.upsert_symbols(conn, [sym("AAA", "UPCOM", True, d1)], T0)
    repo.upsert_symbols(conn, [sym("AAA", "UPCOM", True, d2)], T0)  # a later run never moves delisted_at
    q = text("SELECT exchange, is_delisted, delisted_at FROM symbols WHERE symbol='AAA'")
    assert conn.execute(q).one() == ("HNX", True, d1)
    repo.upsert_symbols(conn, [sym("AAA", "HOSE")], T0)  # re-listed: flag flips, the date stays
    assert conn.execute(q).one() == ("HOSE", False, d1)
    assert [r.symbol for r in repo.list_symbols(conn, include_delisted=False)] == ["AAA", "BBB"]


def test_mark_delisted_only_absent_rows_and_empty_is_noop(conn):
    repo.upsert_symbols(conn, [sym("AAA"), sym("BBB"), sym("CCC", delisted=True, delisted_at=D)], T0)
    assert repo.mark_delisted(conn, set(), D) == 0
    assert repo.mark_delisted(conn, {"AAA", "CCC"}, date(2026, 10, 16)) == 1
    got = {r.symbol: (r.is_delisted, r.delisted_at) for r in repo.list_symbols(conn)}
    assert got == {"AAA": (False, None), "BBB": (True, date(2026, 10, 16)), "CCC": (True, D)}
    assert repo.mark_delisted(conn, {"AAA"}, date(2026, 10, 17)) == 0  # already delisted rows are left alone


def test_symbols_check_constraints(conn):
    with pytest.raises(IntegrityError), conn.begin_nested():
        repo.upsert_symbols(conn, [sym("AAA", "NYSE")], T0)


def bar(symbol: str, day: int = 15, c: int = 65001) -> Bar:
    ts = datetime(2026, 10, day - 1, 17, 0, tzinfo=UTC)  # 00:00 Asia/Ho_Chi_Minh
    return Bar(symbol, ts, 65819, 66637, 64819, c, 6618016, 474963630000, "vci")


def test_upsert_bars_1d_src_is_versioned_by_fetched_at(conn):
    bars = [bar("FPT", 15), bar("FPT", 16)]
    for _ in range(2):  # same fetched_at: idempotent
        repo.upsert_bars_1d_src(conn, bars, T0)
    count = text("SELECT count(*) FROM bars_1d_src")
    assert conn.execute(count).scalar_one() == 2
    repo.upsert_bars_1d_src(conn, [bar("FPT", 15, c=65100)], T0)  # same version: overwritten in place
    q = text("SELECT adj_c, value, trading_date FROM bars_1d_src WHERE trading_date='2026-10-15'")
    assert conn.execute(q).one() == (65100, 474963630000, D)
    repo.upsert_bars_1d_src(conn, bars, datetime(2026, 10, 16, 2, 0, tzinfo=UTC))  # later fetch: new versions
    assert conn.execute(count).scalar_one() == 4


def test_upsert_index_1d_latest_wins(conn):
    def ib(c: str) -> IndexBar:
        lv = Decimal
        return IndexBar("VNINDEX", D, lv("1700.10"), lv("1720.55"), lv("1699.99"), lv(c), 5, None)

    repo.upsert_index_1d(conn, [ib("1710.25")])
    repo.upsert_index_1d(conn, [ib("1711.50")])
    assert conn.execute(text("SELECT count(*), max(c) FROM index_1d")).one() == (1, Decimal("1711.50"))


def test_daily_coverage_per_exchange_includes_delisted(conn):
    repo.upsert_symbols(conn, [sym("AAA"), sym("BBB"), sym("CCC", delisted=True, delisted_at=D),
                               sym("DDD", "HNX")], T0)
    repo.upsert_bars_1d_src(conn, [bar("AAA"), bar("DDD")], T0)
    assert {k: str(v) for k, v in repo.daily_coverage(conn).items()} == {"HOSE": "33.3", "HNX": "100.0"}
    repo.upsert_bars_1d_src(conn, [bar("BBB")], T0)
    assert str(repo.daily_coverage(conn)["HOSE"]) == "66.7"
