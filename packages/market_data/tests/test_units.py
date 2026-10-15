from decimal import Decimal

from finvest_market_data.domain.units import to_shares, to_vnd


def test_to_vnd_examples() -> None:
    assert to_vnd("93.5", "thousand_vnd") == 93500
    assert to_vnd("65182.47", "vnd") == 65182
    assert to_vnd("65182.5", "vnd") == 65183
    assert to_vnd(58000, "vnd") == 58000
    assert to_vnd(Decimal("0.0005"), "thousand_vnd") == 1  # 0.5 VND rounds half up


def test_to_shares() -> None:
    assert to_shares(10, 10) == 100
