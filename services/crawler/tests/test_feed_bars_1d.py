"""bars_1d back-fill on recorded fixtures with an in-memory repo (no network, no db)."""

import gzip
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from finvest_crawler.archive import Archive
from finvest_crawler.feeds import bars_1d
from finvest_crawler.feeds.bars_1d import run_bars_1d
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from finvest_market_data.domain.models import Bar, SymbolRecord
from finvest_market_data.domain.ports import SourceNoLongerServes

FIX = Path(__file__).parent / "fixtures/feeds/bars_1d"
D, TODAY = date(2026, 10, 15), date(2026, 10, 16)


def load(name: str) -> bytes:
    return gzip.decompress((FIX / f"{name}.json.gz").read_bytes())


def payload(sym: str) -> bytes:  # ZZZ answers with zero bars; any other name serves FPT's columns, renamed
    if sym == "ZZZ":
        return load("ZZZ")
    return json.dumps([{**json.loads(load("FPT"))[0], "symbol": sym}]).encode()


class FakeRepo:
    """In-memory stand-in for finvest_market_data.infrastructure.repositories (same functions)."""

    def __init__(self, names=("FPT", "ZZZ"), fail_on_call=None):
        self.names, self.fail_on_call = names, fail_on_call
        self.bars, self.index, self.runs, self.sessions, self.calls = {}, {}, [], [], 0
        self.last, self.delisted_flags = {}, []  # last_bar_dates() answer; include_delisted of each call

    def last_bar_dates(self, conn):
        return self.last

    def list_symbols(self, conn, include_delisted=True):
        self.delisted_flags.append(include_delisted)
        return [SymbolRecord(n, "HOSE", "STOCK", n, n, None, False, "vci") for n in self.names]

    def fail_unfinished_runs(self, conn, feed, d):
        return 0

    def insert_crawl_run(self, conn, feed, d, started):
        self.runs.append(None)
        return len(self.runs) - 1

    def finish_crawl_run(self, conn, id, status, reason, requests, rows, path):
        self.runs[id] = (status, reason, requests, rows)

    def upsert_crawl_session(self, conn, m):
        self.sessions.append(m)

    def upsert_bars_1d_src(self, conn, bars, fetched_at):
        self.calls += 1
        if self.calls == self.fail_on_call:
            raise RuntimeError("disk full")
        for b in bars:
            self.bars[(b.symbol, b.trading_date, b.source, fetched_at)] = b

    def upsert_index_1d(self, conn, bars):
        for b in bars:
            self.index[(b.index_code, b.trading_date)] = b

    def daily_coverage(self, conn):
        return {"HOSE": 50}


class FakeSnap:
    """Stands in for the SSI board source: records calls, counts one request, archives like the real one."""

    name = "ssi"

    def __init__(self):
        self.calls, self.bars, self.idle, self.fetcher = [], [], [], None
        self.exc = SourceNoLongerServes("board", None)

    def snapshot_bars(self, session):
        self.calls.append(session)
        if self.exc:
            raise self.exc
        self.fetcher.requests += 1
        self.fetcher.archive.write("bars_1d", session, "board-hose", b"[]")
        return self.bars, self.idle


@pytest.fixture(autouse=True)
def snap(monkeypatch):
    """Every test sees a board that no longer serves (steps 1 and 3 only) unless it sets `snap.exc = None`."""
    s, real = FakeSnap(), bars_1d.source_for

    def source_for(role, settings, fetcher):
        if role == "snapshot":
            s.fetcher = fetcher
            return s
        return real(role, settings, fetcher)

    monkeypatch.setattr(bars_1d, "source_for", source_for)
    return s


def run(tmp_path, repo, only=("FPT", "ZZZ"), blocked=(), today=TODAY, run_date=D, serve=None, calls=None,
        failing=(), absent=(), **kw):
    def handler(req):
        body = json.loads(req.content)
        syms = body["symbols"]
        if calls is not None:
            calls.append((syms, body["countBack"]))
        if serve and syms[0] in serve:
            return httpx.Response(200, content=serve[syms[0]])
        if blocked and set(syms) & set(blocked):
            return httpx.Response(200, content=b"<html>Just a moment</html>")
        if set(syms) & set(failing):
            return httpx.Response(503)
        return httpx.Response(200, content=json.dumps(
            [r for s in syms if s not in absent for r in json.loads(payload(s))]).encode())

    f = Fetcher(httpx.Client(transport=httpx.MockTransport(handler)), {"vci": TokenBucket(1000)},
                Archive(tmp_path / "raw"), "ua", sleep=lambda s: None)
    m = run_bars_1d(Settings(_env_file=None, data_dir=tmp_path), run_date, only=list(only) if only else None,
                    fetcher=f, conn=MagicMock(), repo=repo, today=today, **kw)
    return m, f


def test_first_run_then_replay_is_identical(tmp_path):
    repo = FakeRepo()
    m, f = run(tmp_path, repo)
    assert (m.status, m.symbols_fetched, m.symbols_no_trades, m.rows, m.requests) == (
        "complete", 1, ("ZZZ",), 50, 2)
    assert m.universe_source == "cli:--only"
    assert repo.runs == [("complete", None, 2, 50)]
    first = dict(repo.bars)
    m2, f2 = run(tmp_path, repo)
    assert (m2.checksum, m2.requests, f2.replays) == (m.checksum, 0, 2)
    assert repo.bars == first  # same fetched_at (archive mtime) => same 50 versions, none added


def test_interrupt_then_resume_equals_uninterrupted(tmp_path):
    clean = FakeRepo()
    clean_m, _ = run(tmp_path / "clean", clean, only=("AAA", "BBB", "FPT"))
    repo = FakeRepo(fail_on_call=2)  # the second stock write (BBB) dies; FPT was never fetched
    with pytest.raises(RuntimeError):
        run(tmp_path / "x", repo, only=("AAA", "BBB", "FPT"))
    assert repo.runs[0][0] == "failed" and [m.reason for m in repo.sessions] == ["running"]  # AAA only
    repo.fail_on_call = None
    m, f = run(tmp_path / "x", repo, only=("AAA", "BBB", "FPT"))
    assert (m.status, f.requests, f.replays) == ("complete", 1, 2)  # AAA and BBB replay, only FPT is fetched
    assert m.checksum == clean_m.checksum and m.rows == 150
    assert {k[:3]: b for k, b in repo.bars.items()} == {k[:3]: b for k, b in clean.bars.items()}


def test_blocked_on_second_symbol_keeps_the_first(tmp_path):
    repo = FakeRepo()
    m, _ = run(tmp_path, repo, only=("FPT", "ZZZ"), blocked=("ZZZ",))
    assert (m.status, m.reason, m.symbols_fetched, m.rows) == ("blocked", "source_blocked", 1, 50)
    assert m.symbols_skipped == (("ZZZ", "source_blocked"),)
    assert len(repo.bars) == 50


def test_full_universe_adds_indices_and_rounds_levels_to_2dp(tmp_path):
    repo = FakeRepo(("FPT",))
    m, _ = run(tmp_path, repo, only=None)
    assert (m.universe_source, m.universe_count, m.symbols_fetched, m.rows, m.requests) == (
        "symbols table", 3, 3, 150, 3)
    vn = repo.index[("VNINDEX", date(2026, 8, 4))]
    assert str(vn.o) == "65818.84"  # 2 dp kept, not rounded to integer VND
    assert {i for i, _ in repo.index} == {"VNINDEX", "VN30"}


def test_recorded_vn30_payload_is_stored_with_coverage_summary(tmp_path, capsys):
    vn30 = gzip.decompress((Path(__file__).parent / "fixtures/vci/gap_chart/VN30-1d.json.gz").read_bytes())
    repo = FakeRepo()
    m, _ = run(tmp_path, repo, only=("FPT", "VN30", "VNINDEX"), serve={"VN30": vn30})
    assert (m.status, m.symbols_fetched, m.rows) == ("complete", 3, 50 + 59 + 50)
    assert {i for i, _ in repo.index} == {"VN30", "VNINDEX"}
    assert all(b.value < 2**63 for b in repo.index.values())
    summary = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert (summary["summary"], summary["rows"], summary["coverage"]) == ("complete", 159, {"HOSE": "50"})


def test_future_run_date_is_refused(tmp_path):
    with pytest.raises(ValueError):
        run(tmp_path, FakeRepo(), run_date=date(2026, 10, 17))


def test_count_bounds_the_fetch_and_progress_reports_every_name(tmp_path):
    calls = []
    repo = FakeRepo()
    m7, _ = run(tmp_path / "a", repo, only=("FPT", "ZZZ"), count=7, on_progress=lambda *a: calls.append(a))
    assert calls == [(1, 2), (2, 2)]  # one call per name, fetched or no_trades
    assert list((tmp_path / "a/raw").rglob("FPT-1d-7*"))  # archive name carries the count
    mc, _ = run(tmp_path / "b", FakeRepo(), only=("FPT", "ZZZ"))
    assert (m7.status, m7.rows, m7.symbols_fetched) == (mc.status, mc.rows, mc.symbols_fetched)
    assert m7.checksum == mc.checksum


NAMES = tuple(f"S{i:03d}" for i in range(120))


def test_indices_first_then_symbol_batches(tmp_path, monkeypatch):
    monkeypatch.setattr("finvest_crawler.feeds.bars_1d.BATCH_MAX", 50)
    calls, progress = [], []
    m, _ = run(tmp_path, FakeRepo(NAMES), only=None, count=8, calls=calls,
               on_progress=lambda *a: progress.append(a))
    assert [(len(c), n) for c, n in calls] == [(1, 6000), (1, 6000), (50, 8), (50, 8), (20, 8)]
    assert [c[0] for c, _ in calls[:2]] == ["VN30", "VNINDEX"]
    assert progress == [(1, 122), (2, 122), (52, 122), (102, 122), (122, 122)]
    assert (m.status, m.symbols_fetched, m.requests, m.universe_count) == ("complete", 122, 5, 122)


def test_batch_size_shrinks_with_count_and_is_one_by_default(tmp_path, monkeypatch):
    calls = []
    run(tmp_path / "a", FakeRepo(), only=("FPT", "HPG"), count=8, calls=calls)
    assert calls == [(["FPT"], 8), (["HPG"], 8)]  # BATCH_MAX = 1 (spike S-v2-batch)
    monkeypatch.setattr("finvest_crawler.feeds.bars_1d.BATCH_MAX", 50)
    calls.clear()
    run(tmp_path / "b", FakeRepo(), only=("FPT", "HPG"), count=8, calls=calls)
    assert calls == [(["FPT", "HPG"], 8)]  # --only: no indices fetched
    calls.clear()
    run(tmp_path / "c", FakeRepo(NAMES[:20]), only=NAMES[:20], count=6000, calls=calls)
    assert [len(c) for c, _ in calls] == [8, 8, 4]


def test_batch_gaps_failures_and_block(tmp_path, monkeypatch):
    monkeypatch.setattr("finvest_crawler.feeds.bars_1d.BATCH_MAX", 50)
    only = NAMES[:120]
    m, _ = run(tmp_path / "a", FakeRepo(), only=only, count=8, absent=("S007",))
    assert (m.status, m.symbols_no_trades, m.symbols_fetched) == ("complete", ("S007",), 119)
    calls = []
    m, _ = run(tmp_path / "b", FakeRepo(), only=only, count=8, failing=("S060",), calls=calls)
    assert (m.status, m.symbols_fetched, len(m.symbols_skipped), len(calls) > 3) == ("partial", 70, 50, True)
    assert {r for _, r in m.symbols_skipped} == {"http_503"} and len(calls) == 3 + 2  # 3 tries on batch 2
    repo, calls = FakeRepo(), []
    m, _ = run(tmp_path / "c", repo, only=("VN30", *only), count=8, blocked=("S060",), calls=calls)
    got = (m.status, m.reason, m.symbols_fetched, len(m.symbols_skipped))
    assert got == ("blocked", "source_blocked", 51, 70)
    assert {r for _, r in m.symbols_skipped} == {"source_blocked"} and {i for i, _ in repo.index} == {"VN30"}


# sha256 of the one-by-one run (before batching) over these names; the batched run must not change it
OLD_DIGEST = "sha256:0ecbfc173a5e6bcfb6a7533cb9d51852b06ca0b42a6ccfcfe579f4e0073d7bd7"


def test_checksum_is_batch_size_independent(tmp_path, monkeypatch):
    only = ("FPT", "VN30", "VNINDEX", "VNM", "ZZZ")  # the indices sort between the symbols
    m1, _ = run(tmp_path / "a", FakeRepo(), only=only)
    monkeypatch.setattr("finvest_crawler.feeds.bars_1d.BATCH_MAX", 50)
    m50, _ = run(tmp_path / "b", FakeRepo(), only=only)
    assert m1.checksum == m50.checksum == OLD_DIGEST


LETTERS = tuple("ABCDEF")


def board_bar(sym, day=D):
    ts = datetime(day.year, day.month, day.day - 1, 17, 0, tzinfo=UTC)  # 00:00 Asia/Ho_Chi_Minh
    return Bar(sym, ts, 100, 110, 90, 105, 1000, None, "ssi")


def test_press_asks_the_board_then_only_the_gaps(tmp_path, snap):
    repo, calls = FakeRepo(LETTERS), []
    repo.last = {"E": D}  # E is current already; F has no bar at all
    snap.exc, snap.bars, snap.idle = None, [board_bar(n) for n in "ABC"], ["D"]
    progress = []
    m, _ = run(tmp_path, repo, only=None, count=8, calls=calls, on_progress=lambda *a: progress.append(a))
    assert calls == [(["VN30"], 6000), (["VNINDEX"], 6000), (["F"], 8)] and snap.calls == [D]
    assert (m.status, m.symbols_fetched, m.symbols_no_trades, m.requests) == ("complete", 5 + 2, ("D",), 4)
    assert progress[-1] == (8, 8) and m.universe_count == 8
    assert {(k[0], k[2]) for k in repo.bars} == {("A", "ssi"), ("B", "ssi"), ("C", "ssi"), ("F", "vci")}


def test_gap_max_defers_the_newest_and_a_dead_board_makes_everything_a_gap(tmp_path):
    repo, calls = FakeRepo(LETTERS), []
    repo.last = {"F": date(2026, 10, 1), "A": date(2026, 10, 5), **dict.fromkeys("BCDE", date(2026, 10, 10))}
    m, _ = run(tmp_path / "a", repo, only=None, count=8, gap_max=2, calls=calls)
    assert sorted(c[0][0] for c in calls[2:]) == ["A", "F"]
    assert m.symbols_skipped == tuple((n, "deferred") for n in "BCDE") and m.status == "partial"
    m, _ = run(tmp_path / "b", FakeRepo(LETTERS), only=None, count=8)
    assert (m.status, m.symbols_fetched) == ("complete", 8)


def test_delisted_names_only_in_a_back_fill(tmp_path):
    for count, flag in ((bars_1d.COUNT, True), (8, False)):
        repo = FakeRepo(("A",))
        run(tmp_path / str(count), repo, only=None, count=count)
        assert repo.delisted_flags == [flag]


def test_three_failed_batches_in_a_row_block_the_run(tmp_path):
    names, calls = tuple(f"S{i:03d}" for i in range(6)), []
    m, _ = run(tmp_path / "a", FakeRepo(names), only=names, count=8, failing=names[:3], calls=calls)
    assert (m.status, m.reason, m.symbols_fetched) == ("blocked", "source_blocked", 0)
    assert m.symbols_skipped == tuple((n, "http_503") for n in names[:3]) + tuple(
        (n, "source_blocked") for n in names[3:])
    assert not {c[0][0] for c in calls} & set(names[3:])
    m, _ = run(tmp_path / "b", FakeRepo(names), only=names, count=8, failing=names[:2])
    assert (m.status, m.symbols_fetched, len(m.symbols_skipped)) == ("partial", 4, 2)


def test_ledger_row_after_every_unit_then_the_final_manifest(tmp_path, snap):
    repo = FakeRepo(("A", "F"))
    snap.exc, snap.bars = None, [board_bar("A")]
    m, _ = run(tmp_path, repo, only=None, count=8)
    assert [s.reason for s in repo.sessions] == ["running"] * 4 + [None]  # 2 indices, snapshot, gap F, final
    assert all(s.status == "partial" for s in repo.sessions[:-1]) and repo.sessions[-1] is m
    rows = [s.rows for s in repo.sessions]
    assert rows == sorted(rows) and rows[-1] == rows[-2]


def line(name, b, source):  # the documented checksum line, written out again
    return bars_1d._line(name, b.trading_date, source, b.o, b.h, b.l, b.c, b.v, b.value)


def test_snapshot_and_gap_bars_hash_like_the_old_one_by_one_path(tmp_path, snap):
    repo = FakeRepo(("A", "B", "C", "F"))
    snap.exc, snap.bars = None, [board_bar(n) for n in "ABC"]
    m, _ = run(tmp_path, repo, only=None, count=8)
    by: dict[str, list[bytes]] = {}
    for b in repo.bars.values():
        by.setdefault(b.symbol, []).append(line(b.symbol, b, b.source))
    for b in repo.index.values():
        by.setdefault(b.index_code, []).append(line(b.index_code, b, "vci"))
    h = hashlib.sha256()
    for n in sorted(by):
        for ln in sorted(by[n]):
            h.update(ln)
    assert m.checksum == "sha256:" + h.hexdigest()


def test_a_dropped_snapshot_counts_toward_the_fail_run(tmp_path):
    names, calls = tuple(f"S{i:03d}" for i in range(4)), []  # the autouse board raises SourceNoLongerServes
    m, _ = run(tmp_path, FakeRepo(names), only=None, count=8, failing=names[:2], calls=calls)
    assert (m.status, m.reason) == ("blocked", "source_blocked")
    assert dict(m.symbols_skipped) == {names[0]: "http_503", names[1]: "http_503", names[2]: "source_blocked",
                                       names[3]: "source_blocked"}
    assert not {c[0][0] for c in calls} & set(names[2:])
