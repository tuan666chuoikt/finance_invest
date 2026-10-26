from decimal import Decimal as D

import pytest
from finvest_rules import CaEvent, InvalidCorporateAction, factor, pre_close_from_adjusted
from hypothesis import given
from hypothesis import strategies as st

CASH = CaEvent("cash_dividend", cash_per_share=1_000)
RIGHTS_LOW = CaEvent("rights", 10, 2, issue_price=10_000)  # S < P at 50,000
BONUS = CaEvent("stock_dividend", 10, 3)


def adj(f: D, p: int) -> D:
    return (f * p).quantize(D("0.01"))


def test_g1_cash():
    f = factor([CASH], 50_000)
    assert f == D("0.980000000000")
    assert adj(f, 50_000) == D("49000.00") and adj(f, 51_000) == D("49980.00")


def test_g2_bonus_independent_of_p():
    f = factor([BONUS], 93_500)
    assert f == D("0.769230769231") == factor([BONUS], 1_000)
    assert adj(f, 93_500) == D("71923.08")


def test_g3_rights_and_g3b_rights_at_or_above_pre_close():
    f = factor([RIGHTS_LOW], 50_000)  # (50,000*10 + 10,000*2) / (12 * 50,000)
    assert f == D("0.866666666667") and adj(f, 50_000) == D("43333.33")
    for s in (50_000, 60_000):
        f = factor([CaEvent("rights", 10, 2, issue_price=s)], 50_000)
        assert f == D("1.000000000000") and adj(f, 50_000) == D("50000.00")


def test_g4_cash_plus_rights_is_not_the_product():
    f = factor([CASH, RIGHTS_LOW], 50_000)  # (50,000 - 1,000 + 2,000) / 1.2 = 42,500
    assert f == D("0.850000000000") and adj(f, 50_000) == D("42500.00")
    assert f != factor([CASH], 50_000) * factor([RIGHTS_LOW], 50_000)  # 42,466.67


def test_g5_cash_plus_bonus_equals_product():
    f = factor([CASH, BONUS], 93_500)  # 92,500 / 1.3 = 71,153.85
    assert f == D("0.761003702180") and adj(f, 93_500) == D("71153.85")
    product = factor([CASH], 93_500) * factor([BONUS], 93_500)  # 0.989304812834 * 0.769230769231
    assert abs(f - product) < D("1e-11")


def test_split_merge_listing_change():
    assert factor([CaEvent("split", 1, 2)], 80_000) == D("0.5")
    assert factor([CaEvent("merge", 2, 1)], 80_000) == D("2")
    assert factor([CaEvent("listing_change")], 80_000) == D("1")
    assert factor([], 80_000) == D("1")


@pytest.mark.parametrize(
    "events,p,reason",
    [
        ([CaEvent("cash_dividend", cash_per_share=50_000)], 50_000, "cash_not_below_pre_close"),
        ([CaEvent("cash_dividend", cash_per_share=60_000)], 50_000, "cash_not_below_pre_close"),
        ([CASH, CASH], 2_000, "cash_not_below_pre_close"),  # cash sums within one ex-date
        ([CaEvent("cash_dividend")], 50_000, "cash_missing_or_not_positive"),
        ([CaEvent("stock_dividend", 0, 3)], 50_000, "ratio_missing_or_below_1"),
        ([CaEvent("stock_dividend", 10, None)], 50_000, "ratio_missing_or_below_1"),
        ([CaEvent("rights", 10, 2)], 50_000, "issue_price_missing_or_not_positive"),
        ([CaEvent("merger")], 50_000, "unknown_type:merger"),
        ([CASH], 0, "pre_close_not_positive"),
    ],
)
def test_invalid_inputs(events, p, reason):
    with pytest.raises(InvalidCorporateAction) as ei:
        factor(events, p)
    assert ei.value.reason == reason


def test_g7_inversion_cash():
    assert pre_close_from_adjusted(D(49_000), [CASH]) == 50_000


def test_g7b_inversion_cash_plus_rights():
    assert pre_close_from_adjusted(D(42_500), [CASH, RIGHTS_LOW]) == 50_000  # 42,500*1.2 - 2,000 + 1,000


def test_inversion_rights_at_or_above_pre_close_branch():
    # forward: S 50,000 >= P 50,000 -> f = 1, adj = 50,000; naive inversion: 50,000*1.2 - 100,000 < 0
    assert pre_close_from_adjusted(D(50_000), [CaEvent("rights", 10, 2, issue_price=50_000)]) == 50_000


def test_inversion_validates_fields():
    with pytest.raises(InvalidCorporateAction):
        pre_close_from_adjusted(D(1), [CaEvent("rights", 10, 2)])


@st.composite
def ex_date(draw):
    p = draw(st.integers(1_000, 500_000))
    ev = []
    if draw(st.booleans()):
        ev.append(CaEvent("cash_dividend", cash_per_share=draw(st.integers(1, max(1, p // 2)))))
    if draw(st.booleans()):
        ev.append(CaEvent("stock_dividend", draw(st.integers(1, 20)), draw(st.integers(1, 20))))
    if draw(st.booleans()):
        ev.append(
            CaEvent(
                "rights",
                draw(st.integers(1, 20)),
                draw(st.integers(1, 20)),
                issue_price=draw(st.integers(1, 2 * p)),
            )
        )
    if draw(st.booleans()):
        ev.append(CaEvent("split", draw(st.integers(1, 5)), draw(st.integers(1, 5))))
    return ev, p


@given(ex_date())
def test_round_trip_to_one_vnd(case):
    events, p = case
    assert pre_close_from_adjusted(D(p) * factor(events, p), events) == p
