# ruff: noqa: E501
"""QA (fi-be-tester) black-box checks for sprint 02, written against the backlog / plan criteria, not the dev tests."""
import json
from datetime import date

import httpx
import pytest
from finvest_rules.calendar import CalendarNotMaintained, day, trading_days
from test_feed_ticks import run, serve

EMPTY = json.dumps({"data": []}).encode()


# ---- F-003 ------------------------------------------------------------------------------------
def test_f003_holiday_weekend_trading_with_names():
    h = day(date(2026, 9, 2))
    assert (h.is_open, h.kind) == (False, "holiday") and h.name
    assert (day(date(2026, 10, 17)).kind, day(date(2026, 10, 18)).kind) == ("weekend", "weekend")
    assert day(date(2026, 10, 14)).is_open  # nothing inferred from a missing row


def test_f003_sprint_week_has_five_trading_days_and_gap_reporting_basis():
    assert len(trading_days(date(2026, 10, 19), date(2026, 10, 23))) == 5
    sep = trading_days(date(2026, 8, 28), date(2026, 9, 4))  # 08-31, 09-01, 09-02 closed
    assert sep == [date(2026, 8, 28), date(2026, 9, 3), date(2026, 9, 4)]


@pytest.mark.parametrize("d", [date(2024, 12, 31), date(2027, 1, 4)])
def test_f003_unmaintained_year_raises_not_guesses(d):
    with pytest.raises(CalendarNotMaintained):
        day(d)


# ---- S02-1 ------------------------------------------------------------------------------------
def test_s02_1_session_of_only_no_trade_names_is_complete(tmp_path):
    m, _, repo = run(tmp_path, serve({"FPT": EMPTY, "VNM": EMPTY}))
    assert (m.status, m.reason, m.rows) == ("complete", None, 0)
    assert (m.symbols_fetched, m.symbols_no_trades, m.symbols_skipped) == (0, ("FPT", "VNM"), ())
    d = m.to_dict()
    assert d["symbols_no_trades"] == ["FPT", "VNM"] and d["symbols_skipped"] == []


def test_s02_1_no_trade_plus_real_skip_is_partial_and_skip_only_lists_real(tmp_path):
    m, _, _ = run(tmp_path, serve({"FPT": EMPTY, "VNM": lambda: httpx.Response(200, content=b'{"data": [{"t": "x"}]}')}))
    assert m.status == "partial" and m.symbols_no_trades == ("FPT",)
    assert [s for s, _ in m.symbols_skipped] == ["VNM"] and m.symbols_skipped[0][1] == "payload_shape"


def test_s02_1_past_date_empty_tape_is_still_missed(tmp_path):  # S02-3: 10-14 must stay `missed`
    m, _, _ = run(tmp_path, serve({"FPT": EMPTY, "VNM": EMPTY}), d=date(2026, 10, 14), today=date(2026, 10, 18))
    assert (m.status, m.reason) == ("missed", "source_no_longer_serves")
    assert m.symbols_no_trades == () and m.rows == 0
