"""SqlMarketView: analytics `MarketView` port over the market-data tables (contracts/analytics.md §1.4)."""
from datetime import UTC, date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from finvest_analytics.adjust.series import adjusted, cumulative, round_vnd
from finvest_analytics.domain.models import AdjBar, CorporateAction, DailyBar, Factor, IndexBar, NominalBar
from finvest_market_data.infrastructure.tables import (
    adj_factors,
    bars_1d,
    bars_1d_src,
    corporate_actions,
    index_1d,
)
from finvest_rules import CaEvent
from finvest_rules.calendar import CalendarNotMaintained, trading_days
from sqlalchemy import func, select, union_all
from sqlalchemy.engine import Engine

_BASIS = "source_adjusted"
_CENT = Decimal("0.01")


def _today() -> date:
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()


class SqlMarketView:
    """One instance per request: `snapshot()` covers the bar rows this instance has served."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._served: datetime | None = None

    def _serve(self, *stamps: datetime) -> None:
        """R9: `snapshot()` = max fetched_at over everything this view served or applied."""
        self._served = max([s for s in (self._served, *stamps) if s is not None], default=None)

    def _factors(self, symbol: str, as_of: date) -> list[Factor]:
        t = adj_factors
        q = select(t.c.ex_date, t.c.factor).where(t.c.symbol == symbol, t.c.ex_date <= as_of)
        return [Factor(symbol, d, Decimal(str(f))) for d, f in self._rows(q)]

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
        """Source-adjusted basis (R7 `ours`): `bars_1d` nominal x factors over (d, today].

        shortcut: a symbol with no `reconstructed` row (V5 not reached, platform.md §2.6) falls back to the
        newest `bars_1d_src` rows, symbol-level never per date; drop when V5 coverage is full (S06).
        """
        o, hi = bars_1d, min(end, as_of)
        rec = select(o.c.symbol).where(o.c.symbol == symbol, o.c.nominal_kind == "reconstructed").limit(1)
        bars: list[DailyBar] = []
        if not self._rows(rec):
            t = bars_1d_src
            q = (select(t.c.trading_date, t.c.adj_o, t.c.adj_h, t.c.adj_l, t.c.adj_c, t.c.v, t.c.fetched_at)
                 .where(t.c.symbol == symbol, t.c.trading_date.between(start, hi))
                 .distinct(t.c.trading_date)  # Postgres DISTINCT ON: newest fetched_at per day
                 .order_by(t.c.trading_date, t.c.fetched_at.desc()))
            bars = [DailyBar(symbol, *r[:6], _BASIS, r[6]) for r in self._rows(q)]
        seen = {b.trading_date for b in bars}
        q = (select(o.c.trading_date, o.c.o, o.c.h, o.c.l, o.c.c, o.c.v, o.c.fetched_at)
             .where(o.c.symbol == symbol, o.c.trading_date.between(start, hi))
             .order_by(o.c.trading_date))
        rows = [r for r in self._rows(q) if r[0] not in seen]
        if rows:
            # nominal x factors over (d, today]
            today = _today()
            fs = self._factors(symbol, today)
            self.corporate_actions(symbol, rows[0][0], today, as_of=today)  # rows applied move the snapshot
            for r in rows:
                g = cumulative(fs, r[0], today)
                bars.append(DailyBar(symbol, r[0], *(round_vnd(x * g) for x in map(Decimal, r[1:5])), r[5],
                                     _BASIS, r[6]))
            bars.sort(key=lambda b: b.trading_date)
        if bars:
            self._serve(max(b.fetched_at for b in bars))
        return bars

    def corporate_actions(self, symbol: str, start: date, end: date, *, as_of: date) -> list[CorporateAction]:
        """Rows with a stored factor, ex_date in [start, min(end, as_of)]; they count as applied (R9, G11)."""
        c, f = corporate_actions, adj_factors
        q = (select(c.c.ex_date, c.c.type, c.c.ratio_a, c.c.ratio_b, c.c.cash_per_share, c.c.issue_price,
                    c.c.fetched_at)
             .join(f, (f.c.symbol == c.c.symbol) & (f.c.ex_date == c.c.ex_date))
             .where(c.c.symbol == symbol, c.c.ex_date.between(start, min(end, as_of)))
             .order_by(c.c.ex_date, c.c.id))
        out = [CorporateAction(symbol, r[0], CaEvent(*r[1:6]), r[6]) for r in self._rows(q)]
        self._serve(*(a.fetched_at for a in out))
        return out

    def adjusted_close(self, symbol: str, start: date, end: date, *, as_of: date) -> list[AdjBar]:
        """Our adjusted series (R5): nominal bars_1d x stored factors over (d, as_of]."""
        o = bars_1d
        q = (select(o.c.trading_date, o.c.c, o.c.nominal_kind, o.c.fetched_at)
             .where(o.c.symbol == symbol, o.c.trading_date.between(start, min(end, as_of))))
        rows = self._rows(q)
        if not rows:
            return []
        self.corporate_actions(symbol, date.min, as_of, as_of=as_of)
        self._serve(max(r[3] for r in rows))
        nominal = [NominalBar(symbol, d, c, k) for d, c, k, _ in rows]
        return adjusted(nominal, self._factors(symbol, as_of), as_of)

    def first_bar_date(self, symbol: str) -> date | None:
        days = union_all(*(select(t.c.trading_date).where(t.c.symbol == symbol)
                           for t in (bars_1d_src, bars_1d)))
        return self._rows(select(func.min(days.subquery().c.trading_date)))[0][0]

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
