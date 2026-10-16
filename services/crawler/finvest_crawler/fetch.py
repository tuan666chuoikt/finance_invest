import time
from collections.abc import Callable
from datetime import date
from urllib.parse import urlparse

import httpx

from finvest_crawler.archive import Archive
from finvest_crawler.ratelimit import TokenBucket

ALLOWED_HOSTS = {
    "kbbuddywts.kbsec.com.vn", "trading.vietcap.com.vn", "iboard-api.ssi.com.vn",
    "iboard-query.ssi.com.vn", "iq.vietcap.com.vn",
}
TRIES = 3  # consecutive blocked responses -> SourceBlocked; also max tries on 5xx/timeout


class SourceBlocked(Exception):
    def __init__(self, source: str, last_status: int):
        super().__init__(f"{source} blocked (last status {last_status})")
        self.source, self.last_status = source, last_status


def _blocked(r: httpx.Response) -> bool:
    return r.status_code in (429, 403) or (
        r.status_code == 200 and (r.content.lstrip().startswith(b"<") or b"Just a moment" in r.content))


class Fetcher:
    def __init__(self, client: httpx.Client, buckets: dict[str, TokenBucket], archive: Archive,
                 user_agent: str, sleep: Callable[[float], None] = time.sleep):
        self.client, self.buckets, self.archive = client, buckets, archive
        self.user_agent, self.sleep = user_agent, sleep
        self.requests = 0
        self.replays = 0

    def get(self, source: str, url: str, *, feed: str, trading_date: date, name: str,
            method: str = "GET", json: object = None, archive: bool = True) -> bytes:
        if urlparse(url).hostname not in ALLOWED_HOSTS:
            raise ValueError(f"host not allowed: {url}")
        hit = self.archive.read(feed, trading_date, name)
        if hit is not None:
            self.replays += 1
            return hit
        blocked = failed = 0
        while True:
            self.buckets[source].take()
            self.requests += 1
            try:
                r = self.client.request(method, url, json=json, timeout=20,
                                        headers={"User-Agent": self.user_agent})
                if _blocked(r):
                    blocked, failed, status = blocked + 1, 0, r.status_code
                elif r.status_code >= 500:
                    blocked, failed, status = 0, failed + 1, r.status_code
                else:
                    r.raise_for_status()
                    if archive:  # archive=False: caller stores only after it accepted the payload
                        self.archive.write(feed, trading_date, name, r.content)
                    return r.content
            except httpx.TimeoutException:
                blocked, failed, status = 0, failed + 1, 0
            if blocked >= TRIES:
                raise SourceBlocked(source, status)
            if failed >= TRIES:
                raise httpx.HTTPError(f"{source} failed after {TRIES} tries (last status {status})")
            self.sleep(2 ** (max(blocked, failed) - 1))
