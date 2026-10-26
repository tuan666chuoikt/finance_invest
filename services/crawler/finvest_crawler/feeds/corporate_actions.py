"""Crawl step 3: V5 corporate events per symbol under a request budget -> upsert + diff log -> crawl_runs row
(platform.md 2.6 v1.14, data.md 1.2 V5 / 4). No manifest: the ledger row is `crawl_runs` only."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import ModuleType

import httpx
from finvest_market_data.infrastructure import repositories
from sqlalchemy import Connection

from finvest_crawler.adapters.vci.events import fetch_events
from finvest_crawler.feeds.ticks import _fetcher
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.settings import Settings

FEED = "corporate_actions"
SOURCE = "vci_iq"


@dataclass
class CaResult:
    status: str = "ok"  # ok | partial | blocked
    symbols_checked: int = 0
    events_upserted: int = 0
    changes: int = 0  # corporate_action_log rows written
    symbols_deferred: int = 0  # listed names not read this press
    requests: int = 0
    changed_symbols: list[str] = field(default_factory=list)  # new or changed events: input of the recompute
    source: str = SOURCE
    run_id: int = 0  # the crawl_runs row, so the runner can note the recompute on it


def run_corporate_actions(
    settings: Settings,
    run_date: date,
    *,
    budget: int | None = None,
    on_progress: Callable[[int, int], None] | None = None,  # (symbols read, symbols this press can read)
    fetcher: Fetcher | None = None,
    conn: Connection | None = None,
    repo: ModuleType = repositories,  # tests pass an in-memory fake with the same functions
) -> CaResult:
    budget = settings.ca_budget if budget is None else budget
    own_client = httpx.Client() if fetcher is None else None
    fetcher = fetcher or _fetcher(settings, own_client)  # type: ignore[arg-type]
    own_engine = repo.engine(settings.database_url) if conn is None else None
    conn = conn or own_engine.connect()  # type: ignore[union-attr]
    commit = conn.commit if own_engine else (lambda: None)  # we only commit what we opened
    try:
        return _run(run_date, budget, on_progress, fetcher, conn, repo, commit)
    finally:
        if own_client:
            own_client.close()
        if own_engine:
            conn.close()
            own_engine.dispose()


def _run(run_date, budget, on_progress, fetcher, conn, repo, commit) -> CaResult:  # noqa: ANN001
    started, req0 = datetime.now(UTC), fetcher.requests
    repo.fail_unfinished_runs(conn, FEED, run_date)
    run_id = repo.insert_crawl_run(conn, FEED, run_date, started)
    commit()
    r = CaResult(run_id=run_id)
    try:
        order = repo.ca_symbols_in_order(conn)
        total = min(len(order), max(budget - 1, 0))  # every read costs at least one request
        if on_progress:
            on_progress(0, total)
        for sym in order:
            if fetcher.requests - req0 + 1 >= budget:  # the next read may not fit: the rest is deferred
                r.status = "partial"
                break
            try:
                rows, anomalies, _ = fetch_events(fetcher, sym, run_date)
            except SourceBlocked:
                r.status = "blocked"
                break
            known = {e.source_event_id for e in repo.corporate_actions_for(conn, [sym])[sym]}
            upserted, changes = repo.upsert_corporate_actions(conn, rows, datetime.now(UTC))
            ex = {e.source_event_id: e.ex_date for e in rows}
            for event_id, rule in anomalies:  # an unmapped event has no row, so no ex_date
                repo.insert_anomaly(conn, sym, ex.get(event_id), rule, event_id)
            repo.mark_ca_checked(conn, [sym], datetime.now(UTC))
            commit()  # an interrupt loses at most this one symbol
            r.symbols_checked += 1
            r.events_upserted += upserted
            r.changes += changes
            if changes or set(ex) - known:
                r.changed_symbols.append(sym)
            if on_progress:
                on_progress(r.symbols_checked, total)
        r.symbols_deferred = len(order) - r.symbols_checked
        r.requests = fetcher.requests - req0
        repo.finish_crawl_run(conn, run_id, r.status, "source_blocked" if r.status == "blocked" else None,
                              r.requests, r.events_upserted, None)
        commit()
    except Exception:
        conn.rollback()
        repo.finish_crawl_run(conn, run_id, "failed", None, fetcher.requests - req0, 0, None)
        commit()
        raise
    return r
