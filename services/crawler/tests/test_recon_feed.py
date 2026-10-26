"""`crawl recon` on a real db (needs FINVEST_DATABASE_URL, db name *_test; excluded from the kernel).
Hand numbers are tech plan sprint-05 G10 (cash 1,000 on 50,000 -> f 0.98) and R8."""

import gzip
import json
import os
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
from alembic import command
from alembic.config import Config
from finvest_crawler.archive import Archive
from finvest_crawler.cli import main
from finvest_crawler.feeds import recon as recon_mod
from finvest_crawler.feeds.recon import run_recon
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from finvest_market_data.domain.models import Bar
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
VN = ZoneInfo("Asia/Ho_Chi_Minh")
F1 = datetime(2026, 10, 15, 9, tzinfo=UTC)
D1, D2, EX, D6 = (date(2026, 10, n) for n in (1, 2, 5, 6))  # Thu, Fri, Mon (ex-date), Tue
TODAY = date(2026, 10, 26)
SYM = ("INSERT INTO symbols (symbol, exchange, type, name_vi, name_en, source, fetched_at)"
       " VALUES (:s, 'HOSE', 'STOCK', '', '', 'vci', now())")


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
        for t in ("symbols", "symbol_index_membership", "bars_1d_src", "bars_1d", "adj_factors",
                  "recon_mismatches", "data_anomalies", "crawl_runs", "scenarios"):
            c.execute(text(f"TRUNCATE {t}"))
        c.commit()
        yield c


def bar(d: date, c: int, sym: str) -> Bar:
    return Bar(sym, datetime.combine(d, time(), VN).astimezone(UTC), c, c, c, c, 1000, None, "vci")


def seed(conn, sym: str, nominal: dict[date, int], adjusted: dict[date, int], f: str | None = None,
         ref: int | None = None, kind="observed") -> None:
    """`nominal` closes (ours), `adjusted` closes (the source's), a factor on EX, a board ref on EX."""
    conn.execute(text(SYM + " ON CONFLICT DO NOTHING"), {"s": sym})
    for d, c in nominal.items():
        repo.upsert_bars_1d(conn, [bar(d, c, sym)], nominal_kind=kind, fetched_at=F1,
                            ref={sym: ref} if ref and d == EX else None)
    repo.upsert_bars_1d_src(conn, [bar(d, c, sym) for d, c in adjusted.items()], F1)
    if f:
        repo.replace_adj_factors(conn, sym, [(EX, f, None)], "t")
    conn.commit()


def rows(conn, table="recon_mismatches"):
    return conn.execute(text(f"SELECT * FROM {table}")).all()


def test_g10_one_mismatch_row_and_a_rerun_changes_nothing(conn):
    seed(conn, "AAA", {D1: 50_000, D2: 50_000, D6: 93_500}, {D1: 48_900, D2: 48_980, D6: 93_500}, "0.98")
    for _ in range(2):
        r = run_recon(Settings(), TODAY, ["AAA"], conn=conn)
    # hand: 50,000 x 0.98 = 49,000 vs 48,900 -> 0.2045 %; 49,000 vs 48,980 -> 0.0408 % (none)
    (m,) = rows(conn)
    assert (m.symbol, m.trading_date, m.ours, m.theirs, m.diff_pct) == (
        "AAA", D1, 49_000, 48_900, Decimal("0.2045"))
    assert (r.checked, r.mismatches, r.missing) == (1, 1, [])
    assert r.summary == "1/1, 1 mismatches; first mismatch AAA 2026-10-01"
    q = text("SELECT feed, status, requests, rows, reason FROM crawl_runs ORDER BY id DESC")
    run = conn.execute(q).first()
    assert run == ("recon", "ok", 0, 1, r.summary)


def test_no_factor_and_equal_closes_gives_no_row(conn):
    seed(conn, "AAA", {D1: 50_000, D2: 50_000}, {D1: 50_000, D2: 50_000})
    r = run_recon(Settings(), TODAY, ["AAA"], conn=conn)
    assert rows(conn) == [] and r.results["AAA"].checked == 2


def test_one_vnd_diff_without_an_ex_date_is_a_unit_or_adapter_mismatch(conn):
    seed(conn, "AAA", {D1: 50_000, D2: 50_000}, {D1: 50_000, D2: 49_999})
    r = run_recon(Settings(), TODAY, ["AAA"], conn=conn)
    assert [(m.trading_date, m.note) for m in r.results["AAA"].mismatches] == [(D2, "unit_or_adapter")]
    assert len(rows(conn)) == 1


def test_29_of_30_vn30_names_names_the_missing_one_and_exits_1(conn, monkeypatch, capsys):
    for i in range(30):
        s = f"V{i:02d}"
        conn.execute(text("INSERT INTO symbol_index_membership (index_code, symbol, valid_from)"
                          " VALUES ('VN30', :s, '2026-01-01')"), {"s": s})
        if i != 7:
            seed(conn, s, {D1: 50_000}, {D1: 50_000})
        else:  # in the master, no bars at all
            conn.execute(text(SYM), {"s": s})
    seed(conn, "SCEN", {D1: 50_000}, {D1: 50_000})  # a scenario symbol outside VN30 joins the default set
    conn.execute(text("INSERT INTO scenarios (name, symbol, style, amount_vnd, buy_date,"
                      " created_at, updated_at)"
                      " VALUES ('s', 'SCEN', 'lump_sum', 1, '2026-01-02', now(), now())"))
    conn.commit()
    monkeypatch.setenv("FINVEST_DATABASE_URL", URL)  # type: ignore[arg-type]
    assert main(["recon", "--date", TODAY.isoformat()]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "30/31, 0 mismatches; missing V07"
    assert "V00: 1 days checked, 0 mismatches" in out
    assert conn.execute(text("SELECT status, reason FROM crawl_runs")).one() == ("partial", out[0])


@pytest.mark.parametrize("ref, found", [(49_000, 0), (49_050, 0), (49_100, 1)])
def test_r8_board_reference_price_within_one_tick(conn, ref, found):
    # hand: 0.98 x 50,000 = 49,000, tick 50 (HOSE, 10,000 <= price < 50,000); 2 ticks off = 49,100
    seed(conn, "AAA", {D2: 50_000, EX: 49_000}, {D2: 49_000, EX: 49_000}, "0.98", ref=ref)
    for _ in range(2):  # a re-run must not add a second finding
        r = run_recon(Settings(), TODAY, ["AAA"], conn=conn)
    assert r.anomalies == found
    got = rows(conn, "data_anomalies")
    assert [(a.rule, a.trading_date) for a in got] == [("adj_factor_ref_mismatch", EX)] * found


def test_r8_skips_a_reconstructed_previous_bar(conn):
    seed(conn, "AAA", {D2: 50_000}, {D2: 49_000, EX: 49_000}, "0.98", kind="reconstructed")
    seed(conn, "AAA", {EX: 49_000}, {}, ref=49_900)  # a wrong ref, but pre_close is ours, not the exchange's
    assert run_recon(Settings(), TODAY, ["AAA"], conn=conn).anomalies == 0



def test_r8_skips_upcom_whose_reference_is_the_previous_vwap(conn):  # VN§3
    seed(conn, "AAA", {D2: 50_000, EX: 49_000}, {D2: 49_000, EX: 49_000}, "0.98", ref=49_200)
    conn.execute(text("UPDATE symbols SET exchange = 'UPCOM'"))
    conn.commit()
    assert run_recon(Settings(), TODAY, ["AAA"], conn=conn).anomalies == 0
    assert rows(conn, "data_anomalies") == []


# --- F-016 / BE-recon-s2: --cross-check ssi (S2 as a second `theirs`) ---
FPT_DAY, FPT_EX = date(2026, 9, 18), date(2026, 9, 21)
FIX = Path(__file__).parent / "fixtures/ssi/history/FPT-1d.json.gz"


def ssi_fetcher(tmp_path, status=200, close=None):
    body = gzip.decompress(FIX.read_bytes())
    if close is not None:  # hand-break the 2026-09-18 close (thousand VND)
        d = json.loads(body)
        i = [datetime.fromtimestamp(t, UTC).date() for t in d["data"]["t"]].index(FPT_DAY)
        d["data"]["c"][i] = close
        body = json.dumps(d).encode()
    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(status, content=body)))
    return Fetcher(client, {"ssi": TokenBucket(100)}, Archive(tmp_path), "ua", sleep=lambda s: None)


def seed_fpt(conn):
    """09-18 is pre-crawl (reconstructed from V2); ex-date 09-21 factor 1/1.1: ours 71,701 -> 65,182.73."""
    v2 = {FPT_DAY: 65_183, date(2026, 9, 22): 65_000}  # V2 `last` >= ex-date
    seed(conn, "FPT", {FPT_DAY: 71_701}, v2, kind="reconstructed")
    repo.replace_adj_factors(conn, "FPT", [(FPT_EX, "0.9090909091", None)], "t")
    conn.commit()


def spy_self_check(monkeypatch):
    calls = []
    real = recon_mod.reconcile
    monkeypatch.setattr(recon_mod, "reconcile",
                        lambda *a, **k: calls.append(k.get("self_check")) or real(*a, **k))
    return calls


def test_s2_fpt_lands_as_65180_and_ours_65182_73_is_no_mismatch(conn, tmp_path, monkeypatch):
    seed_fpt(conn)
    calls = spy_self_check(monkeypatch)
    r = run_recon(Settings(), TODAY, ["FPT"], conn=conn, cross_check="ssi", fetcher=ssi_fetcher(tmp_path))
    (row,) = conn.execute(text("SELECT adj_c FROM bars_1d_src WHERE source='ssi' AND trading_date=:d"),
                          {"d": FPT_DAY}).all()
    assert row.adj_c == 65_180  # S2 65.18 thousand VND
    assert (r.mismatches, r.ssi_mismatches, r.ssi_blocked) == (0, 0, False)  # 0.0042 % < 0.1 %
    assert r.ssi_requests == 1 and r.summary.endswith("| vci: 0, ssi: 0 mismatches")
    assert calls == [True, False]  # self-check against V2 only


def test_s2_hand_broken_close_is_a_factor_or_event_mismatch(conn, tmp_path, monkeypatch):
    seed_fpt(conn)
    out = []
    real = recon_mod.reconcile
    monkeypatch.setattr(recon_mod, "reconcile", lambda *a, **k: out.append(real(*a, **k)) or out[-1])
    r = run_recon(Settings(), TODAY, ["FPT"], conn=conn, cross_check="ssi",
                  fetcher=ssi_fetcher(tmp_path, close=65.28))
    # hand: |65,182.73 - 65,280| / 65,280 = 0.149 % > 0.1 %
    (m,) = out[-1].mismatches
    assert (m.note, m.theirs, r.ssi_mismatches, r.mismatches) == ("factor_or_event", 65_280, 1, 0)


def test_s2_blocked_keeps_the_local_summary(conn, tmp_path):
    seed_fpt(conn)
    r = run_recon(Settings(), TODAY, ["FPT"], conn=conn, cross_check="ssi",
                  fetcher=ssi_fetcher(tmp_path, status=418))
    assert r.ssi_blocked and r.ssi_mismatches == 0 and r.mismatches == 0
    assert r.summary.startswith("1/1, 0 mismatches") and "ssi blocked, cross-check stopped" in r.summary
    assert conn.execute(text("SELECT status FROM crawl_runs")).scalar() == "ok"
