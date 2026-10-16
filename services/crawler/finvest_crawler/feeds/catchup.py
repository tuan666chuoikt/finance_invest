"""Catch-up: run `ticks` for every trading day since the last recorded session (ADR-S-009, data.md 4)."""

import json
from datetime import datetime, time, timedelta
from types import ModuleType

from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.infrastructure import repositories
from finvest_rules.calendar import trading_days
from sqlalchemy import Connection

from finvest_crawler.feeds.ticks import FEED, run_ticks
from finvest_crawler.settings import Settings

CUTOFF = time(15, 5)  # VN close 15:00 + 5 min (VN section 2)


class CatchupFailed(RuntimeError):
    """Some day raised; the others still ran (`manifests` holds them)."""

    def __init__(self, manifests: list[Manifest], failed: list[str]):
        super().__init__(f"failed days: {', '.join(failed)}")
        self.manifests = manifests


def catchup(
    settings: Settings, *, now_vn: datetime, conn: Connection, repo: ModuleType = repositories, run=run_ticks  # noqa: ANN001
) -> list[Manifest]:
    today = now_vn.date()
    last = repo.last_session_date(conn, FEED)
    # no history => only today: never back-walk silently into the past
    start = last or today  # the last day counts too: it may be partial/blocked (ADR-S-009)
    end = today if now_vn.time() >= CUTOFF else today - timedelta(1)
    out: list[Manifest] = []
    failed: list[str] = []
    for d in trading_days(start, end):
        if repo.session_status(conn, FEED, d) in ("complete", "missed"):
            continue
        try:
            out.append(run(settings, d, None))
        except (Exception, SystemExit) as e:  # one bad day must not stop the rest
            print(json.dumps({"catchup_failed": str(d), "error": repr(e)}))
            failed.append(str(d))
    if failed:
        raise CatchupFailed(out, failed)
    return out
