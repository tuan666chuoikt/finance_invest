import gzip
import json
import os
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from finvest_crawler import cli
from finvest_crawler.archive import Archive
from finvest_crawler.feeds import ticks as feed
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from finvest_market_data.domain.manifest import checksum

FIX = Path(__file__).parent / "fixtures/feeds/ticks"
D = date(2026, 10, 15)
MANIFEST_KEYS = {"feed", "trading_date", "source", "started_at", "finished_at", "status", "reason",
                 "requests", "rows", "checksum", "symbols_fetched", "symbols_skipped", "universe"}


def load(name: str) -> bytes:
    return gzip.decompress((FIX / f"{name}.json.gz").read_bytes())


class FakeRepo:
    """In-memory stand-in for finvest_market_data.infrastructure.repositories (same functions)."""

    def __init__(self):
        self.ticks, self.sessions, self.anomalies, self.runs = {}, {}, [], {}

    def insert_crawl_run(self, conn, feed, d, started):
        self.runs[len(self.runs) + 1] = None
        return len(self.runs)

    def fail_unfinished_runs(self, conn, feed, d):
        n = 0
        for i, r in self.runs.items():
            if r is None:
                self.runs[i], n = ("failed", "interrupted", 0, 0, None), n + 1
        return n

    def finish_crawl_run(self, conn, id, status, reason, requests, rows, manifest_path):
        self.runs[id] = (status, reason, requests, rows, manifest_path)

    def upsert_crawl_session(self, conn, m):
        self.sessions[(m.feed, m.trading_date)] = m

    def insert_anomaly(self, conn, symbol, d, rule, value):
        self.anomalies.append((symbol, rule, value))

    def upsert_ticks(self, conn, rows):
        changed = 0
        for t in rows:
            old = self.ticks.get((t.symbol, t.ts, t.seq))
            changed += old is not None and old != t
            self.ticks[(t.symbol, t.ts, t.seq)] = t
        return changed


def make(tmp_path, handler):
    buckets = {n: TokenBucket(1000) for n in ("kbs", "vci", "ssi")}
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Fetcher(client, buckets, Archive(tmp_path / "raw"), "ua", sleep=lambda s: None)


def serve(overrides=None):
    overrides = overrides or {}

    def handler(req):
        url = str(req.url)
        if "getAll" in url:
            return httpx.Response(200, content=load("symbols_getAll"))
        sym = url.split("/history/")[1].split("?")[0]
        o = overrides.get(sym)
        if callable(o):
            return o()
        return httpx.Response(200, content=o if o is not None else load(sym))

    return handler


def run(tmp_path, handler=None, d=D, only=None, repo=None, today=D):
    repo = repo or FakeRepo()
    f = make(tmp_path, handler or serve())
    s = Settings(_env_file=None, data_dir=tmp_path)
    m = feed.run_ticks(s, d, only, fetcher=f, conn=MagicMock(), repo=repo, today=today)
    return m, f, repo


def test_complete_run_and_manifest_file(tmp_path, capsys):
    m, f, repo = run(tmp_path)
    assert (m.status, m.reason, m.symbols_fetched, m.rows, m.requests) == ("complete", None, 2, 100, 3)
    assert m.universe_source == "vci:symbols/getAll" and m.universe_count == 2
    on_disk = json.loads((tmp_path / "raw/ticks/2026-10-15/_manifest.json").read_text())
    assert set(on_disk) == MANIFEST_KEYS and on_disk["universe"].keys() == {"source", "as_of", "count"}
    assert on_disk["checksum"] == checksum(repo.ticks.values())  # streaming sha == domain checksum
    assert repo.sessions[("ticks", D)] is m and repo.runs[1][0] == "complete" and not repo.anomalies
    out = capsys.readouterr().out.splitlines()
    assert json.loads(out[0]).keys() == {"symbol", "rows", "replayed", "ms"} and "summary" in out[-1]


def test_idempotent_rerun_replays_archive(tmp_path):
    m1, _, repo = run(tmp_path)
    before = dict(repo.ticks)
    m2, f2, _ = run(tmp_path, repo=repo)
    assert repo.ticks == before and m2.checksum == m1.checksum and m2.rows == 100
    assert (m2.requests, f2.replays) == (0, 3) and not repo.anomalies
    # universe pinned by the archive
    assert (m2.universe_count, m2.universe_as_of) == (m1.universe_count, m1.universe_as_of)


def test_unfinished_run_is_closed_before_the_next(tmp_path):
    repo = FakeRepo()
    repo.insert_crawl_run(None, "ticks", D, None)  # a crashed run, never finished
    run(tmp_path, repo=repo)
    assert repo.runs[1] == ("failed", "interrupted", 0, 0, None) and repo.runs[2][0] == "complete"


def test_past_date_other_session_is_missed(tmp_path):
    m, f, repo = run(tmp_path, d=date(2026, 10, 14))
    assert (m.status, m.reason, m.symbols_fetched, m.rows, m.requests) == (
        "missed", "source_no_longer_serves", 0, 0, 2)
    assert (tmp_path / "raw/ticks/2026-10-14/_manifest.json").exists() and not repo.ticks
    assert repo.sessions[("ticks", date(2026, 10, 14))].status == "missed"


def test_past_date_empty_tape_after_good_one_is_partial(tmp_path):
    tomorrow = date(2026, 10, 16)
    Archive(tmp_path / "raw").write("ticks", D, "FPT", load("FPT"))
    m, f, repo = run(tmp_path, serve({"VNM": b'{"data": []}'}), today=tomorrow)
    assert (m.status, m.reason, m.symbols_fetched, m.requests) == ("partial", "source_no_longer_serves", 1, 2)
    assert f.replays == 1
    assert m.symbols_skipped == (("VNM", "source_no_longer_serves"),)
    assert (tmp_path / "raw/ticks/2026-10-15/FPT.json.gz").exists()
    assert not (tmp_path / "raw/ticks/2026-10-15/VNM.json.gz").exists()


def test_past_date_empty_first_tape_is_missed(tmp_path):
    m, f, _ = run(tmp_path, serve({"FPT": b'{"data": []}'}), today=date(2026, 10, 16))
    assert (m.status, m.reason, m.symbols_fetched, m.requests) == ("missed", "source_no_longer_serves", 0, 2)
    assert m.symbols_skipped == () and not (tmp_path / "raw/ticks/2026-10-15/FPT.json.gz").exists()


def test_blocked_stops_and_exit_code_2(tmp_path, monkeypatch):
    h = serve({"VNM": lambda: httpx.Response(429)})
    m, f, repo = run(tmp_path, h)
    assert (m.status, m.reason, m.symbols_fetched, m.rows) == ("blocked", "source_blocked", 1, 50)
    assert m.symbols_skipped == (("VNM", "source_blocked"),) and f.requests == 1 + 1 + 3
    assert (tmp_path / "raw/ticks/2026-10-15/_manifest.json").exists()
    monkeypatch.setattr(cli, "run_ticks", lambda *a: m)
    assert cli.main(["ticks", "--date", "2026-10-15"]) == 2


def test_empty_first_tape_is_inconclusive_not_missed(tmp_path):
    m, f, _ = run(tmp_path, serve({"FPT": b'{"data": []}'}))
    assert (m.status, m.reason, m.symbols_fetched, m.rows, m.requests) == ("partial", None, 1, 50, 3)
    assert m.symbols_skipped == (("FPT", "no_ticks"),)


def test_universe_blocked_records_manifest_and_session(tmp_path):
    h = lambda req: httpx.Response(429)  # noqa: E731
    m, f, repo = run(tmp_path, h)
    assert (m.status, m.reason, m.symbols_fetched, m.rows) == ("blocked", "source_blocked", 0, 0)
    on_disk = json.loads((tmp_path / "raw/ticks/2026-10-15/_manifest.json").read_text())
    assert on_disk["status"] == "blocked" and repo.sessions[("ticks", D)].status == "blocked"
    assert repo.runs[1][0] == "blocked"


def test_payload_shape_skips_one_symbol_only(tmp_path):
    bad = load("VNM").replace(b'"FMP"', b'"PRICE"')
    m, _, repo = run(tmp_path, serve({"VNM": bad}))
    assert (m.status, m.reason, m.symbols_fetched, m.rows) == ("partial", None, 1, 50)
    assert m.symbols_skipped == (("VNM", "payload_shape"),) and {k[0] for k in repo.ticks} == {"FPT"}


def test_http_and_timeout_reasons(tmp_path):
    def boom():
        raise httpx.ReadTimeout("slow")

    m, *_ = run(tmp_path / "a", serve({"FPT": lambda: httpx.Response(404), "VNM": boom}))
    assert m.symbols_skipped == (("FPT", "http_404"), ("VNM", "timeout")) and m.status == "partial"
    m, *_ = run(tmp_path / "b", serve({"VNM": lambda: httpx.Response(503)}))
    assert m.symbols_skipped == (("VNM", "http_503"),)


def test_only_skips_universe_and_dedupe_logs_anomaly(tmp_path):
    rows = json.loads(load("FPT"))
    rows["data"].append(dict(rows["data"][0], FMP=rows["data"][0]["FMP"] + 100))  # same (ts, seq), new price
    m, f, repo = run(tmp_path, serve({"FPT": json.dumps(rows).encode()}), only=["fpt".upper()])
    assert (m.universe_source, m.universe_count, m.requests, m.rows) == ("cli:--only", 1, 1, 50)
    assert repo.anomalies == [("FPT", "duplicate_tick", "1")]
    assert next(t for t in repo.ticks.values() if t.seq == rows["data"][0]["AVO"]).price == 58100


def test_weekend_and_only_parsing(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(cli, "run_ticks", lambda s, d, o: seen.append((d, o)) or MagicMock(status="complete"))
    assert cli.main(["ticks", "--date", "2026-10-16", "--only", "fpt, vnm"]) == 0
    assert seen == [(date(2026, 10, 16), ["FPT", "VNM"])]


URL = os.environ.get("FINVEST_DATABASE_URL")


@pytest.mark.db
@pytest.mark.enable_socket
@pytest.mark.skipif(not URL or not URL.rsplit("/", 1)[-1].endswith("_test"), reason="needs a *_test db")
def test_two_runs_against_db(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from finvest_market_data.infrastructure import repositories as repo
    from sqlalchemy import text

    monkeypatch.setenv("FINVEST_DATABASE_URL", URL)  # conftest clears it; alembic env.py reads it
    command.upgrade(Config(str(Path(__file__).parents[3] / "apps/api/alembic.ini")), "head")
    eng = repo.engine(URL)
    with eng.begin() as c:
        for t in ("ticks", "crawl_runs", "crawl_sessions", "data_anomalies"):
            c.execute(text(f"TRUNCATE {t}"))
    st = Settings(_env_file=None, data_dir=tmp_path, database_url=URL)
    with eng.connect() as c:  # caller-owned connection: we commit
        feed.run_ticks(st, D, None, fetcher=make(tmp_path, serve()), conn=c)
        c.commit()
    m = feed.run_ticks(st, D, None, fetcher=make(tmp_path, serve()))  # own connection: run_ticks commits
    with eng.connect() as c:
        assert c.execute(text("SELECT count(*) FROM ticks")).scalar_one() == 100
        assert c.execute(text("SELECT count(*), min(checksum) FROM crawl_sessions")).one() == (1, m.checksum)
        assert c.execute(text("SELECT count(*) FROM data_anomalies")).scalar_one() == 0
    eng.dispose()
