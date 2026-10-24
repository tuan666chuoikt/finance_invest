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


def run(tmp_path, repo, only=("FPT", "ZZZ"), blocked=(), today=TODAY, run_date=D, serve=None, **kw):
    def handler(req):
        sym = json.loads(req.content)["symbols"][0]
        if serve and sym in serve:
            return httpx.Response(200, content=serve[sym])
        if sym in blocked:
            return httpx.Response(200, content=b"<html>Just a moment</html>")
        return httpx.Response(200, content=payload(sym))

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
