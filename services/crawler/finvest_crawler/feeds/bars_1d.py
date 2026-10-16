"""Daily bars back-fill: symbols table + indices -> archive-first fetch -> upsert -> manifest."""

import hashlib
import json
from datetime import UTC, date, datetime
from types import ModuleType

import httpx
from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.ports import PayloadShapeError
from finvest_market_data.infrastructure import repositories
from sqlalchemy import Connection

from finvest_crawler.adapters.registry import source_for
from finvest_crawler.feeds.ticks import VN, _fetcher, _skip_reason
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.settings import Settings

FEED = "bars_1d"
INDICES = ("VNINDEX", "VN30")
COUNT = 6000  # > 19 years of sessions; V2 daily history starts 2006-12-13 (data.md 1.2)


def run_bars_1d(
    settings: Settings,
    run_date: date,
    *,
    only: list[str] | None = None,
    fetcher: Fetcher | None = None,
    conn: Connection | None = None,
    repo: ModuleType = repositories,  # tests pass an in-memory fake with the same functions
    today: date | None = None,  # VN calendar day; tests inject it
) -> Manifest:
    today = today or datetime.now(VN).date()
    if run_date > today:
        raise ValueError(f"run date {run_date} is in the future (today {today})")
    own_client = httpx.Client() if fetcher is None else None
    fetcher = fetcher or _fetcher(settings, own_client)  # type: ignore[arg-type]
    own_engine = repositories.engine(settings.database_url) if conn is None else None
    conn = conn or own_engine.connect()  # type: ignore[union-attr]
    commit = conn.commit if own_engine else (lambda: None)  # we only commit what we opened
    try:
        return _run(settings, run_date, only, fetcher, conn, repo, commit)
    finally:
        if own_client:
            own_client.close()
        if own_engine:
            conn.close()
            own_engine.dispose()


def _line(*cols: object) -> bytes:
    return (",".join("" if c is None else str(c) for c in cols) + "\n").encode()


def _run(settings, run_date, only, fetcher, conn, repo, commit) -> Manifest:  # noqa: ANN001
    started, req0 = datetime.now(UTC), fetcher.requests
    repo.fail_unfinished_runs(conn, FEED, run_date)
    run_id = repo.insert_crawl_run(conn, FEED, run_date, started)
    commit()
    source = source_for("bars", settings, fetcher)
    try:
        if only:
            names, uni_src = sorted(set(only)), "cli:--only"
        else:
            names = sorted({r.symbol for r in repo.list_symbols(conn, include_delisted=True)} | set(INDICES))
            uni_src = "symbols table"
        # sorted names => per-name sorted lines concatenate into the globally sorted checksum input
        digest, rows, fetched = hashlib.sha256(), 0, 0
        skipped: list[tuple[str, str]] = []
        no_trades: list[str] = []
        status, reason = "complete", None
        for i, name in enumerate(names):
            index = name in INDICES
            try:
                bars = (source.index_bars([name], run_date, COUNT) if index
                        else source.bars([name], "1d", run_date, COUNT))
            except SourceBlocked:
                skipped += [(s, "source_blocked") for s in names[i:]]
                status, reason = "blocked", "source_blocked"
                break
            except (PayloadShapeError, httpx.HTTPError) as e:
                skipped.append((name, _skip_reason(e)))
                continue
            if not bars:
                no_trades.append(name)
                continue
            # one bar per day; the archive file name is the adapter's `<name>-1d-<count>`
            mtime = fetcher.archive.path(FEED, run_date, f"{name}-1d-{COUNT}").stat().st_mtime
            if index:
                repo.upsert_index_1d(conn, bars)
                keys = [_line(b.index_code, b.trading_date, source.name, b.o, b.h, b.l, b.c, b.v, b.value)
                        for b in bars]
            else:
                repo.upsert_bars_1d_src(conn, bars, datetime.fromtimestamp(mtime, UTC))
                keys = [_line(b.symbol, b.trading_date, b.source, b.o, b.h, b.l, b.c, b.v, b.value)
                        for b in bars]
            commit()  # an interrupt loses at most this one name
            for line in sorted(keys):
                digest.update(line)
            rows, fetched = rows + len(bars), fetched + 1
            print(json.dumps({"symbol": name, "rows": len(bars)}))
        if status == "complete" and skipped:
            status = "partial"
        assert fetched + len(no_trades) + len(skipped) == len(names), (
            fetched, no_trades, skipped, len(names))
        m = Manifest(FEED, run_date, source.name, started, datetime.now(UTC), status, reason,
                     fetcher.requests - req0, rows, "sha256:" + digest.hexdigest(), fetched, tuple(skipped),
                     tuple(no_trades), uni_src, started, len(names))
        path = fetcher.archive.write_manifest(FEED, run_date, m.to_dict())
        repo.upsert_crawl_session(conn, m)
        repo.finish_crawl_run(conn, run_id, m.status, m.reason, m.requests, m.rows, str(path))
        coverage = {k: str(v) for k, v in repo.daily_coverage(conn).items()}
        commit()
    except Exception:
        conn.rollback()
        repo.finish_crawl_run(conn, run_id, "failed", None, fetcher.requests - req0, 0, None)
        commit()
        raise
    print(json.dumps({"summary": m.status, "reason": m.reason, "date": str(run_date), "fetched": fetched,
                      "no_trades": len(no_trades), "skipped": len(skipped), "rows": rows,
                      "requests": m.requests, "coverage": coverage}))
    return m
