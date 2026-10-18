"""Trading-day shifts for what-if dates (contracts/analytics.md §2.4, F-040 buy forward, F-041 sell back)."""

from datetime import date, timedelta

from ..domain.ports import MarketView

LOOKAROUND = timedelta(days=14)  # longer than any VN holiday run (Tet); beyond it the caller gets None


def shift_forward(d: date, calendar: list[date]) -> date | None:
    """First trading day >= d, None when `calendar` has none."""
    return next((c for c in sorted(calendar) if c >= d), None)


def shift_back(d: date, calendar: list[date]) -> date | None:
    """Last trading day <= d, None when `calendar` has none."""
    return next((c for c in sorted(calendar, reverse=True) if c <= d), None)


def record(shifts: list[dict], field: str, frm: date, to: date, reason: str = "non_trading") -> None:
    if frm != to:
        shifts.append({"field": field, "from": frm.isoformat(), "to": to.isoformat(), "reason": reason})


def resolve_sell(
    sell: date | None, symbol: str, floor: date, view: MarketView, shifts: list[dict]
) -> date | None:
    """Valuation date M: latest bar <= sell (sell None: last stored bar); never reads past the snapshot."""
    snap = view.snapshot().date()
    if sell is None:
        bars = view.bars_1d(symbol, floor, snap, as_of=snap)
        return max(b.trading_date for b in bars) if bars else None
    d = shift_back(sell, view.calendar(sell - LOOKAROUND, sell))
    if d is None:
        return None
    record(shifts, "sell_date", sell, d)
    bars = view.bars_1d(symbol, floor, d, as_of=d)
    if not bars:
        return None
    last = max(b.trading_date for b in bars)
    record(shifts, "sell_date", d, last, "no_bar")
    return last
