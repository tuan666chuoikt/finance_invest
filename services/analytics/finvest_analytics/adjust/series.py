"""Adjusted series and nominal reconstruction (tech plan sprint-05 R1, R4-R6; VN§3, VN§6 v1.1).

Pure functions over sorted lists, no I/O. Factors come from `finvest_rules.factor`; this module only
chains them. Nothing here reads a bar dated after `as_of` or applies an ex-date after it (R5).
"""

from collections import defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from finvest_rules import CaEvent, factor, pre_close_from_adjusted

from ..domain.models import AdjBar, CorporateAction, Factor, NominalBar

_F_PLACES = Decimal(1).scaleb(-12)
_PX_PLACES = Decimal("0.01")


def round_vnd(x: Decimal) -> int:
    return int(x.quantize(Decimal(1), ROUND_HALF_UP))


RECONSTRUCTED_HOW = "giá danh nghĩa tái dựng, sai số ± 1 bước giá"  # A18-A: stated, not hidden


def events_by_ex_date(actions: list[CorporateAction]) -> dict[date, list[CaEvent]]:
    out: dict[date, list[CaEvent]] = defaultdict(list)
    for a in actions:
        out[a.ex_date].append(a.event)
    return dict(out)


def cumulative(factors: list[Factor], d: date, upto: date) -> Decimal:
    """G(d) = product of f over ex-dates e with d < e <= upto, on the stored 12-place rows (R4, R5)."""
    g = Decimal(1)
    for x in factors:
        if d < x.ex_date <= upto:
            g *= x.f
    return g.quantize(_F_PLACES, ROUND_HALF_UP)


def forward_factors(symbol: str, bars: list[NominalBar], events: dict[date, list[CaEvent]]) -> list[Factor]:
    """One factor per ex-date from P = nominal close of the latest bar before it (R1).

    An ex-date with no earlier bar gets no factor (it adjusts nothing); the SQL side records the anomaly.
    """
    out = []
    for d in sorted(events):
        prior = [b for b in bars if b.trading_date < d]
        if prior:
            out.append(Factor(symbol, d, factor(events[d], prior[-1].c)))
    return out


def adjusted(nominal_bars: list[NominalBar], factors: list[Factor], as_of: date) -> list[AdjBar]:
    """adj(d) = nominal(d) x G(d), 2 dp half-up, over bars and ex-dates <= as_of (R5)."""
    return [
        AdjBar(
            b.symbol,
            b.trading_date,
            (b.c * cumulative(factors, b.trading_date, as_of)).quantize(_PX_PLACES, ROUND_HALF_UP),
        )
        for b in sorted(nominal_bars, key=lambda b: b.trading_date)
        if b.trading_date <= as_of
    ]


def reconstruct(
    src_bars: list[AdjBar], events: dict[date, list[CaEvent]], observed: dict[date, int]
) -> tuple[list[NominalBar], list[Factor]]:
    """R6: walk backwards from the newest source version; `observed` maps date -> observed nominal close.

    Events dated after the last source bar are not applied (the source could not know them); one dated at
    or before the first bar adjusts nothing. P of an ex-date is the observed close of the day before when
    we have one, else the VN§6 inversion of the source's A(D-1). Observed dates are never emitted.
    """
    src = sorted(src_bars, key=lambda b: b.trading_date)
    if not src:
        return [], []
    sym, first, last = src[0].symbol, src[0].trading_date, src[-1].trading_date
    factors: list[Factor] = []
    for d in sorted((e for e in events if first < e <= last), reverse=True):
        prev = [b for b in src if b.trading_date < d][-1]
        # P is observed only if the latest source bar before D is; else invert (source has every trading day)
        if prev.trading_date in observed:
            p = observed[prev.trading_date]
        else:
            p = pre_close_from_adjusted(prev.c / cumulative(factors, d, last), events[d])
        factors.append(Factor(sym, d, factor(events[d], p)))
    factors.sort(key=lambda x: x.ex_date)
    nominal = [
        NominalBar(
            sym, b.trading_date, round_vnd(b.c / cumulative(factors, b.trading_date, last)), "reconstructed"
        )
        for b in src
        if b.trading_date not in observed
    ]
    return nominal, factors
