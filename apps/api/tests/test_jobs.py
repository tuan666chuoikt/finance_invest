import threading
import time
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
from finvest_api.deps import VN, get_engine
from finvest_api.jobs import jobs, runner
from finvest_market_data.infrastructure import tables
from sqlalchemy import insert, select

TRADING = datetime(2026, 10, 26, 16, 0, tzinfo=VN)  # Monday, after the close
SUNDAY = datetime(2026, 10, 25, 10, 0, tzinfo=VN)


def _m(rows=0, status="complete"):
    return SimpleNamespace(trading_date=date(2026, 10, 26), status=status, source="kbs", symbols_fetched=30,
                           rows=rows, symbols_skipped=())


@pytest.fixture
def make_client(make_client, tmp_path):
    """The job thread writes while the test reads: one in-memory connection would be shared by both."""
    return lambda seed=True: make_client(seed, path=tmp_path / "t.db")


@pytest.fixture
def fakes(monkeypatch):
    """Fake crawler steps; `gate` holds the ticks step open, `calls` records them."""
    f = SimpleNamespace(gate=threading.Event(), calls=[], ticks_exc=None, now=TRADING,
                        ticks_status="complete", bars_status="complete")
    f.gate.set()

    def ticks(settings, d, only, *, today, on_progress):
        f.calls.append(("ticks", d))
        f.gate.wait(5)
        if f.ticks_exc:
            raise f.ticks_exc
        on_progress(12, 30)
        on_progress(30, 30)
        return _m(rows=4521, status=f.ticks_status)

    def bars(settings, d, *, today, count, on_progress):
        f.calls.append(("bars", count))
        on_progress(40, 40)
        return _m(rows=0, status=f.bars_status)

    monkeypatch.setattr(runner, "run_ticks", ticks)
    monkeypatch.setattr(runner, "run_bars_1d", bars)
    monkeypatch.setattr(runner, "_now", lambda: f.now)
    yield f
    f.gate.set()
    for _ in range(100):  # let a leftover thread release the process-wide lock
        if runner._lock.acquire(blocking=False):
            runner._lock.release()
            return
        time.sleep(0.05)


def _wait(c):
    for _ in range(100):
        j = c.get("/api/jobs/current").json()
        if j["status"] != "running":
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_run_and_lock(make_client, fakes):
    c = make_client()
    fakes.gate.clear()
    r = c.post("/api/jobs", json={"kind": "crawl"})
    assert r.status_code == 202 and r.json()["status"] == "running"
    assert r.json()["created_at"].endswith("+07:00")
    first = r.json()["id"]
    r = c.post("/api/jobs", json={"kind": "crawl"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "JOB_RUNNING"
    assert r.json()["error"]["details"]["id"] == first and r.json()["error"]["details"]["started_at"]
    fakes.gate.set()
    j = _wait(c)
    assert j["id"] == first and j["status"] == "done" and j["error"] is None and j["finished_at"]
    assert j["summary"]["ticks"]["rows"] == 4521 and j["summary"]["ticks"]["partial_until"] is None
    assert j["summary"]["bars_1d"]["sessions_added"] == 0 and j["summary"]["no_session_today"] is False
    assert j["progress"]["done"] == j["progress"]["total"] == 40
    assert c.get(f"/api/jobs/{first}").json() == j
    assert c.get("/api/jobs/999").status_code == 404


def test_partial_before_close(make_client, fakes):
    c = make_client()
    fakes.now = datetime(2026, 10, 26, 11, 0, tzinfo=VN)
    c.post("/api/jobs", json={"kind": "crawl"})
    assert _wait(c)["summary"]["ticks"]["partial_until"] == "2026-10-26T11:00:00+07:00"


def test_failure_releases_lock(make_client, fakes):
    c = make_client()
    path = "/app/data/raw/ticks/2026-10-26"
    fakes.ticks_exc = PermissionError(13, "Permission denied", path)
    c.post("/api/jobs", json={"kind": "crawl"})
    j = _wait(c)
    assert j["status"] == "failed" and j["summary"]["ticks"] is None
    assert j["error"] == {"code": "PermissionError", "message": str(fakes.ticks_exc), "path": path}
    fakes.ticks_exc = None
    assert c.post("/api/jobs", json={"kind": "crawl"}).status_code == 202
    assert _wait(c)["status"] == "done"


def test_blocked_bars_fails_job(make_client, fakes):
    c = make_client()
    fakes.bars_status = "blocked"
    c.post("/api/jobs", json={"kind": "crawl"})
    j = _wait(c)
    assert j["status"] == "failed" and j["error"]["code"] == "SourceBlocked" and j["error"]["source"] == "kbs"
    assert j["summary"]["ticks"]["rows"] == 4521


def test_blocked_ticks_skips_bars(make_client, fakes):
    c = make_client()
    fakes.ticks_status = "blocked"
    c.post("/api/jobs", json={"kind": "crawl"})
    j = _wait(c)
    assert j["status"] == "failed" and j["error"]["code"] == "SourceBlocked"
    assert j["summary"]["ticks"]["rows"] == 4521 and j["summary"]["bars_1d"] is None
    assert [k for k, _ in fakes.calls] == ["ticks"]


def test_stale_running_row_blocks(make_client, fakes):
    c = make_client()
    eng = c.app.dependency_overrides[get_engine]()
    with eng.begin() as cn:
        stale = cn.execute(insert(jobs).values(kind="crawl", args={}, status="running",
                                               created_at=datetime.now(UTC)).returning(jobs.c.id)).scalar_one()
    r = c.post("/api/jobs", json={"kind": "crawl"})
    assert r.status_code == 409 and r.json()["error"]["details"]["id"] == stale
    assert fakes.calls == [] and runner._lock.acquire(blocking=False)  # lock was released
    runner._lock.release()


def test_non_trading_day(make_client, fakes):
    c = make_client()
    fakes.now = SUNDAY
    c.post("/api/jobs", json={"kind": "crawl"})
    j = _wait(c)
    assert j["status"] == "done" and j["summary"]["ticks"] is None
    assert j["summary"]["no_session_today"] is True
    assert [k for k, _ in fakes.calls] == ["bars"]


def test_count_rule(make_client, fakes):
    c = make_client()  # seed: last bar 2026-10-16, index_1d empty (ignored)
    c.post("/api/jobs", json={"kind": "crawl"})
    _wait(c)
    assert ("bars", 8) in fakes.calls  # 10-19..10-23 + 10-26 = 6 sessions, +2


def test_count_empty_tables(make_client, fakes):
    c = make_client(seed=False)
    c.post("/api/jobs", json={"kind": "crawl"})
    _wait(c)
    assert ("bars", runner.COUNT) in fakes.calls


def test_sessions_added_counts_new_dates(make_client, fakes, monkeypatch):
    c = make_client()
    eng = c.app.dependency_overrides[get_engine]()
    bar = dict(symbol="FPT", trading_date=date(2026, 10, 26), source="vci", fetched_at=datetime.now(UTC),
               adj_o=1, adj_h=1, adj_l=1, adj_c=1, v=1)
    orig = runner.run_bars_1d

    def bars(*a, **kw):
        with eng.begin() as cn:
            cn.execute(insert(tables.bars_1d_src), [bar])
        return orig(*a, **kw)

    monkeypatch.setattr(runner, "run_bars_1d", bars)
    c.post("/api/jobs", json={"kind": "crawl"})
    assert _wait(c)["summary"]["bars_1d"]["sessions_added"] == 1


def test_bad_kind_and_empty_current(make_client):
    c = make_client()
    r = c.post("/api/jobs", json={"kind": "purge"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "VALIDATION"
    r = c.get("/api/jobs/current")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_startup_marks_interrupted(make_client):
    c = make_client()
    eng = c.app.dependency_overrides[get_engine]()
    with eng.begin() as cn:
        cn.execute(insert(jobs).values(kind="crawl", args={}, status="running", created_at=datetime.now(UTC)))
    with c:  # runs the lifespan
        pass
    with eng.connect() as cn:
        row = cn.execute(select(jobs)).one()
    assert row.status == "failed" and row.error["code"] == "interrupted" and row.finished_at
