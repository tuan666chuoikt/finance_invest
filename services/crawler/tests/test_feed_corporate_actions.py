"""corporate_actions press on a mocked V5 with an in-memory repo (no network, no db)."""

import json
from dataclasses import astuple
from datetime import date
from unittest.mock import MagicMock

import httpx
import pytest
from finvest_crawler.archive import Archive
from finvest_crawler.feeds.corporate_actions import run_corporate_actions
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings

RUN = date(2026, 10, 26)
SYMS = ("AAA", "BBB", "CCC")


def page(sym, ex="2026-11-05T00:00:00", *extra) -> bytes:
    ev = {"id": f"{sym}-1", "ticker": sym, "eventCode": "DIV", "eventTitleVi": "Cổ tức tiền mặt",
          "exrightDate": ex, "valuePerShare": 1000.0}
    return json.dumps({"status": 200, "data": {"content": [ev, *extra], "last": True}}).encode()


class FakeRepo:
    """The functions the feed calls; the diff log is the rule under test: one row per changed field."""

    def __init__(self):
        self.runs, self.events, self.log, self.anomalies, self.checked = [], {}, [], [], []

    def fail_unfinished_runs(self, conn, feed, d):
        return 0

    def insert_crawl_run(self, conn, feed, d, started):
        self.runs.append(None)
        return len(self.runs) - 1

    def finish_crawl_run(self, conn, id, status, reason, requests, rows, path):
        self.runs[id] = (status, reason, requests, rows)

    def ca_symbols_in_order(self, conn, limit=None):
        return list(SYMS)

    def corporate_actions_for(self, conn, syms):
        return {s: [e for e in self.events.values() if e.symbol == s] for s in syms}

    def upsert_corporate_actions(self, conn, rows, at):
        changes = 0
        for r in rows:
            old = self.events.get(r.source_event_id)
            for f, a, b in zip(r.__dataclass_fields__, astuple(old) if old else (), astuple(r), strict=False):
                if a != b:
                    self.log.append((r.source_event_id, f, a, b))
                    changes += 1
            self.events[r.source_event_id] = r
        return len(rows), changes

    def insert_anomaly(self, conn, symbol, d, rule, value):
        self.anomalies.append((symbol, d, rule, value))

    def mark_ca_checked(self, conn, syms, at):
        self.checked += syms


def press(tmp_path, repo, *, ex="2026-11-05T00:00:00", status=200, body=None, **kw):
    seen = []

    def handler(req):
        sym = req.url.params["ticker"]
        seen.append(sym)
        return httpx.Response(status, content=body if body is not None else page(sym, ex))

    f = Fetcher(httpx.Client(transport=httpx.MockTransport(handler)), {"vci_iq": TokenBucket(1000)},
                Archive(tmp_path), "ua", sleep=lambda s: None)
    r = run_corporate_actions(Settings(_env_file=None), RUN, fetcher=f, conn=MagicMock(), repo=repo, **kw)
    return r, seen


def test_budget_defers_the_rest(tmp_path):
    repo = FakeRepo()
    r, seen = press(tmp_path, repo, budget=2)
    assert (r.status, r.symbols_checked, r.symbols_deferred, r.requests) == ("partial", 1, 2, 1)
    assert seen == ["AAA"] and repo.checked == ["AAA"] and repo.runs == [("partial", None, 1, 1)]
    assert r.changed_symbols == ["AAA"]  # a new event counts as changed


def test_ex_date_change_is_logged_once(tmp_path):
    repo = FakeRepo()
    r1, _ = press(tmp_path / "1", repo)
    assert (r1.status, r1.symbols_checked, r1.events_upserted, r1.changes) == ("ok", 3, 3, 0)
    r2, _ = press(tmp_path / "2", repo, ex="2026-11-07T00:00:00")
    assert r2.changes == 3 and r2.changed_symbols == list(SYMS)
    assert repo.log[0] == ("AAA-1", "ex_date", date(2026, 11, 5), date(2026, 11, 7))
    r3, _ = press(tmp_path / "3", repo, ex="2026-11-07T00:00:00")
    assert r3.changes == 0 and r3.changed_symbols == [] and len(repo.log) == 3


def test_blocked_stops_without_further_requests(tmp_path):
    repo = FakeRepo()
    r, seen = press(tmp_path, repo, status=418)
    assert r.status == "blocked" and r.symbols_checked == 0 and r.symbols_deferred == 3
    assert seen == ["AAA"] * 3 and r.requests == 3  # 3 x 418 -> SourceBlocked, no BBB
    assert repo.runs == [("blocked", "source_blocked", 3, 0)]


def test_anomaly_is_logged_on_the_ex_date(tmp_path):
    repo = FakeRepo()
    bad = {"id": "AAA-2", "ticker": "AAA", "eventCode": "DIV", "eventTitleVi": "Cổ tức",
           "exrightDate": "2026-11-09T00:00:00"}
    press(tmp_path, repo, body=json.dumps({"data": {"content": [bad], "last": True}}).encode(), budget=2)
    assert repo.anomalies == [("AAA", date(2026, 11, 9), "corporate_action_amount_missing", "AAA-2")]


def test_failure_marks_the_run_failed(tmp_path):
    repo = FakeRepo()
    with pytest.raises(Exception):  # noqa: B017  # a body that is not a V5 page
        press(tmp_path, repo, body=b"{}")
    assert repo.runs[0][0] == "failed"
