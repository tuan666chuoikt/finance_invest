"""Independent oracle for F-015 (tester, sprint-05). Exact Fractions, written from the plan's golden table
(2-tech-plan.ai.md G1-G13b) and VN§6, NOT from the implementation. Compares to finvest_rules / finvest_analytics."""
import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction as F

import pytest
from finvest_analytics.adjust.series import cumulative, forward_factors, reconstruct, adjusted
from finvest_analytics.domain.models import AdjBar, Factor, NominalBar
from finvest_rules import CaEvent, InvalidCorporateAction, factor, pre_close_from_adjusted


def q12(x: F) -> Decimal:
    n = x.numerator * 10**12
    d = x.denominator
    return Decimal((2 * n + d) // (2 * d)).scaleb(-12)  # half-up for positive x


def oracle(events, P):
    """P_adj = (P - c + sum(S r_rights)) / (1 + r_stock + sum r_rights); split a:b multiplies a/b."""
    c = sum(e.cash_per_share or 0 for e in events if e.type == "cash_dividend")
    rs = sum((F(e.ratio_b, e.ratio_a) for e in events if e.type == "stock_dividend"), F(0))
    rights = [(e.issue_price, F(e.ratio_b, e.ratio_a)) for e in events if e.type == "rights" and e.issue_price < P]
    split = F(1)
    for e in events:
        if e.type in ("split", "merge"):
            split *= F(e.ratio_a, e.ratio_b)
    num = F(P - c) + sum((s * r for s, r in rights), F(0))
    den = 1 + rs + sum((r for _, r in rights), F(0))
    return num / den / P * split


CASH = CaEvent("cash_dividend", cash_per_share=1000)
BONUS = CaEvent("stock_dividend", 10, 3)
RIGHTS = CaEvent("rights", 10, 2, issue_price=10000)

GOLD = [  # id, events, P, expected f (from the plan table, typed by hand)
    ("G1", [CASH], 50000, "0.980000000000"),
    ("G2", [BONUS], 93500, "0.769230769231"),
    ("G3", [RIGHTS], 50000, "0.866666666667"),
    ("G3b", [CaEvent("rights", 10, 2, issue_price=50000)], 50000, "1.000000000000"),
    ("G4", [CASH, RIGHTS], 50000, "0.850000000000"),
]


def test_gold_table_factors():
    for name, ev, P, exp in GOLD:
        assert factor(ev, P) == Decimal(exp) == q12(oracle(ev, P)), name
    f5 = factor([CASH, BONUS], 93500)
    assert f5 == q12(oracle([CASH, BONUS], 93500))
    assert (Decimal(93500) * f5).quantize(Decimal("0.01"), ROUND_HALF_UP) == Decimal("71153.85")  # plan G5
    # plan cross-check: product 0.989304812834 x 0.769230769231 x 93,500 (approx equal)
    assert abs(Decimal("0.989304812834") * Decimal("0.769230769231") * 93500 - Decimal("71153.85")) < Decimal("0.01")


def test_G2_G3_G4_prices():
    assert (93500 * factor([BONUS], 93500)).quantize(Decimal("0.01"), ROUND_HALF_UP) == Decimal("71923.08")
    assert (50000 * factor([RIGHTS], 50000)).quantize(Decimal("0.01"), ROUND_HALF_UP) == Decimal("43333.33")
    assert (50000 * factor([CASH, RIGHTS], 50000)).quantize(Decimal("0.01"), ROUND_HALF_UP) == Decimal("42500.00")
    assert 50000 * factor([CASH, RIGHTS], 50000) != Decimal("42466.67")  # not the product of separate factors


def test_G1_G6_series():
    d = date
    nom = [NominalBar("X", d(2026, 10, 1), 51000, "observed"), NominalBar("X", d(2026, 10, 2), 50000, "observed"),
           NominalBar("X", d(2026, 10, 3), 49000, "observed")]
    f = [Factor("X", d(2026, 10, 2), Decimal("0.98"))]
    adj = {b.trading_date: b.c for b in adjusted(nom[:2], f, d(2026, 10, 2))}
    assert adj[d(2026, 10, 1)] == Decimal("49980.00")
    # G6: two ex-dates; nominal 51,000 before D1 -> 51,000 x 0.98 x 10/13
    f2 = [Factor("X", d(2026, 10, 2), Decimal("0.98")), Factor("X", d(2026, 10, 3), Decimal("0.769230769231"))]
    want = (F(51000) * F(98, 100) * F(10, 13))
    got = adjusted([nom[0]], f2, d(2026, 10, 3))[0].c
    assert abs(Decimal(want.numerator) / Decimal(want.denominator) - got) < Decimal("0.01")  # 38,446.15
    assert got == Decimal("38446.15")
    assert adjusted([nom[0]], f2, d(2026, 10, 2))[0].c == Decimal("49980.00")  # as_of between D1 and D2
    # no look-ahead: bar after as_of absent
    assert [b.trading_date for b in adjusted(nom, f2, d(2026, 10, 2))] == [d(2026, 10, 1), d(2026, 10, 2)]


def test_invalid_inputs():
    with pytest.raises(InvalidCorporateAction):
        factor([CaEvent("cash_dividend", cash_per_share=50000)], 50000)
    with pytest.raises(InvalidCorporateAction):
        factor([CASH], 0)
    with pytest.raises(InvalidCorporateAction):
        factor([CaEvent("stock_dividend", 0, 3)], 50000)
    with pytest.raises(InvalidCorporateAction):
        factor([CaEvent("rights", 10, 2)], 50000)


def test_random_factor_vs_oracle():
    rnd = random.Random(20261026)
    for _ in range(3000):
        P = rnd.randrange(1000, 400000, 100)
        ev = []
        if rnd.random() < .4:
            ev.append(CaEvent("cash_dividend", cash_per_share=rnd.randrange(100, max(200, P // 2), 100)))
        if rnd.random() < .3:
            ev.append(CaEvent("stock_dividend", rnd.randrange(1, 100), rnd.randrange(1, 40)))
        if rnd.random() < .3:
            ev.append(CaEvent("rights", rnd.randrange(1, 50), rnd.randrange(1, 30), issue_price=rnd.randrange(1000, 450000, 100)))
        if rnd.random() < .1:
            ev.append(CaEvent(rnd.choice(["split", "merge"]), rnd.randrange(1, 10), rnd.randrange(1, 10)))
        if not ev:
            continue
        assert factor(ev, P) == q12(oracle(ev, P)), (ev, P)


def test_inversion_roundtrip_random():
    rnd = random.Random(7)
    n = 0
    for _ in range(3000):
        P = rnd.randrange(5000, 300000, 100)
        ev = [CaEvent("cash_dividend", cash_per_share=rnd.randrange(100, P // 3, 100))] if rnd.random() < .5 else []
        if rnd.random() < .5:
            ev.append(CaEvent("stock_dividend", rnd.randrange(1, 100), rnd.randrange(1, 40)))
        if rnd.random() < .3:
            ev.append(CaEvent("rights", rnd.randrange(1, 20), rnd.randrange(1, 10), issue_price=rnd.randrange(1000, P - 100, 100)))
        if not ev:
            continue
        f = factor(ev, P)
        A = (Decimal(P) * f).quantize(Decimal("0.01"), ROUND_HALF_UP)  # source stores 2dp
        back = pre_close_from_adjusted(A, ev)
        assert abs(back - P) <= 1 + int(P * 1e-9) + 1, (ev, P, back)  # rounding of A to 0.01 / f to 12dp
        n += 1
    assert n > 1500


def src(rows, last=None):
    return [AdjBar("X", date.fromisoformat(k), Decimal(v), date.fromisoformat(last[k]) if last else None) for k, v in rows.items()]


def test_G7_G7b():
    ev = {date(2026, 10, 2): [CASH]}
    nom, fs = reconstruct(src({"2026-10-01": "49000", "2026-10-02": "49000"}), ev, {})
    assert fs[0].f == Decimal("0.980000000000") and nom[0].c == 50000 and nom[0].nominal_kind == "reconstructed"
    ev2 = {date(2026, 10, 2): [CASH, RIGHTS]}
    nom, fs = reconstruct(src({"2026-10-01": "42500", "2026-10-02": "42500"}), ev2, {})
    assert nom[0].c == 42500 * 12 // 10 - 2000 + 1000 == 50000
    assert fs[0].f == Decimal("0.850000000000")


def test_G9_observed_not_emitted():
    ev = {date(2026, 10, 2): [CASH]}
    nom, fs = reconstruct(src({"2026-10-01": "49000", "2026-10-02": "49000"}), ev, {date(2026, 10, 1): 50000})
    assert all(b.trading_date != date(2026, 10, 1) for b in nom)
    assert fs[0].f == Decimal("0.980000000000")


def test_G13_versions():
    days = [date(2026, 10, 1) + timedelta(i) for i in range(12)]
    rows, last = {}, {}
    for i, d in enumerate(days):
        if i < 7:
            rows[d.isoformat()], last[d.isoformat()] = "50000", days[9].isoformat()  # V0, last_v = day 10
        else:
            rows[d.isoformat()], last[d.isoformat()] = ("50000" if i < 10 else "49000"), days[11].isoformat()
    ev = {days[10]: [CASH]}
    # V1 covers days 8-12: A(day8..10)=49,000 per plan; fix rows 7..9 = 49000
    for i in (7, 8, 9):
        rows[days[i].isoformat()] = "49000"
    nom, fs = reconstruct(src(rows, last), ev, {})
    assert fs[0].f == Decimal("0.980000000000")
    byd = {b.trading_date: b.c for b in nom}
    assert [byd[d] for d in days[:10]] == [50000] * 10      # global-last rule would give 51,020 for days 1-7
    assert byd[days[10]] == byd[days[11]] == 49000


def test_G13b_gap():
    days = [date(2026, 10, 1) + timedelta(i) for i in range(16)]
    rows, last = {}, {}
    for i, d in enumerate(days):
        if i < 10:
            rows[d.isoformat()], last[d.isoformat()] = "50000", days[9].isoformat()
        elif i >= 11:
            rows[d.isoformat()], last[d.isoformat()] = "49000", days[15].isoformat()
    ev = {days[10]: [CASH]}
    nom, fs = reconstruct(src(rows, last), ev, {})
    assert fs and fs[0].f == Decimal("0.980000000000")
    assert {b.c for b in nom if b.trading_date <= days[9]} == {50000}


def test_G12_fpt():
    ev = {date(2026, 9, 21): [CaEvent("stock_dividend", 10, 1)]}
    nom, fs = reconstruct(src({"2026-09-17": "65182.47", "2026-09-18": "65182.47", "2026-09-21": "65000.00", "2026-09-22": "65100.00"}), ev, {})
    assert fs[0].f == Decimal("0.909090909091")
    assert {b.trading_date: b.c for b in nom}[date(2026, 9, 18)] == 71701  # build note says 71,700: doc slip
