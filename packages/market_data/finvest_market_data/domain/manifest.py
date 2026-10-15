"""Tick canonical rows, checksum, dedupe and the session manifest (platform.md §4, ADR-S-008)."""

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from finvest_market_data.domain.models import Tick

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def canonical_line(tick: Tick) -> str:
    ts = tick.ts.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    return f"{tick.symbol},{ts},{tick.seq},{tick.price},{tick.volume},{tick.side or ''}"


def checksum(ticks: Iterable[Tick]) -> str:
    lines = sorted(canonical_line(t).encode() + b"\n" for t in ticks)
    return "sha256:" + hashlib.sha256(b"".join(lines)).hexdigest()


def dedupe(ticks: Iterable[Tick]) -> tuple[list[Tick], list[Tick]]:
    """Keep the last row per (symbol, ts, seq); return (kept, displaced)."""
    kept: dict[tuple[str, datetime, int], Tick] = {}
    displaced: list[Tick] = []
    for t in ticks:
        old = kept.get(k := (t.symbol, t.ts, t.seq))
        if old is not None:
            displaced.append(old)
        kept[k] = t
    return list(kept.values()), displaced


def _vn_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("manifest timestamps must be tz-aware")
    return dt.astimezone(VN).isoformat(timespec="seconds")


@dataclass(frozen=True, slots=True)
class Manifest:
    feed: str
    trading_date: date
    source: str
    started_at: datetime
    finished_at: datetime
    status: str  # complete | partial | missed | blocked | failed
    reason: str | None
    requests: int
    rows: int
    checksum: str
    symbols_fetched: int
    symbols_skipped: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (symbol, reason)
    universe_source: str = ""
    universe_as_of: datetime | None = None
    universe_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "feed": self.feed,
            "trading_date": self.trading_date.isoformat(),
            "source": self.source,
            "started_at": _vn_iso(self.started_at),
            "finished_at": _vn_iso(self.finished_at),
            "status": self.status,
            "reason": self.reason,
            "requests": self.requests,
            "rows": self.rows,
            "checksum": self.checksum,
            "symbols_fetched": self.symbols_fetched,
            "symbols_skipped": [{"symbol": s, "reason": r} for s, r in self.symbols_skipped],
            "universe": {
                "source": self.universe_source,
                "as_of": _vn_iso(self.universe_as_of) if self.universe_as_of else None,
                "count": self.universe_count,
            },
        }
