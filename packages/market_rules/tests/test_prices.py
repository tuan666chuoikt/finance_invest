from finvest_rules.prices import tick_size


def test_tick_sizes_by_venue():  # VN§3
    assert [tick_size("HOSE", "STOCK", p) for p in (9_990, 10_000, 49_950, 50_000)] == [10, 50, 50, 100]
    kinds = (("HOSE", "ETF"), ("HNX", "STOCK"), ("HNX", "ETF"), ("UPCOM", "STOCK"))
    assert [tick_size(e, t, 9_000) for e, t in kinds] == [10, 100, 1, 100]
