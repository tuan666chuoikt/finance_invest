"""symbols feed against the compose db (needs FINVEST_DATABASE_URL, db name *_test) plus one blocked case."""

import gzip
import json
import os
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from alembic import command
from alembic.config import Config
from finvest_crawler.archive import Archive
from finvest_crawler.feeds.symbols import run_symbols
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from finvest_market_data.infrastructure import repositories as repo
from sqlalchemy import text
from sqlalchemy.engine import make_url

URL = os.environ.get("FINVEST_DATABASE_URL")
INI = Path(__file__).parents[3] / "apps" / "api" / "alembic.ini"
SAMPLE = gzip.decompress((Path(__file__).parent / "fixtures/vci/symbols_getAll/sample.json.gz").read_bytes())
D1, D2, D3 = date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 17)


def feed(tmp_path, conn, run_date, payload=SAMPLE, repo=repo):
    f = Fetcher(
        httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=payload))),
        {"vci": TokenBucket(1000)}, Archive(tmp_path / "raw"), "ua", sleep=lambda s: None)
    run_symbols(Settings(_env_file=None, data_dir=tmp_path), run_date, fetcher=f, conn=conn, repo=repo)
    return f


def without(symbol: str) -> bytes:
    return json.dumps([r for r in json.loads(SAMPLE) if r["symbol"] != symbol]).encode()


def table(conn):
    return conn.execute(text("SELECT * FROM symbols ORDER BY symbol")).all()


def test_blocked_source_is_recorded_and_raised(tmp_path):
    fake = MagicMock()
    with pytest.raises(SourceBlocked):
        feed(tmp_path, MagicMock(), D1, payload=b"<html>Just a moment</html>", repo=fake)
    assert fake.finish_crawl_run.call_args.args[2:4] == ("blocked", "source_blocked")
    fake.upsert_symbols.assert_not_called()


@pytest.mark.db
@pytest.mark.enable_socket
@pytest.mark.skipif(not URL, reason="FINVEST_DATABASE_URL not set")
@pytest.mark.skipif(
    bool(URL) and not (make_url(URL).database or "").endswith("_test"),
    reason="db name must end in _test (tests drop all tables)")
class TestDb:
    @pytest.fixture(autouse=True)
    def conn(self, monkeypatch):
        monkeypatch.setenv("FINVEST_DATABASE_URL", URL)  # conftest strips FINVEST_*; alembic env.py reads it
        cfg = Config(str(INI))
        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")
        e = repo.engine(URL)  # type: ignore[arg-type]
        with e.begin() as c:
            yield c
        e.dispose()

    def test_rerun_is_identical_and_replays(self, tmp_path, conn):
        f = feed(tmp_path, conn, D1)
        first = table(conn)
        assert (f.requests, len(first)) == (1, 32)
        assert sum(r.is_delisted for r in first) == 5
        f = feed(tmp_path, conn, D1)
        assert (f.requests, f.replays) == (0, 1)
        assert table(conn) == first  # F-004 criterion 3: same rows, same fetched_at
        rules = conn.execute(text("SELECT rule, count(*) FROM data_anomalies GROUP BY rule")).all()
        assert rules == [("delisted_exchange_unknown", 5)]  # written once, not per run

    def test_vanished_then_relisted(self, tmp_path, conn):
        feed(tmp_path, conn, D1)
        gone = next(r["symbol"] for r in json.loads(SAMPLE) if r["board"] == "HNX" and r["type"] == "STOCK")
        feed(tmp_path, conn, D2, without(gone))
        rows = table(conn)
        assert len(rows) == 32  # never deleted
        row = next(r for r in rows if r.symbol == gone)
        assert (row.is_delisted, row.delisted_at, row.exchange) == (True, D2, "HNX")
        feed(tmp_path, conn, D3)  # back
        row = next(r for r in table(conn) if r.symbol == gone)
        assert (row.is_delisted, row.delisted_at) == (False, D2)
        relisted = text("SELECT symbol FROM data_anomalies WHERE rule='relisted'")
        assert conn.execute(relisted).scalars().all() == [gone]
        q = text("SELECT status, rows FROM crawl_runs WHERE feed='symbols' ORDER BY id")
        runs = conn.execute(q).all()
        assert runs == [("ok", 32), ("ok", 31), ("ok", 32)]
