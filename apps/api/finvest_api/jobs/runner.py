"""Manual crawl job (platform.md 2.6): one background thread, one job at a time."""

import threading
import time
from datetime import UTC, date, datetime, timedelta

import httpx
from finvest_crawler.feeds.bars_1d import COUNT, run_bars_1d
from finvest_crawler.feeds.ticks import run_ticks
from finvest_crawler.fetch import SourceBlocked
from finvest_crawler.settings import Settings
from finvest_market_data.infrastructure.tables import bars_1d_src, index_1d
from finvest_rules.calendar import day, trading_days
from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Engine

from ..deps import VN
from . import jobs

_lock = threading.Lock()
CLOSE_HOUR = 15  # VN close; before it the tape is partial (platform.md 4)


def _now() -> datetime:  # tests monkeypatch this
    return datetime.now(VN)


def _write(engine: Engine, job_id: int, **vals) -> None:
    with engine.begin() as c:
        c.execute(update(jobs).where(jobs.c.id == job_id).values(**vals))


def _count(engine: Engine, today: date) -> int:
    """Sessions since the oldest last bar of bars_1d_src / index_1d, +2, min 5 (platform.md 2.6)."""
    with engine.connect() as c:
        maxes = (c.execute(select(func.max(t.c.trading_date))).scalar() for t in (bars_1d_src, index_1d))
        lasts = [d for d in maxes if d]
    if not lasts:
        return COUNT
    return max(5, len(trading_days(min(lasts) + timedelta(1), today)) + 2)


def _sessions(engine: Engine) -> int:
    with engine.connect() as c:
        return c.execute(select(func.count(func.distinct(bars_1d_src.c.trading_date)))).scalar_one()


def _error(e: BaseException) -> dict:
    if isinstance(e, _Blocked):
        return {"code": "SourceBlocked", "message": str(e), "source": e.source}
    err = {"code": type(e).__name__, "message": str(e)}
    if isinstance(e, OSError) and e.filename:
        err["path"] = str(e.filename)
    if isinstance(e, SourceBlocked):
        err["source"], err["http_status"] = e.source, e.last_status
    elif isinstance(e, httpx.HTTPStatusError):
        err["http_status"] = e.response.status_code
    return err


class _Blocked(Exception):
    """A step ended `blocked`: the crawler swallowed SourceBlocked and returned a manifest instead."""

    def __init__(self, m):
        super().__init__(f"source {m.source} blocked the crawl")
        self.source = m.source


def _run(engine: Engine, settings: Settings, job_id: int) -> None:
    t0 = time.monotonic()
    summary: dict = {"ticks": None, "bars_1d": None, "no_session_today": False}
    prog: dict = {"step": 1, "steps": 2, "label": "ticks", "trading_date": None, "done": 0, "total": 0}
    last = [float("-inf")]

    def on_progress(done: int, total: int) -> None:
        prog.update(done=done, total=total)
        if time.monotonic() - last[0] >= 2:  # at most one write per 2 s
            last[0] = time.monotonic()
            _write(engine, job_id, progress=dict(prog))

    def step(n: int, label: str, d: date) -> None:
        prog.update(step=n, label=label, trading_date=d.isoformat(), done=0, total=0)
        last[0] = float("-inf")
        _write(engine, job_id, progress=dict(prog))

    status, error = "done", None
    try:
        now = _now()
        today = now.date()
        if day(today).is_open:
            step(1, "ticks", today)
            m = run_ticks(settings, today, None, today=today, on_progress=on_progress)
            summary["ticks"] = {
                "trading_date": m.trading_date.isoformat(), "status": m.status,
                "symbols_fetched": m.symbols_fetched, "rows": m.rows,
                "symbols_skipped": len(m.symbols_skipped),
                "partial_until": now.isoformat(timespec="seconds") if now.hour < CLOSE_HOUR else None,
            }
            _write(engine, job_id, summary=dict(summary))
            if m.status == "blocked":  # rate budget is shared: skip step 2
                raise _Blocked(m)
        else:
            summary["no_session_today"] = True
        step(2, "bars_1d", today)
        before = _sessions(engine)
        m = run_bars_1d(settings, today, today=today, count=_count(engine, today), on_progress=on_progress)
        summary["bars_1d"] = {"sessions_added": _sessions(engine) - before,
                              "symbols_fetched": m.symbols_fetched, "symbols_skipped": len(m.symbols_skipped)}
        if m.status == "blocked":
            raise _Blocked(m)
    except Exception as e:  # any failure is reported on the row, never lost in the thread
        status, error = "failed", _error(e)
    finally:
        summary["duration_s"] = round(time.monotonic() - t0)
        try:
            _write(engine, job_id, status=status, finished_at=datetime.now(UTC), progress=prog,
                   summary=summary, error=error)
        finally:
            _lock.release()


def start_crawl(engine: Engine, settings: Settings) -> int | None:
    """Insert the `running` row and start the thread; None when a crawl already runs."""
    if not _lock.acquire(blocking=False):
        return None
    try:
        with engine.begin() as c:
            if c.execute(select(jobs.c.id).where(jobs.c.kind == "crawl", jobs.c.status == "running")).first():
                _lock.release()  # a stale `running` row (failed final write, other worker) also blocks (2.6)
                return None
            job_id = c.execute(insert(jobs).values(kind="crawl", args={}, status="running",
                                                   created_at=datetime.now(UTC)).returning(jobs.c.id)).scalar_one()
        threading.Thread(target=_run, args=(engine, settings, job_id), daemon=True).start()
    except BaseException:
        _lock.release()
        raise
    return job_id


def mark_interrupted(engine: Engine) -> None:
    """Start-up: the thread of a `running` row died with the previous process."""
    err = {"code": "interrupted", "message": "the api restarted while the job was running"}
    with engine.begin() as c:
        c.execute(update(jobs).where(jobs.c.status == "running").values(
            status="failed", finished_at=datetime.now(UTC), error=err))
