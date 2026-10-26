"""Corporate-action adjustment factors (VN§6 v1.1, reference price VN§3): pure, imports nothing of ours.

Events of one ex-date combine in ONE formula (VN§6, source S7), r = b/a per event:
    P_adj = (P - c + sum(S*r_rights)) / (1 + r_stock + sum(r_rights));  factor = P_adj / P
A rights issue with S >= P is dropped (VN§3/§6: no adjustment).
split|merge a:b (a old -> b new) multiplies by a/b;
listing_change is 1. Factors are Decimal, 12 places half-up (ADR-S-005); P is integer VND.
Changing any formula here requires bumping RULES_VERSION (test_costs hashes this module).
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

_PLACES = Decimal(1).scaleb(-12)
_TYPES = {"cash_dividend", "stock_dividend", "rights", "split", "merge", "listing_change"}


class InvalidCorporateAction(ValueError):
    """Unusable event data; the caller records anomaly `adj_factor_invalid_input` with `reason`."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class CaEvent:
    type: str  # as data.md §3 corporate_actions.type
    ratio_a: int | None = None
    ratio_b: int | None = None
    cash_per_share: int | None = None
    issue_price: int | None = None


def _terms(events: list[CaEvent]) -> tuple[int, Decimal, list[tuple[int, Decimal]], Decimal]:
    """(cash, stock ratio r_s, [(S, r_rights)], split multiplier); validates fields, not P."""
    cash, r_s, rights, split = 0, Decimal(0), [], Decimal(1)
    for e in events:
        if e.type not in _TYPES:
            raise InvalidCorporateAction(f"unknown_type:{e.type}")
        if e.type == "cash_dividend":
            if e.cash_per_share is None or e.cash_per_share <= 0:
                raise InvalidCorporateAction("cash_missing_or_not_positive")
            cash += e.cash_per_share
        elif e.type != "listing_change":
            if e.ratio_a is None or e.ratio_b is None or e.ratio_a < 1 or e.ratio_b < 1:
                raise InvalidCorporateAction("ratio_missing_or_below_1")
            if e.type == "stock_dividend":
                r_s += Decimal(e.ratio_b) / e.ratio_a
            elif e.type == "rights":
                if e.issue_price is None or e.issue_price <= 0:
                    raise InvalidCorporateAction("issue_price_missing_or_not_positive")
                rights.append((e.issue_price, Decimal(e.ratio_b) / e.ratio_a))
            else:  # split | merge
                split *= Decimal(e.ratio_a) / e.ratio_b
    return cash, r_s, rights, split


def factor(events: list[CaEvent], pre_close: int) -> Decimal:
    """Combined factor of all events on one ex-date; `pre_close` = nominal close of the day before (VN§3)."""
    if pre_close <= 0:
        raise InvalidCorporateAction("pre_close_not_positive")
    cash, r_s, rights, split = _terms(events)
    if cash >= pre_close:
        raise InvalidCorporateAction("cash_not_below_pre_close")
    live = [(s, r) for s, r in rights if s < pre_close]  # S >= P: no adjustment (VN§3/§6)
    num = Decimal(pre_close - cash) + sum((s * r for s, r in live), Decimal(0))
    den = 1 + r_s + sum((r for _, r in live), Decimal(0))
    return (num / den / pre_close * split).quantize(_PLACES, ROUND_HALF_UP)


def pre_close_from_adjusted(adj_pre_close: Decimal, events: list[CaEvent]) -> int:
    """Invert the VN§6 formula (S7): nominal pre-ex close P from `adj_pre_close` = A(D-1)/G(D).

    The caller divides the source-adjusted close A by G = product of factors with LATER ex-dates, so this
    event's own factor is the only one left: P = A/G * (1 + r_s + r_r) - S*r_r + c. There is no circularity:
    G holds later events only, whose factors do not depend on this P. If a rights price S >= the P found,
    the forward rule applied no rights adjustment, so that term is dropped and P recomputed.
    Integer VND, half-up.
    shortcut: one recompute pass, exact for at most one rights event per ex-date (the only case seen), upgrade
    to a fixed-point loop if the crawler ever stores two rights with different S on one ex-date.
    """
    cash, r_s, rights, split = _terms(events)
    a = adj_pre_close / split

    def nominal(live: list[tuple[int, Decimal]]) -> Decimal:
        return (
            a * (1 + r_s + sum((r for _, r in live), Decimal(0)))
            - sum((s * r for s, r in live), Decimal(0))
            + cash
        )

    p = nominal(rights)
    p = nominal([(s, r) for s, r in rights if s < p])
    return int(p.quantize(Decimal(1), ROUND_HALF_UP))
