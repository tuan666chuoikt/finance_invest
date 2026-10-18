"""SqlMarketView: analytics `MarketView` port over the market-data tables (contracts/analytics.md §1.4)."""
from datetime import UTC, date, datetime
from decimal import Decimal

from finvest_analytics.domain.models import DailyBar, IndexBar
from finvest_market_data.infrastructure.tables import bars_1d_src, index_1d
from finvest_rules.calendar import CalendarNotMaintained, trading_days
from sqlalchemy import func, select
from sqlalchemy.engine import Engine

_BASIS = "source_adjusted"
_CENT = Decimal("0.01")


class SqlMarketView:
    """One instance per request: `snapshot()` covers the bar rows this instance has served."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._served: datetime | None = None

    def _rows(self, stmt):
        with self._engine.connect() as c:
            return c.execute(stmt).all()

    def calendar(self, start: date, end: date) -> list[date]:
        out: list[date] = []
        for y in range(start.year, end.year + 1):
            lo, hi = max(start, date(y, 1, 1)), min(end, date(y, 12, 31))
            try:
                out += trading_days(lo, hi)
            except CalendarNotMaintained:
                # shortcut: years outside holidays.csv use VNINDEX dates as sessions (data.md §1.2 V2),
                # drop when holidays.csv covers 2006+
                q = select(index_1d.c.trading_date).where(
                    index_1d.c.index_code == "VNINDEX", index_1d.c.trading_date.between(lo, hi))
                out += [r[0] for r in self._rows(q)]
        return sorted(set(out))

    def bars_1d(self, symbol: str, start: date, end: date, *, as_of: date) -> list[DailyBar]:
        t = bars_1d_src
        q = (select(t.c.trading_date, t.c.adj_o, t.c.adj_h, t.c.adj_l, t.c.adj_c, t.c.v, t.c.fetched_at)
             .where(t.c.symbol == symbol, t.c.trading_date.between(start, min(end, as_of)))
             .distinct(t.c.trading_date)  # Postgres DISTINCT ON: newest fetched_at per day
             .order_by(t.c.trading_date, t.c.fetched_at.desc()))
        bars = [DailyBar(symbol, *r[:6], _BASIS, r[6]) for r in self._rows(q)]
        if bars:
            newest = max(b.fetched_at for b in bars)
            self._served = newest if self._served is None else max(self._served, newest)
        return bars

    def first_bar_date(self, symbol: str) -> date | None:
        q = select(func.min(bars_1d_src.c.trading_date)).where(bars_1d_src.c.symbol == symbol)
        return self._rows(q)[0][0]

    def index_1d(self, code: str, start: date, end: date, *, as_of: date) -> list[IndexBar]:
        t = index_1d
        q = (select(t.c.trading_date, t.c.c)
             .where(t.c.index_code == code, t.c.trading_date.between(start, min(end, as_of)))
             .order_by(t.c.trading_date))
        return [IndexBar(code, d, Decimal(c).quantize(_CENT)) for d, c in self._rows(q)]

    def snapshot(self) -> datetime:
        return self._served or datetime.min.replace(tzinfo=UTC)

    def price_basis(self) -> str:
        return _BASIS
