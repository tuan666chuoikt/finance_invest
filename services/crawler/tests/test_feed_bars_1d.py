"""bars_1d back-fill on recorded fixtures with an in-memory repo (no network, no db)."""

import gzip
import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from finvest_crawler.archive import Archive
from finvest_crawler.feeds.bars_1d import run_bars_1d
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from finvest_market_data.domain.models import SymbolRecord

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

    def list_symbols(self, conn, include_delisted=True):
        assert include_delisted
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
    assert repo.runs[0][0] == "failed" and repo.sessions == []
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
