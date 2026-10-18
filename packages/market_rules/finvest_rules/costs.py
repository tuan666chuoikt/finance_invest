"""Trading-cost rules v1 (VN§4, VN§5): pure, versioned by `effective_from`, imports nothing of ours.

`effective_from` is the date we *apply* a rule from (2006-01-01, before the earliest daily bar,
data.md §1.2 V2), not the date the law started. Changing any value in RULES requires bumping RULES_VERSION.
"""

from bisect import bisect_right
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

RULES_VERSION = "2026.10.16"
_FROM = date(2006, 1, 1)


class RuleNotEffective(LookupError):
    def __init__(self, name: str, on: date):
        super().__init__(f"rule {name!r} has no entry effective on {on}")
        self.name, self.on = name, on


@dataclass(frozen=True)
class Rule:
    value: Decimal | int
    effective_from: date
    verified: bool
    verified_on: date | None
    source: str
    cite: str


@dataclass(frozen=True)
class Costs:
    buy_fee_rate: Decimal
    sell_fee_rate: Decimal
    sell_tax_rate: Decimal
    lot: int
    settlement_days: int


RULES: dict[str, list[Rule]] = {
    "buy_fee_rate": [Rule(Decimal("0.0015"), _FROM, False, None, "sponsor A6 default", "VN§5")],
    "sell_fee_rate": [Rule(Decimal("0.0015"), _FROM, False, None, "sponsor A6 default", "VN§5")],
    "sell_tax_rate": [
        Rule(
            Decimal("0.001"),
            _FROM,
            True,
            date(2026, 10, 15),
            "Law 109/2025/QH15, Decree 253/2026 (S4)",
            "VN§5",
        )
    ],
    "board_lot": [Rule(100, _FROM, True, date(2026, 10, 15), "S1, S2", "VN§4")],
    "settlement_days": [Rule(2, _FROM, True, date(2026, 10, 15), "S3 (T+2)", "VN§5")],
}


def rule(name: str, on: date, rules: dict[str, list[Rule]] | None = None) -> Rule:
    """Entry with the latest effective_from <= on. `rules` is for tests; default is RULES."""
    entries = sorted((RULES if rules is None else rules)[name], key=lambda r: r.effective_from)
    i = bisect_right([r.effective_from for r in entries], on)
    if i == 0:
        raise RuleNotEffective(name, on)
    return entries[i - 1]


def _rate(name: str, on: date, rules: dict[str, list[Rule]] | None) -> Decimal:
    v = rule(name, on, rules).value
    if not isinstance(v, Decimal):
        raise TypeError(f"rule {name!r} must be Decimal, got {type(v).__name__}")
    return v


def _count(name: str, on: date, rules: dict[str, list[Rule]] | None) -> int:
    v = rule(name, on, rules).value
    if not isinstance(v, int) or isinstance(v, bool):
        raise TypeError(f"rule {name!r} must be int, got {type(v).__name__}")
    return v


def costs(on: date, rules: dict[str, list[Rule]] | None = None) -> Costs:
    return Costs(
        _rate("buy_fee_rate", on, rules),
        _rate("sell_fee_rate", on, rules),
        _rate("sell_tax_rate", on, rules),
        _count("board_lot", on, rules),
        _count("settlement_days", on, rules),
    )
