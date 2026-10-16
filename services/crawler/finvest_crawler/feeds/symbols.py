"""Symbols feed: V3 symbol master -> `symbols` table, delisted kept (platform.md 4 "Other feeds", F-004)."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from types import ModuleType

import httpx
from finvest_market_data.infrastructure import repositories
from sqlalchemy import Connection

from finvest_crawler.adapters.registry import source_for
from finvest_crawler.feeds.ticks import _fetcher
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.settings import Settings

FEED = "symbols"


def run_symbols(
    settings: Settings,
    run_date: date,
    *,
    fetcher: Fetcher | None = None,
    conn: Connection | None = None,
    repo: ModuleType = repositories,  # tests pass an in-memory fake with the same functions
) -> int:
    """Upsert the master list for `run_date`; return how many symbols the payload held (delisted incl.)."""
    own_client = httpx.Client() if fetcher is None else None
    fetcher = fetcher or _fetcher(settings, own_client)  # type: ignore[arg-type]
    own_engine = repositories.engine(settings.database_url) if conn is None else None
    conn = conn or own_engine.connect()  # type: ignore[union-attr]
    commit = conn.commit if own_engine else (lambda: None)  # we only commit what we opened
    try:
        return _run(settings, run_date, fetcher, conn, repo, commit)
    finally:
        if own_client:
            own_client.close()
        if own_engine:
            conn.close()
            own_engine.dispose()


def _run(settings, run_date, fetcher, conn, repo, commit) -> int:  # noqa: ANN001
    started, req0 = datetime.now(UTC), fetcher.requests
    repo.fail_unfinished_runs(conn, FEED, run_date)
    run_id = repo.insert_crawl_run(conn, FEED, run_date, started)
    commit()
    status, reason, n = "ok", None, 0
    try:
        try:
            recs = source_for("symbols", settings, fetcher).symbols(run_date, include_delisted=True)
        except SourceBlocked:
            status, reason = "blocked", "source_blocked"
            raise
        # fetched_at = archive mtime, so replaying the same day rewrites identical rows
        mtime = fetcher.archive.path(FEED, run_date, "getAll").stat().st_mtime
        known = {r.symbol: r for r in repo.list_symbols(conn)}
        out, relisted, unknown_exchange = [], [], []
        for r in recs:
            old = known.get(r.symbol)
            if r.is_delisted:
                r = replace(r, delisted_at=run_date)
                if old is None:
                    unknown_exchange.append(r.symbol)
            elif old is not None and old.is_delisted:
                relisted.append(r.symbol)
            out.append(r)
        repo.upsert_symbols(conn, out, datetime.fromtimestamp(mtime, UTC))
        gone = repo.mark_delisted(conn, {r.symbol for r in recs}, run_date)
        for sym in unknown_exchange:
            repo.insert_anomaly(conn, sym, run_date, "delisted_exchange_unknown", None)
        for sym in relisted:
            repo.insert_anomaly(conn, sym, run_date, "relisted", None)
        n = len(recs)
        repo.finish_crawl_run(conn, run_id, status, reason, fetcher.requests - req0, n, None)
        commit()
    except Exception:
        conn.rollback()
        repo.finish_crawl_run(
            conn, run_id, status if reason else "failed", reason, fetcher.requests - req0, 0, None)
        commit()
        raise
    print(json.dumps({"summary": status, "date": str(run_date), "symbols": n,
                      "delisted": sum(r.is_delisted for r in recs), "gone": gone, "relisted": len(relisted),
                      "requests": fetcher.requests - req0}))
    return n
