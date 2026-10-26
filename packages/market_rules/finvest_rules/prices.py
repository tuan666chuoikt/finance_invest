"""Price-step rules (VN§3 matching sessions): pure, imports nothing of ours."""


def tick_size(exchange: str, type_: str, price: int) -> int:
    if exchange == "HOSE":
        return 10 if type_ == "ETF" or price < 10_000 else 50 if price < 50_000 else 100
    return 1 if exchange == "HNX" and type_ == "ETF" else 100
