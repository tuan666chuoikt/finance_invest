"""Ticks feed: universe -> archive-first fetch -> upsert -> manifest (platform.md 4, ADR-S-008)."""

import hashlib
import json
import re
import time
from datetime import UTC, date, datetime
from types import ModuleType
from zoneinfo import ZoneInfo

import httpx
from finvest_market_data.domain.manifest import Manifest, canonical_line, dedupe
from finvest_market_data.domain.ports import PayloadShapeError, SourceNoLongerServes
from finvest_market_data.infrastructure import repositories
from sqlalchemy import Connection

from finvest_crawler.adapters.registry import source_for
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings

FEED = "ticks"
VN = ZoneInfo("Asia/Ho_Chi_Minh")
PROBE_SYMBOLS = ("FPT", "HPG", "VNM")  # liquid: all three empty = day not served


def _skip_reason(e: Exception) -> str:
    if isinstance(e, PayloadShapeError):
        return "payload_shape"
    if isinstance(e, httpx.HTTPStatusError):
        return f"http_{e.response.status_code}"
    m = re.search(r"last status (\d+)", str(e))  # Fetcher's "failed after N tries" error
    return f"http_{m[1]}" if m and m[1] != "0" else "timeout"


def _fetcher(settings: Settings, client: httpx.Client) -> Fetcher:
    buckets = {n: TokenBucket(r) for n, r in settings.rate_per_s.items()}
    return Fetcher(client, buckets, Archive(settings.data_dir / "raw"), settings.user_agent)


def run_ticks(
    settings: Settings,
    trading_date: date,
    only: list[str] | None,
    *,
    fetcher: Fetcher | None = None,
    conn: Connection | None = None,
    repo: ModuleType = repositories,  # tests pass an in-memory fake with the same functions
    today: date | None = None,  # VN calendar day; tests inject it
) -> Manifest:
    own_client = httpx.Client() if fetcher is None else None
    fetcher = fetcher or _fetcher(settings, own_client)  # type: ignore[arg-type]
    own_engine = repositories.engine(settings.database_url) if conn is None else None
    conn = conn or own_engine.connect()  # type: ignore[union-attr]
    # we only commit what we opened: a caller-supplied conn keeps its own transaction
    commit = conn.commit if own_engine else (lambda: None)
    try:
        today = today or datetime.now(VN).date()
        return _run(settings, trading_date, only, fetcher, conn, repo, commit, today)
    finally:
        if own_client:
            own_client.close()
        if own_engine:
            conn.close()
            own_engine.dispose()


def _run(settings, trading_date, only, fetcher, conn, repo, commit, today) -> Manifest:  # noqa: ANN001
    started, req0 = datetime.now(UTC), fetcher.requests
    repo.fail_unfinished_runs(conn, FEED, trading_date)
    run_id = repo.insert_crawl_run(conn, FEED, trading_date, started)
    commit()
    source = source_for("ticks", settings, fetcher)
    blocked = False
    try:
        if only:
            names, uni_src, as_of = sorted(set(only)), "cli:--only", started
        else:
            uni_src, as_of, names = "vci:symbols/getAll", datetime.now(UTC), []
            try:
                recs = source_for("symbols", settings, fetcher).symbols(trading_date)
                names = sorted(r.symbol for r in recs)
                # the archived file's mtime = when the universe was really fetched, stable across replays
                mtime = fetcher.archive.path("symbols", trading_date, "getAll").stat().st_mtime
                as_of = datetime.fromtimestamp(mtime, UTC)
            except SourceBlocked:
                blocked = True  # no universe, nothing to fetch: record `blocked` below like an in-loop block
        # sorted symbols => per-symbol sorted lines concatenate into the globally sorted checksum input
        digest, rows, fetched = hashlib.sha256(), 0, 0
        skipped: list[tuple[str, str]] = []
        no_trades: list[str] = []
        status, reason = ("blocked", "source_blocked") if blocked else ("complete", None)
        todo, probed = names, {}
        if not blocked and not only and trading_date < today:
            # past day: an empty tape is "no trades" only once a probe proves the source still serves it
            empties = 0
            for p in PROBE_SYMBOLS:
                try:
                    probed[p] = source.ticks(p, trading_date)
                    break
                except SourceNoLongerServes as e:
                    if e.served_date is not None:
                        todo, status, reason = [], "missed", "source_no_longer_serves"
                        break
                    empties += 1
                except SourceBlocked:
                    todo, skipped = [], [(s, "source_blocked") for s in names]
                    status, reason = "blocked", "source_blocked"
                    break
                except (PayloadShapeError, httpx.HTTPError):
                    pass  # inconclusive probe: fall through to the normal loop
            if todo and empties == len(PROBE_SYMBOLS):
                todo, status, reason = [], "missed", "source_no_longer_serves"
        for i, sym in enumerate(todo):
            t0, replays0 = time.perf_counter(), fetcher.replays
            try:
                tape = probed[sym] if sym in probed else source.ticks(sym, trading_date)
            except SourceNoLongerServes as e:
                # another session served: the source moved on, stop.
                # An empty tape is no trades for that name (platform.md §4): not a skip, carry on.
                if e.served_date is not None:
                    status, reason = ("missed" if not fetched else "partial"), "source_no_longer_serves"
                    skipped += [(s, "source_no_longer_serves") for s in names[i:]] if fetched else []
                    break
                no_trades.append(sym)
                continue
            except SourceBlocked:
                skipped += [(s, "source_blocked") for s in names[i:]]
                status, reason = "blocked", "source_blocked"
                break
            except (PayloadShapeError, httpx.HTTPError) as e:
                skipped.append((sym, _skip_reason(e)))
                continue
            kept, displaced = dedupe(tape)
            changed = repo.upsert_ticks(conn, kept)
            if displaced or changed:
                repo.insert_anomaly(conn, sym, trading_date, "duplicate_tick", str(len(displaced) + changed))
            commit()
            for line in sorted(canonical_line(t).encode() + b"\n" for t in kept):
                digest.update(line)
            rows, fetched = rows + len(kept), fetched + 1
            print(json.dumps({"symbol": sym, "rows": len(kept), "replayed": fetcher.replays > replays0,
                              "ms": round((time.perf_counter() - t0) * 1000)}))
        if status == "complete" and skipped:
            status = "partial"
        # no-trade is not a skip, so `complete` needs only an empty `skipped`; every symbol is accounted for
        assert fetched + len(no_trades) + len(skipped) == len(names) or status == "missed", (
            fetched, no_trades, skipped, len(names))
        m = Manifest(FEED, trading_date, source.name, started, datetime.now(UTC), status, reason,
                     fetcher.requests - req0, rows, "sha256:" + digest.hexdigest(), fetched, tuple(skipped),
                     tuple(no_trades), uni_src, as_of, len(names))
        path = fetcher.archive.write_manifest(FEED, trading_date, m.to_dict())
        repo.upsert_crawl_session(conn, m)
        repo.finish_crawl_run(conn, run_id, m.status, m.reason, m.requests, m.rows, str(path))
        commit()
    except Exception:
        conn.rollback()
        repo.finish_crawl_run(conn, run_id, "failed", None, fetcher.requests - req0, 0, None)
        commit()
        raise
    print(json.dumps({"summary": m.status, "reason": m.reason, "date": str(trading_date), "fetched": fetched,
                      "skipped": len(skipped), "rows": rows, "requests": m.requests}))
    return m
