"""Lump-sum and monthly-DCA what-if on daily closes (analytics.md §1.2 steps 3-5, §1.3.1; contracts §2.4)."""

from decimal import Decimal

import finvest_rules

from ..domain.models import Ctx, WhatIfRequest
from ..domain.money import AnalyticsError, fee, lot_cost_min, max_qty, pct, round_half_up
from ..domain.ports import MarketView
from .dates import LOOKAROUND, record, resolve_sell, shift_forward
from .dca import schedule
from .figures import envelope, iso_vn, whatif_result


def _cagr(liquidation: int, invested: int, days: int) -> Decimal | None:
    if days < 1:
        return None
    # Decimal ** Decimal is exact for exponent 1 (365 days) and for 0.5 (730 days)
    return ((Decimal(liquidation) / Decimal(invested)) ** (Decimal(365) / Decimal(days)) - 1) * 100


def run_whatif(req: WhatIfRequest, view: MarketView, rules=finvest_rules.costs) -> dict:
    sym = req.symbol
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

    dca = req.style == "dca"
    shifts: list[dict] = []
    # DCA records every contribution shift (first one included) through schedule(); lump sum records here
    first_shifts = [] if dca else shifts
    n = shift_forward(req.buy_date, view.calendar(req.buy_date, req.buy_date + LOOKAROUND))
    if n is None:
        raise AnalyticsError("VALIDATION", {"reason": "no_trading_day_near_buy"})
    record(first_shifts, "buy_date", req.buy_date, n)
    # calendar day without a stored bar: move forward to the first bar (contracts §2.1), like the sell side
    n_bar = next((d for d in bar_days if d >= n), None)
    if n_bar is None:
        raise AnalyticsError("NO_DATA", {"last_available": last.isoformat()})
    record(first_shifts, "buy_date", n, n_bar, "no_bar")
    n = n_bar
    m = resolve_sell(req.sell_date, sym, n, view, shifts)
    if m is None:
        raise AnalyticsError("VALIDATION", {"reason": "sell_before_buy_after_shift"})

    if dca:
        fills = []
        for rq, t in schedule(req.buy_date, m, view.calendar(req.buy_date, m + LOOKAROUND), shifts):
            b = next((d for d in bar_days if d >= t), None)  # a trading day without a stored bar
            if b is None or b > m:
                shifts.append(
                    {"field": "contribution", "from": t.isoformat(), "to": None, "reason": "after_end"}
                )
            else:
                record(shifts, "contribution", t, b, "no_bar")
                fills.append((rq, b))
    else:
        fills = [(req.buy_date, n)]

    cs = rules(m)
    sell_rate = req.fee_rate if req.fee_rate is not None else cs.sell_fee_rate
    # decision time t_i = close of t_i: only data <= t_i is visible to contribution i (no look-ahead)
    rows, states, cash, shares, invested, min_amount = [], [], 0, 0, 0, None
    for rq, t in fills:
        c = rules(t)
        buy_rate = req.fee_rate if req.fee_rate is not None else c.buy_fee_rate
        px = view.bars_1d(sym, t, t, as_of=t)[0].c
        cash += req.amount_vnd
        qty = max_qty(cash, px, c.lot, buy_rate)
        fee_vnd = fee(qty, px, buy_rate)
        cash -= qty * px + fee_vnd
        shares, invested = shares + qty, invested + req.amount_vnd
        rows.append(
            {
                "date": t,
                "requested": rq,
                "amount_vnd": req.amount_vnd,
                "qty": qty,
                "price": px,
                "fee_vnd": fee_vnd,
                "cash_after": cash,
                "buy_fee_rate": buy_rate,
            }
        )
        states.append((cash, shares, invested))
        if qty == 0 and min_amount is None:
            min_amount = (lot_cost_min(px, c.lot, buy_rate), px, buy_rate)
    cb = rules(n)
    flags = {"fill_shifted"} if shifts else set()
    if min_amount:
        flags.add("below_one_lot")
    # shortcut: flags read the shipped RULES, not an injected `rules` callable; fine until a test needs both
    used = [("board_lot", t) for _, t in fills] + [("sell_tax_rate", m)]
    if req.fee_rate is None:
        used += [("buy_fee_rate", t) for _, t in fills] + [("sell_fee_rate", m)]
    flags |= {f"rules_unverified:{k}" for k, d in used if not finvest_rules.rule(k, d).verified}

    bars = view.bars_1d(sym, n, m, as_of=m)
    closes = {b.trading_date: b.c for b in bars}
    close_m = closes[m]
    market_value = shares * close_m
    sell_fee = fee(shares, close_m, sell_rate)
    sell_tax = round_half_up(Decimal(market_value) * cs.sell_tax_rate)
    liquidation = cash + market_value - sell_fee - sell_tax
    pl = liquidation - invested
    days = (m - n).days

    curve, missing, last_close, i = [], [], rows[0]["price"], -1
    for d in view.calendar(n, m):
        while i + 1 < len(rows) and rows[i + 1]["date"] <= d:
            i += 1
        if d in closes:
            last_close = closes[d]
        else:
            missing.append(d)
        c_, s_, inv_ = states[i]
        curve.append({"date": d.isoformat(), "market_value": c_ + s_ * last_close, "invested": inv_})
    if missing:
        flags.add("missing_sessions")

    ctx = Ctx(iso_vn(max(b.fetched_at for b in bars)), finvest_rules.RULES_VERSION)
    result = whatif_result(
        ctx=ctx,
        rows=rows,
        dca=dca,
        sell=m,
        shifts=shifts,
        close_sell=close_m,
        lot=cb.lot,
        sell_rate=sell_rate,
        tax_rate=cs.sell_tax_rate,
        qty=shares,
        cash=cash,
        market_value=market_value,
        sell_fee=sell_fee,
        sell_tax=sell_tax,
        liquidation=liquidation,
        pl=pl,
        pl_pct=pct(pl, invested),
        holding_days=days,
        cagr=None if dca else _cagr(liquidation, invested, days),
        min_amount=min_amount,
        missing=missing,
        curve=curve,
    )
    return envelope(req, ctx, view.price_basis(), flags, result)
