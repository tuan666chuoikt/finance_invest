"""Unit conversion in one place (platform.md §1.2): money is integer VND, volume is integer shares."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal


def to_vnd(value: Decimal | int | str, unit: Literal["vnd", "thousand_vnd", "million_vnd"]) -> int:
    """Convert to integer VND, rounding half up to 1 VND. Floats are rejected: pass str or Decimal."""
    d = Decimal(value) * {"vnd": 1, "thousand_vnd": 1000, "million_vnd": 1_000_000}[unit]
    return int(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def to_shares(qty: int, lot_unit: int) -> int:
    return qty * lot_unit
