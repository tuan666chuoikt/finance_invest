"""Needs the compose db via FINVEST_DATABASE_URL; excluded from the kernel (-m "not db")."""

import os
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import Bar, CorporateAction, IndexBar, SymbolRecord, Tick
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
                  "bars_1d", "index_1d", "symbol_index_membership", "corporate_actions",
                  "corporate_action_log", "adj_factors", "recon_mismatches", "scenarios"):
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
    command.downgrade(cfg, "0004")  # 0005 round-trips on its own
    with eng.connect() as c:
        assert c.execute(text("SELECT to_regclass('symbol_index_membership')")).scalar_one() is None
    command.upgrade(cfg, "head")
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


def test_missed_manifest_does_not_overwrite_partial_or_complete(conn):
    q = text("SELECT status, rows FROM crawl_sessions")
    partial = manifest("partial")
    repo.upsert_crawl_session(conn, replace(partial, rows=145_184))
    repo.upsert_crawl_session(conn, replace(manifest("missed"), rows=0, symbols_fetched=0))
    assert conn.execute(q).one() == ("partial", 145_184)
    repo.upsert_crawl_session(conn, replace(manifest("complete"), rows=145_184))
    repo.upsert_crawl_session(conn, replace(manifest("missed"), rows=0))
    assert conn.execute(q).one() == ("complete", 145_184)


def test_ledger_keeps_the_richest_replay(conn):
    q = text("SELECT status, rows, symbols_fetched, checksum FROM crawl_sessions")
    big = replace(manifest("partial"), rows=145_184, symbols_fetched=400, checksum="sha256:big")
    repo.upsert_crawl_session(conn, big)
    repo.upsert_crawl_session(conn, replace(
        big, rows=2_578, symbols_fetched=9, checksum="sha256:small", reason="source_no_longer_serves"))
    assert conn.execute(q).one() == ("partial", 145_184, 400, "sha256:big")
    repo.upsert_crawl_session(conn, replace(big, status="complete"))
    assert conn.execute(q).one()[0] == "complete"
    repo.upsert_crawl_session(conn, replace(
        big, status="complete", rows=150_000, symbols_fetched=410, checksum="sha256:new"))
    assert conn.execute(q).one() == ("complete", 150_000, 410, "sha256:new")


def test_status_rank_is_never_lowered(conn):
    q = text("SELECT status, rows FROM crawl_sessions")
    repo.upsert_crawl_session(conn, replace(manifest("complete"), rows=4_949))
    repo.upsert_crawl_session(conn, replace(manifest("blocked"), rows=10_357))
    assert conn.execute(q).one() == ("complete", 4_949)
    repo.upsert_crawl_session(conn, replace(manifest("complete"), rows=5_000))
    assert conn.execute(q).one() == ("complete", 5_000)
    repo.upsert_crawl_session(conn, replace(manifest("partial"), rows=100))
    assert conn.execute(q).one() == ("complete", 5_000)


def test_new_day_with_zero_rows_is_inserted(conn):
    repo.upsert_crawl_session(conn, replace(manifest("missed"), rows=0))
    assert conn.execute(text("SELECT status, rows FROM crawl_sessions")).one() == ("missed", 0)


def test_missed_session_is_replaced_by_a_later_status(conn):
    repo.upsert_crawl_session(conn, replace(manifest("missed"), rows=0))
    repo.upsert_crawl_session(conn, manifest("complete"))
    assert repo.session_status(conn, "ticks", D) == "complete"


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


def test_last_bar_dates_is_the_latest_per_symbol(conn):
    repo.upsert_bars_1d_src(conn, [bar("AAA", 15), bar("AAA", 16), bar("BBB", 15)], T0)
    assert repo.last_bar_dates(conn) == {"AAA": date(2026, 10, 16), "BBB": date(2026, 10, 15)}


def test_upsert_listed_at_fills_only_null(conn):
    repo.upsert_symbols(conn, [sym("AAA"), sym("BBB")], T0)
    assert repo.upsert_listed_at(conn, {"AAA": date(2020, 1, 2), "ZZZ": D}) == 1  # unknown symbol ignored
    assert repo.upsert_listed_at(conn, {"AAA": date(2021, 5, 5), "BBB": D}) == 1  # AAA already set: kept
    got = {r.symbol: r.listed_at for r in repo.list_symbols(conn)}
    assert got == {"AAA": date(2020, 1, 2), "BBB": D}


def test_sync_index_membership_intervals_and_idempotence(conn):
    d1, d2 = date(2026, 10, 15), date(2026, 10, 16)
    assert repo.sync_index_membership(conn, "VN30", {"A", "B"}, d1) == (2, 0)
    assert repo.sync_index_membership(conn, "VN30", {"B", "C"}, d2) == (1, 1)
    q = text("SELECT symbol, valid_from, valid_to FROM symbol_index_membership ORDER BY symbol, valid_from")
    want = [("A", d1, d2), ("B", d1, None), ("C", d2, None)]
    assert [tuple(r) for r in conn.execute(q)] == want
    assert repo.sync_index_membership(conn, "VN30", {"B", "C"}, d2) == (0, 0)  # rerun: no write
    assert repo.sync_index_membership(conn, "VN30", set(), d2) == (0, 0)  # empty payload: no-op
    assert [tuple(r) for r in conn.execute(q)] == want


def test_repair_sessions_from_ticks(conn):
    T16, T15 = (datetime(2026, 10, 16, 8, 59, tzinfo=UTC),
                datetime(2026, 10, 15, 17, 30, tzinfo=UTC))  # both VN 10-16
    ins = text("INSERT INTO ticks VALUES (:s, :ts, :q, 25000, 100, 'B', 'kbs')")
    for i, s in enumerate(("AAA", "BBB", "CCC")):
        for q, ts in enumerate((T16, T15)):
            conn.execute(ins, {"s": s, "ts": ts, "q": q})
    led = text("INSERT INTO crawl_sessions (feed, trading_date, status, symbols_fetched, rows, checksum, "
               "reason) VALUES (:f, :d, 'partial', 1, :r, 'sha256:x', 'source_no_longer_serves')")
    conn.execute(led, {"f": "ticks", "d": date(2026, 10, 16), "r": 2})
    conn.execute(led, {"f": "ticks", "d": date(2026, 10, 15), "r": 6})  # no ticks on 10-15 VN: untouched
    conn.execute(led, {"f": "bars_1d", "d": date(2026, 10, 16), "r": 2})
    q = text("SELECT feed, trading_date, status, reason, rows, symbols_fetched, checksum "
             "FROM crawl_sessions ORDER BY 1, 2")
    before = conn.execute(q).all()
    assert repo.repair_crawl_sessions_from_ticks(conn) == 1
    after = conn.execute(q).all()
    assert after[2] == ("ticks", date(2026, 10, 16), "partial", "source_no_longer_serves", 6, 3, None)
    assert after[:2] == before[:2] and len(after) == 3  # bars_1d row and 10-15 row untouched, no insert
    assert repo.repair_crawl_sessions_from_ticks(conn) == 0
    assert conn.execute(q).all() == after


def test_repair_index_1d_value_nulls_out_of_band_rows_only(conn):
    def ib(d: int, v: int, value: int) -> IndexBar:
        return IndexBar("VNINDEX", date(2026, 10, d), Decimal("1700"), Decimal("1700"), Decimal("1700"),
                        Decimal("1700"), v, value)

    good = 20_000_000_000
    repo.upsert_index_1d(conn, [ib(12, 2, good), ib(13, 400_000, 0), ib(14, 400_000, good)])
    assert repo.repair_index_1d_value(conn) == 2  # ratio 1e10 and value 0; ratio 5e4 is in band
    rows = conn.execute(text("SELECT trading_date, v, value FROM index_1d ORDER BY 1")).all()
    assert [r[2] for r in rows] == [None, None, good] and [r[1] for r in rows] == [2, 400_000, 400_000]
    assert repo.repair_index_1d_value(conn) == 0


def ssi_src(conn, symbol: str, day: int, c: int, fetched_at: datetime, source: str = "ssi") -> None:
    conn.execute(
        text("INSERT INTO bars_1d_src VALUES (:s, :d, :src, :f, :c, :c, :c, :c, 10, 1000)"),
        {"s": symbol, "d": date(2026, 10, day), "src": source, "f": fetched_at, "c": c},
    )


def test_migration_0010_moves_ssi_rows_and_round_trips(eng):
    cfg = Config(str(INI))
    command.downgrade(cfg, "0009")
    old, new = datetime(2026, 10, 15, 9, tzinfo=UTC), datetime(2026, 10, 15, 10, tzinfo=UTC)
    with eng.begin() as c:
        for t in ("bars_1d_src", "symbols"):
            c.execute(text(f"TRUNCATE {t}"))
        ssi_src(c, "FPT", 15, 93_000, old)
        ssi_src(c, "FPT", 15, 93_500, new)  # newest fetched_at wins
        ssi_src(c, "VNM", 15, 60_000, new)
        ssi_src(c, "FPT", 15, 65_000, new, source="vci")
    for _ in range(2):  # down then up again is idempotent
        command.upgrade(cfg, "head")
        with eng.connect() as c:
            got = c.execute(text("SELECT symbol, c, nominal_kind, source, ref FROM bars_1d ORDER BY symbol"))
            assert got.all() == [
                ("FPT", 93_500, "observed", "ssi", None), ("VNM", 60_000, "observed", "ssi", None)]
            assert c.execute(text("SELECT source FROM bars_1d_src")).scalars().all() == ["vci"]
            col = text("SELECT count(*) FROM information_schema.columns "
                       "WHERE table_name='symbols' AND column_name='ca_checked_at'")
            assert c.execute(col).scalar_one() == 1
        command.downgrade(cfg, "0009")
        with eng.connect() as c:
            gone = text("SELECT to_regclass('bars_1d'), to_regclass('adj_factors')")
            assert c.execute(gone).one() == (None, None)
            # observed rows are not lost on downgrade (the older duplicate version is not restored)
            assert c.execute(text("SELECT count(*) FROM bars_1d_src WHERE source='ssi'")).scalar_one() == 2
    command.upgrade(cfg, "head")
    assert ScriptDirectory.from_config(cfg).get_heads() == ["0010"]


def test_upsert_bars_1d_observed_is_never_replaced_by_a_reconstruction(conn):
    f = datetime(2026, 10, 16, tzinfo=UTC)
    obs = replace(bar("FPT", c=93_500), source="ssi")
    rec = replace(bar("FPT", c=93_499), source="vci")
    one = {"nominal_kind": "observed", "fetched_at": f}
    assert repo.upsert_bars_1d(conn, [obs], ref={"FPT": 93_000}, **one) == 1
    assert repo.upsert_bars_1d(conn, [rec], nominal_kind="reconstructed", fetched_at=f) == 0  # G9
    q = text("SELECT c, nominal_kind, ref FROM bars_1d WHERE symbol='FPT'")
    assert conn.execute(q).one() == (93_500, "observed", 93_000)
    assert repo.upsert_bars_1d(conn, [obs], **one) == 1  # observed re-crawl wins
    conn.execute(text("TRUNCATE bars_1d"))
    assert repo.upsert_bars_1d(conn, [rec], nominal_kind="reconstructed", fetched_at=f) == 1
    assert repo.upsert_bars_1d(conn, [obs], **one) == 1  # observed over reconstructed
    assert conn.execute(q).one() == (93_500, "observed", None)
    with pytest.raises(IntegrityError):
        conn.execute(text("UPDATE bars_1d SET nominal_kind='guess'"))


def ca(ex: date = date(2026, 11, 5), event: str = "e1", **kw) -> CorporateAction:
    base = dict(symbol="FPT", type="cash_dividend", ex_date=ex, record_date=date(2026, 11, 6), pay_date=None,
                ratio_a=None, ratio_b=None, cash_per_share=1_000, issue_price=None, source="vci",
                source_event_id=event, public_date=None, title="t")
    return CorporateAction(**{**base, **kw})  # type: ignore[arg-type]


def test_upsert_corporate_actions_logs_each_changed_field_once(conn):
    t1, t2, t3 = (datetime(2026, 10, d, tzinfo=UTC) for d in (20, 21, 22))
    assert repo.upsert_corporate_actions(conn, [ca()], t1) == (1, 0)  # new row: no log
    moved = ca(ex=date(2026, 11, 7))
    assert repo.upsert_corporate_actions(conn, [moved], t2) == (1, 1)
    assert repo.upsert_corporate_actions(conn, [moved], t3) == (1, 0)  # re-run: no new log row
    assert conn.execute(text("SELECT field, old, new, changed_at FROM corporate_action_log")).all() == [
        ("ex_date", "2026-11-05", "2026-11-07", t2)]
    assert conn.execute(text("SELECT count(*), max(fetched_at) FROM corporate_actions")).one() == (1, t3)
    got = repo.corporate_actions_for(conn, ["FPT", "VNM"])
    assert got == {"FPT": [moved], "VNM": []}


def test_ca_symbols_in_order_and_mark_checked(conn):
    old, new = datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 10, 1, tzinfo=UTC)
    repo.upsert_symbols(conn, [sym(s) for s in ("VN30M", "SCEN", "NULLS", "OLD", "NEW")] + [
        sym("GONE", delisted=True)], old)
    repo.sync_index_membership(conn, "VN30", {"VN30M"}, D)
    conn.execute(text("INSERT INTO scenarios (name, symbol, style, amount_vnd, buy_date, created_at,"
                      " updated_at) VALUES ('s', 'SCEN', 'lump_sum', 1, '2026-01-02', now(), now())"))
    repo.mark_ca_checked(conn, ["OLD"], old)
    repo.mark_ca_checked(conn, ["NEW", "VN30M", "SCEN"], new)
    assert repo.ca_symbols_in_order(conn) == ["VN30M", "SCEN", "NULLS", "OLD", "NEW"]
    assert repo.ca_symbols_in_order(conn, limit=2) == ["VN30M", "SCEN"]


def test_adj_factors_round_trip_as_decimal(conn):
    rows = [(date(2026, 11, 5), "0.980000000000", None)]
    repo.replace_adj_factors(conn, "FPT", rows, "r1")
    repo.replace_adj_factors(conn, "FPT", rows, "r1")
    assert repo.adj_factors_for(conn, "FPT") == [(date(2026, 11, 5), Decimal("0.980000000000"), None)]
    assert conn.execute(text("SELECT factor::text FROM adj_factors")).scalar() == "0.980000000000"


def test_replace_recon_mismatches_is_idempotent(conn):
    rows = [(D, 65_000, 64_000, Decimal("1.5625"))]
    for _ in range(2):
        repo.replace_recon_mismatches(conn, "FPT", rows)
    assert conn.execute(text("SELECT count(*) FROM recon_mismatches")).scalar() == 1


def test_newest_src_bars_and_nominal_bars(conn):
    t1, t2 = datetime(2026, 10, 15, tzinfo=UTC), datetime(2026, 10, 16, tzinfo=UTC)
    repo.upsert_bars_1d_src(conn, [bar("FPT", c=100)], t1)
    repo.upsert_bars_1d_src(conn, [bar("FPT", c=101)], t2)
    repo.upsert_bars_1d_src(conn, [bar("FPT", day=14, c=90)], t1)
    assert repo.newest_src_bars(conn, "FPT", "vci") == [(date(2026, 10, 14), 90), (D, 101)]
    repo.upsert_bars_1d(conn, [bar("FPT", c=93_500)], nominal_kind="observed", fetched_at=t1,
                        ref={"FPT": 93_000})
    assert repo.nominal_bars(conn, "FPT") == [(D, 93_500, "observed", 93_000)]
