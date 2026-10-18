"""In-memory MarketView for tests. bars_1d/index_1d enforce as_of (the look-ahead guard)."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .domain.models import DailyBar, IndexBar


@dataclass
class FixtureView:
    bars: dict[str, list[DailyBar]]
    index: dict[str, list[IndexBar]]
    snapshot_at: datetime
    basis: str = "source_adjusted"

    def calendar(self, start: date, end: date) -> list[date]:
        days = (end - start).days + 1
        return [d for d in (start + timedelta(i) for i in range(max(days, 0))) if d.weekday() < 5]

    def bars_1d(self, symbol: str, start: date, end: date, *, as_of: date) -> list[DailyBar]:
        return [b for b in self.bars.get(symbol, []) if start <= b.trading_date <= min(end, as_of)]

    def first_bar_date(self, symbol: str) -> date | None:
        return min((b.trading_date for b in self.bars.get(symbol, [])), default=None)

    def index_1d(self, code: str, start: date, end: date, *, as_of: date) -> list[IndexBar]:
        return [b for b in self.index.get(code, []) if start <= b.trading_date <= min(end, as_of)]

    def snapshot(self) -> datetime:
        return self.snapshot_at

    def price_basis(self) -> str:
        return self.basis


def constant_series(
    symbol: str,
    start: date,
    end: date,
    close: int,
    *,
    last_close: int | None = None,
    fetched_at: datetime | None = None,
) -> list[DailyBar]:
    """Weekday bars at a flat close; the final bar may differ via last_close."""
    fetched_at = fetched_at or datetime(2026, 10, 15, 15, 30)
    days = FixtureView({}, {}, fetched_at).calendar(start, end)
    return [
        DailyBar(symbol, d, close, close, close, close, 1000, "source_adjusted", fetched_at)
        for d in days[:-1]
    ] + [
        DailyBar(symbol, d, c, c, c, c, 1000, "source_adjusted", fetched_at)
        for d in days[-1:]
        for c in [last_close if last_close is not None else close]
    ]
