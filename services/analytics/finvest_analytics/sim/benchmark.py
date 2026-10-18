"""Benchmarks beside a what-if (F-048, PR-034; contracts/analytics.md §2.4): VN-Index and E1VFVN30."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal

from ..domain.models import Ctx, WhatIfRequest
from ..domain.money import AnalyticsError, pct, round_half_up
from ..domain.ports import MarketView
from .figures import fig

ETF = "E1VFVN30"
INDEX = "VNINDEX"


def _na(name: str, investable: bool, first: date | None) -> dict:
    # never a zero: the card shows "n/a since <first>" instead (backlog F-048 criterion 4)
    return {
        "name": name,
        "investable": investable,
        "available": False,
        "first_available": first.isoformat() if first else None,
    }


def _ok(
    name: str,
    investable: bool,
    value: int,
    bench_pl_pct: Decimal,
    invested: int,
    scenario_pl_pct: Decimal,
    how_inputs: dict,
    formula: str,
    ctx: Ctx,
) -> dict:
    inv = "true" if investable else "false"
    f = lambda v, u, fm, i: fig(v, u, fm, {**i, "investable": inv}, ctx, "PR-034")  # noqa: E731
    return {
        "name": name,
        "investable": investable,
        "available": True,
        "value_vnd": f(value, "vnd", formula, how_inputs),
        "pl_pct": f(
            bench_pl_pct, "pct", "(value - invested) / invested * 100", {"value": value, "invested": invested}
        ),
        "diff_pp": f(
            scenario_pl_pct - bench_pl_pct,
            "pct",
            "scenario_pl_pct - benchmark_pl_pct (percentage points)",
            {"scenario_pl_pct": scenario_pl_pct, "benchmark_pl_pct": bench_pl_pct},
        ),
    }


def vnindex(
    contributions: list[tuple[date, int]], sell: date, scenario_pl_pct: Decimal, ctx: Ctx, view: MarketView
) -> dict:
    """value = round_half_up(sum(amount_i * idx(sell) / idx(date_i))); fractional units, no fees."""

    def at(d: date) -> Decimal | None:  # decision time d: only bars <= d are visible
        bars = view.index_1d(INDEX, d, d, as_of=d)
        return bars[0].c if bars and bars[0].c > 0 else None

    idx = [(a, at(d)) for d, a in contributions]
    close = at(sell)
    if close is None or any(i is None for _, i in idx):
        snap = view.snapshot().date()
        bars = view.index_1d(INDEX, date.min, snap, as_of=snap)
        return _na("VN-Index", False, min((b.trading_date for b in bars), default=None))
    invested = sum(a for a, _ in idx)
    value = round_half_up(sum((Decimal(a) * close / i for a, i in idx), Decimal(0)))  # type: ignore[operator]
    return _ok(
        "VN-Index",
        False,
        value,
        pct(value - invested, invested),
        invested,
        scenario_pl_pct,
        {
            "amount_i": ",".join(str(a) for a, _ in idx),
            "index_i": ",".join(str(i) for _, i in idx),
            "index_sell": close,
        },
        "round_half_up(sum(amount_i * index_sell / index_i))",
        ctx,
    )


def etf(
    req: WhatIfRequest,
    sell: date,
    dates: list[date],
    scenario_pl_pct: Decimal,
    ctx: Ctx,
    view: MarketView,
    run: Callable[..., dict],
) -> dict:
    """The same request through the engine on E1VFVN30 (benchmarks off, no recursion). Any gap vs the
    scenario's dates (own shifts, other sell day, NO_DATA) is n/a, not a shifted or zero result."""
    try:
        r = run(req.model_copy(update={"symbol": ETF, "sell_date": sell}), view, with_benchmarks=False)[
            "result"
        ]
    except AnalyticsError:
        r = None
    if (
        r is None
        or r["dates"]["sell"] != sell.isoformat()
        or [c["date"] for c in r["contributions"]] != [d.isoformat() for d in dates]
    ):
        return _na(ETF, True, view.first_bar_date(ETF))
    liq, invested = r["value"]["liquidation_vnd"], r["position"]["invested_vnd"]["value"]
    return _ok(
        ETF,
        True,
        int(liq["value"]),
        Decimal(r["returns"]["pl_pct"]["value"]),
        int(invested),
        scenario_pl_pct,
        {"etf_liquidation": liq["value"], "etf_invested": invested},
        "E1VFVN30 what-if liquidation_vnd",
        ctx,
    )
