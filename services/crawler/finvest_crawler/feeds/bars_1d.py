"""Daily bars back-fill: symbols table + indices -> archive-first fetch -> upsert -> manifest."""

import hashlib
import json
from collections.abc import Callable
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
# V2 serves one symbol per call (S-v2-batch spike 2026-10-24: ["FPT","VNM"] -> []); raise after a re-measure
BATCH_MAX = 1
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
    count: int = COUNT,
    on_progress: Callable[[int, int], None] | None = None,  # (names done, names total)
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
        return _run(settings, run_date, only, fetcher, conn, repo, commit, count, on_progress)
    finally:
        if own_client:
            own_client.close()
        if own_engine:
            conn.close()
            own_engine.dispose()


def _line(*cols: object) -> bytes:
    return (",".join("" if c is None else str(c) for c in cols) + "\n").encode()


def _run(settings, run_date, only, fetcher, conn, repo, commit, count=COUNT, on_progress=None) -> Manifest:  # noqa: ANN001
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
        digest, rows, fetched = hashlib.sha256(), 0, 0
        skipped: list[tuple[str, str]] = []
        no_trades: list[str] = []
        status, reason = "complete", None
        # the checksum input is the per-name sorted lines in name order; indices are fetched first, so their
        # lines wait here until the symbol stream passes their name
        held: list[tuple[str, list[bytes]]] = []

        def feed(name: str, keys: list[bytes]) -> None:
            while held and held[0][0] < name:
                for line in held.pop(0)[1]:
                    digest.update(line)
            for line in keys:
                digest.update(line)

        idx = [n for n in names if n in INDICES]
        stocks = [n for n in names if n not in INDICES]
        size = max(1, min(BATCH_MAX, 50_000 // count))
        units = [[n] for n in idx] + [stocks[i:i + size] for i in range(0, len(stocks), size)]
        done = 0
        for u, unit in enumerate(units):
            index = unit[0] in INDICES
            try:
                bars = (source.index_bars(unit, run_date, COUNT) if index
                        else source.bars(unit, "1d", run_date, count))
            except SourceBlocked:
                skipped += [(s, "source_blocked") for rest in units[u:] for s in rest]
                status, reason = "blocked", "source_blocked"
                break
            except (PayloadShapeError, httpx.HTTPError) as e:
                skipped += [(s, _skip_reason(e)) for s in unit]
                done += len(unit)
                if on_progress:
                    on_progress(done, len(names))
                continue
            by_name: dict[str, list] = {n: [] for n in unit}
            for b in bars:
                by_name.get(b.index_code if index else b.symbol, []).append(b)
            got = [n for n in unit if by_name[n]]
            no_trades += [n for n in unit if not by_name[n]]
            if got and index:
                repo.upsert_index_1d(conn, bars)
            elif got:
                # fetched_at is the archive file's mtime, so a replay hits the same key
                mtime = fetcher.archive.path(FEED, run_date, source.archive_name(unit, count)).stat().st_mtime
                repo.upsert_bars_1d_src(conn, bars, datetime.fromtimestamp(mtime, UTC))
            commit()  # an interrupt loses at most this one batch
            for n in got:
                keys = sorted(
                    _line(b.index_code, b.trading_date, source.name, b.o, b.h, b.l, b.c, b.v, b.value)
                    if index
                    else _line(b.symbol, b.trading_date, b.source, b.o, b.h, b.l, b.c, b.v, b.value)
                    for b in by_name[n])
                if index:
                    held.append((n, keys))
                else:
                    feed(n, keys)
                rows, fetched = rows + len(keys), fetched + 1
                print(json.dumps({"symbol": n, "rows": len(keys)}))
            done += len(unit)
            if on_progress:
                on_progress(done, len(names))
        feed("\U0010ffff", [])  # flush the indices that sort after the last symbol
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
