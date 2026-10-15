import hashlib
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from finvest_market_data.domain.models import Bar, SymbolRecord, Tick
from finvest_market_data.domain.ports import PayloadShapeError, Unsupported
from finvest_market_data.domain.units import to_vnd
from pydantic import TypeAdapter

from finvest_crawler.adapters.vci.payloads import VciBars, VciSymbol, validate
from finvest_crawler.fetch import Fetcher

VN = ZoneInfo("Asia/Ho_Chi_Minh")
BASE = "https://trading.vietcap.com.vn/api"
BOARD = {"HSX": "HOSE", "HNX": "HNX", "UPCOM": "UPCOM"}  # DELISTED/BOND boards are dropped
_SYMBOLS = TypeAdapter(list[VciSymbol])
_BARS = TypeAdapter(list[VciBars])


def parse_symbols(payload: bytes, raw_path: Path = Path("<unarchived>")) -> list[SymbolRecord]:
    """Pure: V3 rows -> STOCK/ETF on HOSE/HNX/UPCOM; CW and delisted excluded (1-sprint-plan.md note 2)."""
    return [
        SymbolRecord(r.symbol, BOARD[r.board], r.type, r.organName or "", r.enOrganName or "",
                     r.icbCode2 or None, False, "vci")
        for r in validate(_SYMBOLS, payload, raw_path)
        if r.board in BOARD and r.type in ("STOCK", "ETF")
    ]


def parse_bars(payload: bytes, raw_path: Path = Path("<unarchived>")) -> list[Bar]:
    """Pure: V2 column arrays -> daily bars in integer VND (adjusted floats rounded half-up, data.md §1.4)."""
    bars = []
    for s in validate(_BARS, payload, raw_path):
        if not len(s.t) == len(s.o) == len(s.h) == len(s.l) == len(s.c) == len(s.v):
            raise PayloadShapeError(f"vci payload shape changed: {s.symbol} ragged arrays", raw_path)
        for t, o, h, lo, c, v in zip(s.t, s.o, s.h, s.l, s.c, s.v, strict=True):
            day = datetime.fromtimestamp(t, UTC).date()  # t is 00:00 UTC of the trading day
            try:
                bars.append(Bar(s.symbol, datetime.combine(day, time(), VN).astimezone(UTC),
                                *(to_vnd(x, "vnd") for x in (o, h, lo, c)), v, None, "vci"))
            except ValueError as e:
                raise PayloadShapeError(f"vci bar {s.symbol} {day}: {e}", raw_path) from e
    return bars


class VciSource:
    name = "vci"

    def __init__(self, fetcher: Fetcher, today: Callable[[], date] = lambda: datetime.now(VN).date()) -> None:
        self.fetcher, self.today = fetcher, today

    def symbols(self) -> list[SymbolRecord]:
        f, d = self.fetcher, self.today()
        payload = f.get("vci", f"{BASE}/price/symbols/getAll", feed="symbols", trading_date=d, name="getAll")
        return parse_symbols(payload, f.archive.path("symbols", d, "getAll"))

    def ticks(self, symbol: str, trading_date: date) -> list[Tick]:
        raise Unsupported("vci ticks are out of scope in S01")

    def bars(self, symbols: list[str], grain: Literal["1m", "1d"], to: date, count: int) -> list[Bar]:
        if grain != "1d":
            raise Unsupported("vci 1m bars are out of scope in S01")
        f = self.fetcher
        body = {"timeFrame": "ONE_DAY", "symbols": symbols, "countBack": count,
                "to": int(datetime.combine(to, time(23, 59, 59), VN).timestamp())}
        # one file per request; long symbol lists are hashed to keep the file name short
        joined = ",".join(symbols)
        key = "-".join(symbols) if len(symbols) < 4 else hashlib.sha1(joined.encode()).hexdigest()[:12]
        name = f"{key}-1d-{count}"
        payload = f.get("vci", f"{BASE}/chart/OHLCChart/gap-chart", feed="bars_1d", trading_date=to,
                        name=name, method="POST", json=body)
        return parse_bars(payload, f.archive.path("bars_1d", to, name))
