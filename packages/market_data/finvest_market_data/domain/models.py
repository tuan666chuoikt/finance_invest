"""Market-data value objects. Prices are integer VND (ADR-S-005), `ts` is UTC-aware (ADR-S-006)."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal


def _require_utc(ts: datetime) -> None:
    if ts.tzinfo is None or ts.utcoffset() != UTC.utcoffset(None):
        raise ValueError(f"ts must be UTC-aware, got {ts!r}")


@dataclass(frozen=True, slots=True)
class Tick:
    symbol: str
    ts: datetime
    seq: int
    price: int
    volume: int
    side: Literal["B", "S"] | None
    source: str

    def __post_init__(self) -> None:
        _require_utc(self.ts)
        if self.price <= 0:
            raise ValueError(f"price must be > 0, got {self.price}")
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got {self.volume}")


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: str
    ts: datetime
    o: int
    h: int
    l: int  # noqa: E741 - OHLC convention
    c: int
    v: int
    value: int | None
    source: str

    def __post_init__(self) -> None:
        _require_utc(self.ts)
        if min(self.o, self.h, self.l, self.c) <= 0:
            raise ValueError("bar prices must be > 0")
        if self.v < 0:
            raise ValueError(f"volume must be >= 0, got {self.v}")


@dataclass(frozen=True, slots=True)
class SymbolRecord:
    symbol: str
    exchange: Literal["HOSE", "HNX", "UPCOM"]
    type: Literal["STOCK", "ETF"]
    name_vi: str
    name_en: str
    icb_code2: str | None
    is_delisted: bool
    source: str
