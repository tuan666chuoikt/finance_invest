"""Daily bars back-fill: symbols table + indices -> archive-first fetch -> upsert -> manifest."""

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, date, datetime
from types import ModuleType

import httpx
from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.ports import PayloadShapeError, SourceNoLongerServes, Unsupported
from finvest_market_data.infrastructure import repositories
from sqlalchemy import Connection

from finvest_crawler.adapters.registry import source_for
from finvest_crawler.feeds.ticks import FAIL_RUN, VN, _fetcher, _skip_reason
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.settings import Settings

FEED = "bars_1d"
INDICES = ("VNINDEX", "VN30")
# V2 serves one symbol per call (S-v2-batch spike 2026-10-24: ["FPT","VNM"] -> []); raise after a re-measure
BATCH_MAX = 1
GAP_MAX = 40  # names fetched per press after the snapshot, oldest last bar first; the rest are `deferred`
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
    gap_max: int | None = None,  # cap on gap names fetched in this run (None = all); the rest are `deferred`
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
        return _run(settings, run_date, only, fetcher, conn, repo, commit, count, on_progress, gap_max)
    finally:
        if own_client:
            own_client.close()
        if own_engine:
            conn.close()
            own_engine.dispose()


def _line(*cols: object) -> bytes:
    return (",".join("" if c is None else str(c) for c in cols) + "\n").encode()


def _run(  # noqa: ANN001
    settings, run_date, only, fetcher, conn, repo, commit, count=COUNT, on_progress=None, gap_max=None
) -> Manifest:
    """symbols_fetched = names whose bar for run_date is in the table after the run: snapshot names with a
    bar, gap names that returned bars, and names already current before the run; board no-trades -> no_trades;
    deferred and failed names -> skipped."""
    started, req0 = datetime.now(UTC), fetcher.requests
    repo.fail_unfinished_runs(conn, FEED, run_date)
    run_id = repo.insert_crawl_run(conn, FEED, run_date, started)
    commit()
    source = source_for("bars", settings, fetcher)
    try:
        if only:
            names, uni_src = sorted(set(only)), "cli:--only"
        else:
            # a catch-up press leaves the delisted names alone; a back-fill keeps them (survivorship, PR-075)
            listed = repo.list_symbols(conn, include_delisted=count >= COUNT)
            names, uni_src = sorted({r.symbol for r in listed} | set(INDICES)), "symbols table"
        digest, rows = hashlib.sha256(), 0
        skipped: list[tuple[str, str]] = []
        no_trades: list[str] = []
        have: set[str] = set()  # names with a bar for run_date (= symbols_fetched)
        done: set[str] = set()  # names with an outcome: progress, and what a blocked run leaves over
        board: set[str] = set()  # names the snapshot answered for (bar or no trade)
        status, reason, streak = "complete", None, 0
        # the checksum input is the per-name sorted lines in name order; indices and snapshot names are held
        # until the (name-sorted) gap stream passes their name
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

        def units():  # lazy: the gaps depend on what the snapshot unit just answered
            for n in idx:
                yield "index", [n]
            if not only:
                yield "snapshot", []
            last = repo.last_bar_dates(conn)
            lag = {n: last.get(n, date.min) for n in stocks if n not in board}
            gaps = sorted((n for n in lag if lag[n] < run_date), key=lambda n: (lag[n], n))
            current = [n for n in lag if lag[n] >= run_date]  # on no board, bar already stored: 0 requests
            have.update(current)
            done.update(current)
            if gap_max is not None:
                gaps, deferred = gaps[:gap_max], gaps[gap_max:]
                skipped.extend((n, "deferred") for n in deferred)
                done.update(deferred)
            gaps.sort()  # fetched in name order so the checksum streams
            if not gaps and on_progress:
                on_progress(len(done), len(names))
            for i in range(0, len(gaps), size):
                yield "gaps", gaps[i:i + size]

        for kind, unit in units():
            index = kind == "index"
            try:
                if kind == "snapshot":
                    bars, idle = source_for("snapshot", settings, fetcher).snapshot_bars(run_date)
                elif index:
                    bars = source.index_bars(unit, run_date, COUNT)
                else:
                    bars = source.bars(unit, "1d", run_date, count)
            except SourceBlocked:
                status, reason = "blocked", "source_blocked"
                break
            except (SourceNoLongerServes, Unsupported) as e:
                if kind != "snapshot":
                    raise
                # its names become gaps
                print(json.dumps({"snapshot": "skipped", "reason": type(e).__name__}))
                continue
            except (PayloadShapeError, httpx.HTTPError) as e:
                if kind == "snapshot":
                    print(json.dumps({"snapshot": "skipped", "reason": _skip_reason(e)}))
                else:
                    skipped += [(s, _skip_reason(e)) for s in unit]
                    done.update(unit)
                    if on_progress:
                        on_progress(len(done), len(names))
                streak += 1
                if streak >= FAIL_RUN:
                    status, reason = "blocked", "source_blocked"
                    break
                continue
            streak = 0
            wanted = set(stocks if kind == "snapshot" else unit)
            by_name: dict[str, list] = {}
            for b in bars:
                if (b.index_code if index else b.symbol) in wanted:
                    by_name.setdefault(b.index_code if index else b.symbol, []).append(b)
            if kind == "snapshot":
                idle = [n for n in idle if n in wanted and n not in by_name]
                board.update(by_name, idle)
                unit = sorted(by_name) + idle
                no_trades += idle
            else:
                no_trades += [n for n in unit if n not in by_name]
            if by_name:
                kept = [b for g in by_name.values() for b in g]
                if index:
                    repo.upsert_index_1d(conn, kept)
                else:
                    # fetched_at is the archive file's mtime, so a replay hits the same key
                    arch = "board-hose" if kind == "snapshot" else source.archive_name(unit, count)
                    mtime = fetcher.archive.path(FEED, run_date, arch).stat().st_mtime
                    repo.upsert_bars_1d_src(conn, kept, datetime.fromtimestamp(mtime, UTC))
            commit()  # an interrupt loses at most this one unit
            for n in sorted(by_name):
                keys = sorted(
                    _line(b.index_code, b.trading_date, source.name, b.o, b.h, b.l, b.c, b.v, b.value)
                    if index
                    else _line(b.symbol, b.trading_date, b.source, b.o, b.h, b.l, b.c, b.v, b.value)
                    for b in by_name[n])
                if kind == "gaps":
                    feed(n, keys)
                else:
                    held.append((n, keys))
                rows += len(keys)
                have.add(n)
                if kind != "snapshot":
                    print(json.dumps({"symbol": n, "rows": len(keys)}))
            held.sort(key=lambda h: h[0])
            done.update(unit)
            # T5: the ledger shows a live partial/running row; the final manifest replaces it (rows only grow)
            repo.upsert_crawl_session(conn, Manifest(
                FEED, run_date, source.name, started, datetime.now(UTC), "partial", "running",
                fetcher.requests - req0, rows, "", len(have), tuple(skipped), tuple(sorted(no_trades)),
                uni_src, started, len(names)))
            commit()
            if on_progress:
                on_progress(len(done), len(names))
        if status == "blocked":
            skipped += [(n, "source_blocked") for n in names if n not in done]
        feed("\U0010ffff", [])  # flush the held names that sort after the last gap
        if status == "complete" and skipped:
            status = "partial"
        fetched = len(have)
        assert fetched + len(no_trades) + len(skipped) == len(names), (
            fetched, no_trades, skipped, len(names))
        m = Manifest(FEED, run_date, source.name, started, datetime.now(UTC), status, reason,
                     fetcher.requests - req0, rows, "sha256:" + digest.hexdigest(), fetched, tuple(skipped),
                     tuple(sorted(no_trades)), uni_src, started, len(names))
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
