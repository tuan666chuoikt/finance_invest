"""Per-press recompute on a real db (needs FINVEST_DATABASE_URL, db name *_test; excluded from the kernel).
Hand numbers are tech plan sprint-05 G7, G9, G12."""

import gzip
import os
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from finvest_crawler.adapters.vci.events import parse_events
from finvest_crawler.adapters.vci.source import parse_bars
from finvest_crawler.feeds.recompute import recompute, recompute_set
from finvest_market_data.domain.models import Bar, CorporateAction
from finvest_market_data.infrastructure import repositories as repo
from sqlalchemy import text
from sqlalchemy.engine import make_url

URL = os.environ.get("FINVEST_DATABASE_URL")
pytestmark = [
    pytest.mark.db,
    pytest.mark.enable_socket,
    pytest.mark.skipif(not URL, reason="FINVEST_DATABASE_URL not set"),
    pytest.mark.skipif(bool(URL) and not (make_url(URL).database or "").endswith("_test"),
                       reason="db name must end in _test (tests drop all tables)"),
]
INI = Path(__file__).parents[3] / "apps" / "api" / "alembic.ini"
FIX = Path(__file__).parent / "fixtures" / "vci"
VN = ZoneInfo("Asia/Ho_Chi_Minh")
F1 = datetime(2026, 10, 15, 9, tzinfo=UTC)
D = date(2026, 10, 15)  # ex-date; D-1 = 10-14, D-2 = 10-13


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
    with eng.connect() as c:
        for t in ("symbols", "bars_1d_src", "bars_1d", "corporate_actions", "corporate_action_log",
                  "adj_factors", "data_anomalies", "crawl_runs"):
            c.execute(text(f"TRUNCATE {t}"))
        c.commit()
        yield c


def bar(d: date, c: int, sym="AAA") -> Bar:
    return Bar(sym, datetime.combine(d, time(), VN).astimezone(UTC), c, c, c, c, 1000, None, "vci")


def src(conn, closes: dict[date, int], sym="AAA") -> None:
    repo.upsert_bars_1d_src(conn, [bar(d, c, sym) for d, c in closes.items()], F1)


def event(ex: date, eid="e1", sym="AAA", **kw) -> CorporateAction:
    base = dict(symbol=sym, type="cash_dividend", ex_date=ex, record_date=None, pay_date=None, ratio_a=None,
                ratio_b=None, cash_per_share=1_000, issue_price=None, source="vci_iq", source_event_id=eid,
                public_date=None, title="t")
    return CorporateAction(**{**base, **kw})  # type: ignore[arg-type]


def stored(conn):
    f = conn.execute(text("SELECT ex_date, factor::text, ca_id, rules_version FROM adj_factors "
                          "ORDER BY 1")).all()
    b = conn.execute(text("SELECT symbol, trading_date, o, h, l, c, v, nominal_kind, fetched_at FROM bars_1d "
                          "ORDER BY 1, 2")).all()
    return f, b


def test_g7_cash_event_reconstructs_the_pre_ex_close_and_a_rerun_changes_nothing(conn):
    src(conn, {date(2026, 10, 13): 48_000, date(2026, 10, 14): 49_000, D: 49_500, date(2026, 10, 16): 50_000})
    repo.upsert_corporate_actions(conn, [event(D)], F1)
    out = recompute(conn, ["AAA"])
    f, b = stored(conn)
    assert [(x[0], x[1]) for x in f] == [(D, "0.980000000000")]  # (50,000 - 1,000) / 50,000
    assert f[0][2] is not None and f[0][3]
    got = {r.trading_date: (r.c, r.nominal_kind) for r in b}
    assert got[date(2026, 10, 14)] == (50_000, "reconstructed")  # hand: 49,000 / 0.98
    assert got[date(2026, 10, 13)] == (48_980, "reconstructed")  # hand: 48,000 / 0.98 = 48,979.6
    assert got[D] == (49_500, "reconstructed")  # G = 1 on and after the ex-date
    assert (b[0].o, b[0].h, b[0].l, b[0].v, b[0].fetched_at) == (48_980, 48_980, 48_980, 1000, F1)
    assert [x.f for x in out["AAA"][0]] == [Decimal("0.980000000000")] and len(out["AAA"][1]) == 4
    conn.commit()
    recompute(conn, ["AAA"])
    assert stored(conn) == (f, b)


def test_g9_an_observed_close_stays_and_is_the_pre_close_of_the_factor(conn):
    src(conn, {date(2026, 10, 14): 92_499, D: 93_000})  # inverting 92,499 would give 93,499
    repo.upsert_bars_1d(conn, [bar(date(2026, 10, 14), 93_500)], nominal_kind="observed", fetched_at=F1)
    repo.upsert_corporate_actions(conn, [event(D)], F1)
    recompute(conn, ["AAA"])
    f, b = stored(conn)
    row = next(r for r in b if r.trading_date == date(2026, 10, 14))
    assert (row.c, row.nominal_kind) == (93_500, "observed")
    assert f[0][1] == "0.989304812834"  # hand: 92,500 / 93,500


def test_g12_fpt_bonus(conn):
    repo.upsert_bars_1d_src(conn, parse_bars(gzip.open(FIX / "gap_chart/FPT-1d.json.gz").read()), F1)
    rows, _, _ = parse_events((FIX / "events/FPT-2026.json").read_bytes())
    repo.upsert_corporate_actions(conn, rows, F1)
    recompute(conn, ["FPT"])
    f, b = stored(conn)
    assert [(x[0], x[1]) for x in f] == [(date(2026, 9, 21), "0.909090909091")]  # 10 / 11
    c = {r.trading_date: r.c for r in b}[date(2026, 9, 18)]
    assert abs(c - 71_701) <= 1  # hand: 65,182.47 x 1.1 = 71,700.7; the db stores 65,182 -> 71,700
    anomalies = conn.execute(text("SELECT rule, trading_date FROM data_anomalies ORDER BY 2")).all()
    # ex 05-28 and 06-24 (two events on one day, one row)
    assert {a.rule for a in anomalies} == {"adj_factor_no_pre_close"} and len(anomalies) == 2


def test_unusable_event_is_an_anomaly_and_the_symbol_continues(conn):
    src(conn, {date(2026, 10, 1): 40_000, date(2026, 10, 2): 40_000, date(2026, 10, 13): 48_000,
               date(2026, 10, 14): 49_000, D: 49_500})
    repo.upsert_corporate_actions(conn, [event(date(2026, 10, 2), "bad", cash_per_share=None),
                                         event(D, "ok")], F1)
    for _ in range(2):  # the second run must not add a second anomaly
        out = recompute(conn, ["AAA"])
        conn.commit()
    assert [x[1] for x in stored(conn)[0]] == ["0.980000000000"]
    assert out["AAA"][2] == [(date(2026, 10, 2), "adj_factor_invalid_input", "cash_missing_or_not_positive")]
    assert conn.execute(text("SELECT count(*) FROM data_anomalies")).scalar_one() == 1


def test_recompute_set_skips_unchecked_names_and_counts_them(conn):
    for s in ("AAA", "BBB", "CCC"):
        conn.execute(text("INSERT INTO symbols (symbol, exchange, type, name_vi, name_en, source, fetched_at)"
                          " VALUES (:s, 'HOSE', 'STOCK', '', '', 'vci', now())"), {"s": s})
    conn.execute(text("UPDATE symbols SET ca_checked_at = now() WHERE symbol IN ('AAA', 'CCC')"))
    src(conn, {D: 49_500}, "BBB")  # step 2 wrote BBB, but V5 never read it
    src(conn, {D: 49_500}, "CCC")
    assert recompute_set(conn, ["AAA"], F1) == (["AAA", "CCC"], 1)
    assert recompute_set(conn, [], F1.replace(day=16)) == ([], 0)  # nothing written since
