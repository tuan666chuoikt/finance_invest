from datetime import date

import httpx
import pytest
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.ratelimit import TokenBucket

D = date(2026, 10, 16)
URL = "https://kbbuddywts.kbsec.com.vn/x"
UA = "test-ua"


class Clock:
    def __init__(self):
        self.t, self.sleeps = 0.0, []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def make(tmp_path, responses, rate=2.0):
    """responses: list of (status, body) served in order; returns fetcher, clock, seen requests."""
    clock, seen, it = Clock(), [], iter(responses)

    def handler(req):
        seen.append(req)
        s, body = next(it)
        return httpx.Response(s, content=body)

    buckets = {k: TokenBucket(rate, clock=clock.now, sleep=clock.sleep) for k in ("kbs", "vci")}
    f = Fetcher(httpx.Client(transport=httpx.MockTransport(handler)), buckets, Archive(tmp_path), UA,
                sleep=lambda s: clock.sleeps.append(("backoff", s)))
    return f, clock, seen


def get(f, name="a"):
    return f.get("kbs", URL, feed="ticks", trading_date=D, name=name)


def test_three_429_blocked(tmp_path):
    f, clock, seen = make(tmp_path, [(429, b"")] * 3)
    with pytest.raises(SourceBlocked) as e:
        get(f)
    assert e.value.last_status == 429 and len(seen) == 3
    assert [s for k, s in (x for x in clock.sleeps if isinstance(x, tuple))] == [1, 2]


def test_reset_after_success(tmp_path):
    f, _, seen = make(tmp_path, [(429, b""), (429, b""), (200, b"{}")])
    assert get(f) == b"{}" and len(seen) == 3


def test_cloudflare_challenge_is_blocked(tmp_path):
    f, _, _ = make(tmp_path, [(200, b"<!DOCTYPE html>Just a moment...")] * 3)
    with pytest.raises(SourceBlocked):
        get(f)


def test_5xx_gives_up_with_http_error(tmp_path):
    f, _, seen = make(tmp_path, [(503, b"")] * 3)
    with pytest.raises(httpx.HTTPError):
        get(f)
    assert len(seen) == 3


def test_rate_limit_per_source(tmp_path):
    f, clock, _ = make(tmp_path, [(200, b"{}")] * 6)
    for i in range(5):
        get(f, f"n{i}")
    assert sum(clock.sleeps) >= 2.0
    before = clock.t
    f.get("vci", "https://trading.vietcap.com.vn/x", feed="ticks", trading_date=D, name="v")
    assert clock.t == before


def test_archive_is_cache_and_exact(tmp_path):
    body = b'{"a":  1}\n'
    f, _, seen = make(tmp_path, [(200, body)])
    assert get(f) == body and get(f) == body
    assert len(seen) == 1 and (f.requests, f.replays) == (1, 1)
    assert Archive(tmp_path).read("ticks", D, "a") == body


def test_user_agent_and_allowlist(tmp_path):
    f, _, seen = make(tmp_path, [(200, b"{}")])
    get(f)
    assert seen[0].headers["User-Agent"] == UA
    with pytest.raises(ValueError):
        f.get("kbs", "https://evil.example.com/x", feed="ticks", trading_date=D, name="z")
    assert len(seen) == 1
