from datetime import date

import pytest
from finvest_rules.calendar import CalendarNotMaintained, day, trading_days


def test_holiday_weekend_trading():
    assert day(date(2026, 9, 2)).kind == "holiday" and "Quốc khánh" in day(date(2026, 9, 2)).name
    assert day(date(2026, 8, 22)).is_open is False
    assert day(date(2026, 10, 16)).kind == "trading"
    assert day(date(2026, 10, 18)).kind == "weekend"
    assert day(date(2026, 1, 2)).kind == "trading"  # unverified press-only closure, not in contract (PR-002)


def test_trading_days_inclusive():
    assert trading_days(date(2026, 8, 28), date(2026, 9, 3)) == [date(2026, 8, 28), date(2026, 9, 3)]


def test_unmaintained_year_raises():
    for d in (date(2027, 1, 4), date(2024, 12, 31)):
        with pytest.raises(CalendarNotMaintained):
            day(d)
