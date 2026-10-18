"""Lump-sum what-if on daily closes (analytics.md §1.2 steps 3-5, §1.3.1; contracts/analytics.md §2.4)."""

from decimal import Decimal

import finvest_rules

from ..domain.models import Ctx, WhatIfRequest
from ..domain.money import AnalyticsError, fee, lot_cost_min, max_qty, pct, round_half_up
from ..domain.ports import MarketView
from .dates import LOOKAROUND, record, resolve_sell, shift_forward
from .figures import envelope, iso_vn, lump_sum_result


def _cagr(liquidation: int, invested: int, days: int) -> Decimal | None:
    if days < 1:
        return None
    # Decimal ** Decimal is exact for exponent 1 (365 days) and for 0.5 (730 days)
    return ((Decimal(liquidation) / Decimal(invested)) ** (Decimal(365) / Decimal(days)) - 1) * 100


def run_whatif(req: WhatIfRequest, view: MarketView, rules=finvest_rules.costs) -> dict:
    sym = req.symbol
    if req.style != "lump_sum":
        raise AnalyticsError("VALIDATION", {"reason": "style_not_supported", "style": req.style})
    if req.fill_rule != "close":
        raise AnalyticsError("VALIDATION", {"reason": "fill_rule_not_supported", "fill_rule": req.fill_rule})
    if req.sell_date is not None and req.sell_date < req.buy_date:
        raise AnalyticsError("VALIDATION", {"reason": "sell_before_buy"})
    first = view.first_bar_date(sym)
    if first is None:
        raise AnalyticsError("SYMBOL_UNKNOWN", {"symbol": sym})
    if req.buy_date < first:
        raise AnalyticsError("NO_DATA", {"first_available": first.isoformat()})
    snap = view.snapshot().date()
    # validation only: this history read never feeds a number
    bar_days = sorted(b.trading_date for b in view.bars_1d(sym, first, snap, as_of=snap))
    last = bar_days[-1]
    if req.buy_date > last:
        raise AnalyticsError(
            "VALIDATION", {"reason": "buy_after_last_bar", "last_available": last.isoformat()}
        )

    shifts: list[dict] = []
    n = shift_forward(req.buy_date, view.calendar(req.buy_date, req.buy_date + LOOKAROUND))
    if n is None:
        raise AnalyticsError("VALIDATION", {"reason": "no_trading_day_near_buy"})
    record(shifts, "buy_date", req.buy_date, n)
    # calendar day without a stored bar: move forward to the first bar (contracts §2.1), like the sell side
    n_bar = next((d for d in bar_days if d >= n), None)
    if n_bar is None:
        raise AnalyticsError("NO_DATA", {"last_available": last.isoformat()})
    record(shifts, "buy_date", n, n_bar, "no_bar")
    n = n_bar
    # decision time N: only data <= N is visible to the buy (no look-ahead)
    buy_bars = view.bars_1d(sym, n, n, as_of=n)
    m = resolve_sell(req.sell_date, sym, n, view, shifts)
    if m is None:
        raise AnalyticsError("VALIDATION", {"reason": "sell_before_buy_after_shift"})

    cb, cs = rules(n), rules(m)
    buy_rate = req.fee_rate if req.fee_rate is not None else cb.buy_fee_rate
    sell_rate = req.fee_rate if req.fee_rate is not None else cs.sell_fee_rate
    amount, close_n = req.amount_vnd, buy_bars[0].c
    qty = max_qty(amount, close_n, cb.lot, buy_rate)
    fee_vnd = fee(qty, close_n, buy_rate)
    cash = amount - qty * close_n - fee_vnd
    flags = {"fill_shifted"} if shifts else set()
    min_amount = None
    if qty == 0:
        flags.add("below_one_lot")
        min_amount = lot_cost_min(close_n, cb.lot, buy_rate)

    bars = view.bars_1d(sym, n, m, as_of=m)
    closes = {b.trading_date: b.c for b in bars}
    close_m = closes[m]
    market_value = qty * close_m
    sell_fee = fee(qty, close_m, sell_rate)
    sell_tax = round_half_up(Decimal(market_value) * cs.sell_tax_rate)
    liquidation = cash + market_value - sell_fee - sell_tax
    pl = liquidation - amount
    days = (m - n).days

    curve, missing, last_close = [], [], close_n
    for d in view.calendar(n, m):
        if d in closes:
            last_close = closes[d]
        else:
            missing.append(d)
        curve.append({"date": d.isoformat(), "market_value": cash + qty * last_close, "invested": amount})
    if missing:
        flags.add("missing_sessions")

    ctx = Ctx(iso_vn(max(b.fetched_at for b in bars)), finvest_rules.RULES_VERSION)
    result = lump_sum_result(
        ctx=ctx,
        amount=amount,
        buy=n,
        sell=m,
        requested=req.buy_date,
        shifts=shifts,
        close_buy=close_n,
        close_sell=close_m,
        lot=cb.lot,
        buy_rate=buy_rate,
        sell_rate=sell_rate,
        tax_rate=cs.sell_tax_rate,
        qty=qty,
        fee_vnd=fee_vnd,
        cash=cash,
        market_value=market_value,
        sell_fee=sell_fee,
        sell_tax=sell_tax,
        liquidation=liquidation,
        pl=pl,
        pl_pct=pct(pl, amount),
        holding_days=days,
        cagr=_cagr(liquidation, amount, days),
        min_amount=min_amount,
        missing=missing,
        curve=curve,
    )
    return envelope(req, ctx, view.price_basis(), flags, result)
