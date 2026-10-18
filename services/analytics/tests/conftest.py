from datetime import date, datetime

import pytest
from finvest_analytics.fixtures import FixtureView, constant_series


@pytest.fixture
def view():
    bars = constant_series("FPT", date(2026, 1, 1), date(2026, 3, 31), 93_500)
    return FixtureView({"FPT": bars}, {}, datetime(2026, 10, 15, 15, 30))
