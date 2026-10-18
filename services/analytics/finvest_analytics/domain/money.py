"""Integer-VND helpers: lot, fee and rounding formulas (contracts/analytics.md §2.4)."""
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal


class AnalyticsError(Exception):
    CODES = ("SYMBOL_UNKNOWN", "NO_DATA", "VALIDATION", "RANGE_TOO_LARGE")

    def __init__(self, code: str, details: dict | None = None):
        assert code in self.CODES, code
        super().__init__(code)
        self.code = code
        self.details = details or {}


def round_half_up(x: Decimal) -> int:
    return int(x.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def fee(qty: int, price: int, rate: Decimal) -> int:
    return round_half_up(Decimal(qty * price) * Decimal(rate))


def max_qty(cash: int, price: int, lot: int, rate: Decimal) -> int:
    """Largest whole-lot qty with qty*price + fee <= cash."""
    rate = Decimal(rate)
    q = int((Decimal(cash) / (price * lot * (1 + rate))).to_integral_value(ROUND_FLOOR)) * lot
    # the floor formula uses the exact fee; the booked fee is rounded, so fix up by whole lots
    while q > 0 and q * price + fee(q, price, rate) > cash:
        q -= lot
    while (q + lot) * price + fee(q + lot, price, rate) <= cash:
        q += lot
    return q


def lot_cost_min(price: int, lot: int, rate: Decimal) -> int:
    return int((price * lot * (1 + Decimal(rate))).to_integral_value(ROUND_CEILING))


def pct(num: int | Decimal, den: int | Decimal) -> Decimal:
    if den == 0:
        raise ZeroDivisionError("pct denominator is 0")
    return (Decimal(num) / Decimal(den) * 100).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
