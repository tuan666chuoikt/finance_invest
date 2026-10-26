"""In-memory MarketView for tests. bars_1d/index_1d enforce as_of (the look-ahead guard)."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .adjust.series import adjusted, events_by_ex_date, forward_factors
from .domain.models import AdjBar, CorporateAction, DailyBar, IndexBar, NominalBar


@dataclass
class FixtureView:
    bars: dict[str, list[DailyBar]]
    index: dict[str, list[IndexBar]]
    snapshot_at: datetime
    basis: str = "source_adjusted"
    actions: dict[str, list[CorporateAction]] = field(default_factory=dict)
    _served: list[datetime] = field(default_factory=list, init=False, repr=False)  # CA fetched_at served

    def calendar(self, start: date, end: date) -> list[date]:
        days = (end - start).days + 1
        return [d for d in (start + timedelta(i) for i in range(max(days, 0))) if d.weekday() < 5]

    def bars_1d(self, symbol: str, start: date, end: date, *, as_of: date) -> list[DailyBar]:
        return [b for b in self.bars.get(symbol, []) if start <= b.trading_date <= min(end, as_of)]

    def first_bar_date(self, symbol: str) -> date | None:
        return min((b.trading_date for b in self.bars.get(symbol, [])), default=None)

    def index_1d(self, code: str, start: date, end: date, *, as_of: date) -> list[IndexBar]:
        return [b for b in self.index.get(code, []) if start <= b.trading_date <= min(end, as_of)]

    def corporate_actions(self, symbol: str, start: date, end: date, *, as_of: date) -> list[CorporateAction]:
        rows = [a for a in self.actions.get(symbol, []) if start <= a.ex_date <= min(end, as_of)]
        self._served.extend(a.fetched_at for a in rows)
        return rows

    def adjusted_close(self, symbol: str, start: date, end: date, *, as_of: date) -> list[AdjBar]:
        """Fixture bars are nominal observed closes; factors derive from CA rows with ex_date <= as_of."""
        nominal = [NominalBar(b.symbol, b.trading_date, b.c, "observed")
                   for b in self.bars_1d(symbol, date.min, as_of, as_of=as_of)]
        applied = self.corporate_actions(symbol, date.min, as_of, as_of=as_of)
        rows = adjusted(nominal, forward_factors(symbol, nominal, events_by_ex_date(applied)), as_of)
        return [r for r in rows if start <= r.trading_date <= end]

    def snapshot(self) -> datetime:
        return max([self.snapshot_at, *self._served])  # served rows only, like SqlMarketView (R9)

    def price_basis(self) -> str:
        return self.basis


def constant_series(symbol: str, start: date, end: date, close: int, *, last_close: int | None = None,
                    fetched_at: datetime | None = None) -> list[DailyBar]:
    """Weekday bars at a flat close; the final bar may differ via last_close."""
    fetched_at = fetched_at or datetime(2026, 10, 15, 15, 30)
    days = FixtureView({}, {}, fetched_at).calendar(start, end)
    return [DailyBar(symbol, d, close, close, close, close, 1000,
                     "source_adjusted", fetched_at) for d in days[:-1]] + [
        DailyBar(symbol, d, c, c, c, c, 1000, "source_adjusted", fetched_at)
        for d in days[-1:] for c in [last_close if last_close is not None else close]]
