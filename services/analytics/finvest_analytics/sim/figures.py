"""Figures and the result envelope (contracts/analytics.md §1.1, §1.4, §2.4); formatting only."""

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from ..domain.models import Ctx, WhatIfRequest, figure

VN_TZ = timezone(timedelta(hours=7))


def iso_vn(t: datetime) -> str:
    """Naive timestamps are taken as Asia/Ho_Chi_Minh (the crawler stores local times)."""
    return (t.replace(tzinfo=VN_TZ) if t.tzinfo is None else t.astimezone(VN_TZ)).isoformat()


def fig(value, unit: str, formula: str, inputs: dict, ctx: Ctx, cite: str | None = None) -> dict:
    return asdict(figure(value, unit, formula, inputs, ctx, cite))


def lump_sum_result(
    *,
    ctx: Ctx,
    amount: int,
    buy: date,
    sell: date,
    requested: date,
    shifts: list[dict],
    close_buy: int,
    close_sell: int,
    lot: int,
    buy_rate: Decimal,
    sell_rate: Decimal,
    tax_rate: Decimal,
    qty: int,
    fee_vnd: int,
    cash: int,
    market_value: int,
    sell_fee: int,
    sell_tax: int,
    liquidation: int,
    pl: int,
    pl_pct: Decimal,
    holding_days: int,
    cagr: Decimal | None,
    min_amount: int | None,
    missing: list[date],
    curve: list[dict],
) -> dict:
    """Assemble `result` for a lump-sum what-if from already-computed numbers."""
    f = lambda *a, **k: fig(*a, ctx=ctx, **k)  # noqa: E731
    buy_how = {
        "formula": "round_half_up(qty * price * buy_fee_rate)",
        "cite": "VN§5",
        "inputs": {"qty": str(qty), "price": str(close_buy), "buy_fee_rate": str(buy_rate)},
        "as_of": ctx.as_of,
        "rules_version": ctx.rules_version,
    }
    returns = {
        "pl_vnd": f(pl, "vnd", "liquidation - invested", {"liquidation": liquidation, "invested": amount}),
        "pl_pct": f(pl_pct, "pct", "pl / invested * 100", {"pl": pl, "invested": amount}),
        "holding_days": f(
            holding_days,
            "days",
            "sell_date - buy_date",
            {"sell_date": sell.isoformat(), "buy_date": buy.isoformat()},
        ),
    }
    if cagr is not None:
        returns["cagr_pct"] = f(
            cagr,
            "pct",
            "((liquidation / invested) ^ (365 / holding_days) - 1) * 100",
            {"liquidation": liquidation, "invested": amount, "holding_days": holding_days},
        )
    else:
        returns["cagr_pct"] = None
        returns["cagr_note"] = {
            "text": "holding_days is 0, CAGR is undefined",
            "how": {
                "formula": "cagr_pct is null when holding_days < 1",
                "inputs": {"holding_days": str(holding_days)},
                "as_of": ctx.as_of,
                "rules_version": ctx.rules_version,
                "cite": None,
            },
        }
    result = {
        "dates": {"buy": buy.isoformat(), "sell": sell.isoformat(), "shifts": shifts},
        # shortcut: plain ints per the contract, one row-level `how` instead of Figure leaves
        "contributions": [
            {
                "date": buy.isoformat(),
                "requested": requested.isoformat(),
                "amount_vnd": amount,
                "qty": qty,
                "price": close_buy,
                "fee_vnd": fee_vnd,
                "cash_after": cash,
                "how": buy_how,
            }
        ],
        "position": {
            "shares": f(
                qty,
                "shares",
                "floor(amount / (close * lot * (1 + buy_fee_rate))) * lot",
                {"amount": amount, "close": close_buy, "lot": lot, "buy_fee_rate": buy_rate},
                cite="VN§4",
            ),
            "cash": f(
                cash,
                "vnd",
                "amount - shares * close - buy_fee",
                {"amount": amount, "shares": qty, "close": close_buy, "buy_fee": fee_vnd},
                cite="VN§5",
            ),
            "invested_vnd": f(amount, "vnd", "amount", {"amount": amount}),
        },
        "value": {
            "market_value_vnd": f(
                market_value, "vnd", "shares * close_sell", {"shares": qty, "close_sell": close_sell}
            ),
            "sell_fee_vnd": f(
                sell_fee,
                "vnd",
                "round_half_up(market_value * sell_fee_rate)",
                {"market_value": market_value, "sell_fee_rate": sell_rate},
                cite="VN§5",
            ),
            "sell_tax_vnd": f(
                sell_tax,
                "vnd",
                "round_half_up(market_value * sell_tax_rate)",
                {"market_value": market_value, "sell_tax_rate": tax_rate},
                cite="VN§5",
            ),
            "liquidation_vnd": f(
                liquidation,
                "vnd",
                "cash + market_value - sell_fee - sell_tax",
                {"cash": cash, "market_value": market_value, "sell_fee": sell_fee, "sell_tax": sell_tax},
                cite="VN§5",
            ),
        },
        "returns": returns,
        "benchmarks": [],
        "missing_sessions": [d.isoformat() for d in missing],
        "equity_curve": curve,
    }
    if min_amount is not None:
        result["details"] = {
            "min_amount": f(
                min_amount,
                "vnd",
                "ceil(lot * price * (1 + buy_fee_rate))",
                {"lot": lot, "price": close_buy, "buy_fee_rate": buy_rate},
                cite="VN§4",
            )
        }
    return result


def envelope(req: WhatIfRequest, ctx: Ctx, basis: str, flags: set[str], result: dict) -> dict:
    approximate = basis != "nominal"
    if approximate:
        flags = flags | {"approximate"}
    return {
        "params": req.model_dump(mode="json"),
        "data_snapshot": ctx.as_of,
        "rules_version": ctx.rules_version,
        "price_basis": basis,
        "approximate": approximate,
        "flags": sorted(flags),
        "disclaimer": "educational",
        "result": result,
    }
