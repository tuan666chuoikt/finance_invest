from datetime import date, datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from finvest_crawler.feeds.catchup import CatchupFailed, catchup

VN = ZoneInfo("Asia/Ho_Chi_Minh")


class Repo:
    def __init__(self, last, status=None):
        # like a real repo: the last day has a row (complete unless the test says otherwise)
        self.last, self.status = last, {last: "complete", **(status or {})}

    def last_session_date(self, conn, feed):
        return self.last

    def session_status(self, conn, feed, d):
        return self.status.get(d)


def _go(repo, now, run=None):
    ran = []

    def default(s, d, only):
        ran.append(d)
        return SimpleNamespace(status="complete")

    out = catchup(None, now_vn=now, conn=None, repo=repo, run=run(ran) if run else default)
    return ran, out


def test_runs_only_trading_days_after_cutoff():
    # 08-29/30 weekend, 08-31 and 09-01 holidays, 09-02 holiday (VN calendar)
    ran, _ = _go(Repo(date(2026, 8, 27)), datetime(2026, 9, 3, 15, 30, tzinfo=VN))
    assert ran == [date(2026, 8, 28), date(2026, 9, 3)]


def test_before_cutoff_skips_today():
    ran, _ = _go(Repo(date(2026, 8, 27)), datetime(2026, 9, 3, 9, 0, tzinfo=VN))
    assert ran == [date(2026, 8, 28)]


def test_no_history_only_today():
    ran, _ = _go(Repo(None), datetime(2026, 10, 16, 15, 30, tzinfo=VN))
    assert ran == [date(2026, 10, 16)]


def test_complete_and_missed_skipped_others_run():
    st = {date(2026, 10, 12): "complete", date(2026, 10, 13): "missed", date(2026, 10, 15): "partial"}
    ran, _ = _go(Repo(date(2026, 10, 15), st), datetime(2026, 10, 16, 20, 0, tzinfo=VN))
    assert ran == [date(2026, 10, 15), date(2026, 10, 16)]


def test_raising_day_logged_others_still_run():
    ran = []

    def run(s, d, only):
        ran.append(d)
        if d == date(2026, 10, 14):
            raise SystemExit(1)
        return SimpleNamespace(status="complete")

    with pytest.raises(CatchupFailed) as e:
        catchup(None, now_vn=datetime(2026, 10, 16, 20, 0, tzinfo=VN), conn=None,
                repo=Repo(date(2026, 10, 13)), run=run)
    assert ran == [date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)]
    assert len(e.value.manifests) == 2


def test_last_day_blocked_is_retried_at_20h():
    st = {date(2026, 10, 16): "blocked"}
    ran, _ = _go(Repo(date(2026, 10, 16), st), datetime(2026, 10, 16, 20, 0, tzinfo=VN))
    assert ran == [date(2026, 10, 16)]


def test_last_day_complete_runs_nothing():
    st = {date(2026, 10, 16): "complete"}
    ran, _ = _go(Repo(date(2026, 10, 16), st), datetime(2026, 10, 16, 20, 0, tzinfo=VN))
    assert ran == []


def test_morning_after_replay_runs_a_past_day():
    # run_ticks takes its probe path whenever trading_date < today (5-review.tech section 2)
    now = datetime(2026, 10, 16, 9, 0, tzinfo=VN)
    ran, _ = _go(Repo(date(2026, 10, 14)), now)
    assert ran and all(d < now.date() for d in ran)
