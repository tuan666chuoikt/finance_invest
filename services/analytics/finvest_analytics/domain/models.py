"""Domain types (contracts/analytics.md §1.1, §1.4, §2.4)."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class DailyBar:
    symbol: str
    trading_date: date
    o: int
    h: int
    l: int  # noqa: E741
    c: int
    v: int
    price_basis: str
    fetched_at: datetime


@dataclass(frozen=True)
class IndexBar:
    index_code: str
    trading_date: date
    c: Decimal


@dataclass(frozen=True)
class How:
    formula: str
    inputs: dict[str, str]
    as_of: str
    rules_version: str
    cite: str | None = None


@dataclass(frozen=True)
class Figure:
    value: str
    unit: str  # vnd | pct | ratio | shares | days
    how: How


@dataclass(frozen=True)
class Ctx:
    as_of: str
    rules_version: str


class WhatIfRequest(BaseModel):
    symbol: str
    amount_vnd: int = Field(ge=1)
    buy_date: date
    sell_date: date | None = None
    style: Literal["lump_sum", "dca"] = "lump_sum"
    fill_rule: Literal["close"] = "close"
    fee_rate: Decimal | None = None


def _s(v: object) -> str:
    if isinstance(v, Decimal):
        return str(v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    return str(v)


def figure(value, unit: str, formula: str, inputs: dict, ctx: Ctx, cite: str | None = None) -> Figure:
    """Ints become plain strings, Decimals 4 dp half-up."""
    return Figure(
        _s(value),
        unit,
        How(formula, {k: _s(v) for k, v in inputs.items()}, ctx.as_of, ctx.rules_version, cite),
    )
