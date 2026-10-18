import hashlib
from datetime import date
from decimal import Decimal

import pytest
from finvest_rules import RULES, RULES_VERSION, Costs, Rule, RuleNotEffective, costs, rule

# Bump RULES_VERSION in finvest_rules/costs.py, then update this hash, whenever a rule changes.
RULES_HASH = "2019ac0ca54a268d"


def test_costs_v1():
    assert costs(date(2026, 10, 12)) == Costs(Decimal("0.0015"), Decimal("0.0015"), Decimal("0.001"), 100, 2)
    assert rule("sell_tax_rate", date(2026, 10, 12)).verified is True
    assert rule("buy_fee_rate", date(2026, 10, 12)).verified is False


def test_new_entry_takes_over_on_its_date():
    r = {k: list(v) for k, v in RULES.items()}
    r["buy_fee_rate"].append(Rule(Decimal("0.0020"), date(2027, 1, 1), False, None, "test", "VN§5"))
    assert rule("buy_fee_rate", date(2026, 12, 31), r).value == Decimal("0.0015")
    assert rule("buy_fee_rate", date(2027, 1, 1), r).value == Decimal("0.0020")
    assert RULES["buy_fee_rate"][-1].value == Decimal("0.0015")  # RULES itself untouched


def test_wrong_type_entry_raises():
    bad = {k: list(v) for k, v in RULES.items()}
    bad["board_lot"] = [Rule(Decimal("100"), date(2006, 1, 1), True, None, "test", "VN§4")]
    with pytest.raises(TypeError):
        costs(date(2026, 10, 12), bad)
    bad = {k: list(v) for k, v in RULES.items()}
    bad["buy_fee_rate"] = [Rule(1, date(2006, 1, 1), False, None, "test", "VN§5")]
    with pytest.raises(TypeError):
        costs(date(2026, 10, 12), bad)


def test_before_first_entry_raises():
    with pytest.raises(RuleNotEffective):
        rule("board_lot", date(2005, 1, 1))


def test_rules_changed_requires_version_bump():
    h = hashlib.sha256(repr(sorted(RULES.items())).encode()).hexdigest()[:16]
    msg = f"RULES changed (hash {h}): bump RULES_VERSION (now {RULES_VERSION}) and update RULES_HASH"
    assert h == RULES_HASH, msg
