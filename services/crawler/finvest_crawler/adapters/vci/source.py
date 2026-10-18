import hashlib
import logging
from datetime import UTC, date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from finvest_market_data.domain.models import Bar, IndexBar, SymbolRecord, Tick
from finvest_market_data.domain.ports import PayloadShapeError, Unsupported
from finvest_market_data.domain.units import to_vnd
from pydantic import TypeAdapter

from finvest_crawler.adapters.vci.payloads import VciBars, VciSymbol, validate
from finvest_crawler.fetch import Fetcher

VN = ZoneInfo("Asia/Ho_Chi_Minh")
log = logging.getLogger(__name__)
BASE = "https://trading.vietcap.com.vn/api"
# BOND board is dropped; DELISTED is read only with include_delisted
BOARD = {"HSX": "HOSE", "HNX": "HNX", "UPCOM": "UPCOM"}
_SYMBOLS = TypeAdapter(list[VciSymbol])
_BARS = TypeAdapter(list[VciBars])


def parse_symbols(
    payload: bytes, raw_path: Path = Path("<unarchived>"), include_delisted: bool = False
) -> list[SymbolRecord]:
    """Pure: V3 rows -> STOCK/ETF on HOSE/HNX/UPCOM; CW excluded (1-sprint-plan.md note 2).

    `include_delisted` adds board DELISTED STOCK/ETF rows with `is_delisted=True`. V3 does not say where
    they were listed: `exchange` is the placeholder UPCOM and the caller keeps the last known value.
    """
    return [
        SymbolRecord(r.symbol, BOARD.get(r.board, "UPCOM"), r.type, r.organName or "", r.enOrganName or "",
                     r.icbCode2 or None, r.board == "DELISTED", "vci")
        for r in validate(_SYMBOLS, payload, raw_path)
        if (r.board in BOARD or (include_delisted and r.board == "DELISTED")) and r.type in ("STOCK", "ETF")
    ]


def _rows(payload: bytes, raw_path: Path):
    """Yield (symbol, trading day, o, h, l, c, v, value in VND) per V2 column-array row."""
    for s in validate(_BARS, payload, raw_path):
        cols = (s.o, s.h, s.l, s.c, s.v, s.accumulatedValue)
        if any(len(x) != len(s.t) for x in cols):
            raise PayloadShapeError(f"vci payload shape changed: {s.symbol} ragged arrays", raw_path)
        for t, o, h, lo, c, v, av in zip(s.t, s.o, s.h, s.l, s.c, s.v, s.accumulatedValue, strict=True):
            # t is 00:00 UTC of the trading day; accumulatedValue is million VND
            if v == 0 and min(o, h, lo, c) <= 0:
                continue  # placeholder row for a day the source has no data (live 2026-10-16: o/h/l/c = 0, v = 0)
            yield (s.symbol, datetime.fromtimestamp(t, UTC).date(), o, h, lo, c, v,
                   None if av is None else to_vnd(av, "million_vnd"))


def parse_bars(payload: bytes, raw_path: Path = Path("<unarchived>")) -> list[Bar]:
    """Pure: V2 column arrays -> daily bars in integer VND (adjusted floats rounded half-up, data.md §1.4)."""
    bars = []
    for sym, day, o, h, lo, c, v, value in _rows(payload, raw_path):
        try:
            bars.append(Bar(sym, datetime.combine(day, time(), VN).astimezone(UTC),
                            *(to_vnd(x, "vnd") for x in (o, h, lo, c)), v, value, "vci"))
        except ValueError as e:
            # live 2026-10-16: a few traded days carry close = 0; one bad day must not drop 19 years of history
            log.warning("vci bar dropped: %s %s: %s (raw: %s)", sym, day, e, raw_path)
    return bars


def parse_index_bars(payload: bytes, raw_path: Path = Path("<unarchived>")) -> list[IndexBar]:
    """Pure: V2 payload for index codes (VNINDEX...) -> levels at 2 decimals, half-up (platform.md §1.2)."""
    q = Decimal("0.01")
    return [IndexBar(sym, day, *(x.quantize(q, ROUND_HALF_UP) for x in (o, h, lo, c)), v, value)
            for sym, day, o, h, lo, c, v, value in _rows(payload, raw_path)]


class VciSource:
    name = "vci"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def symbols(self, as_of: date, include_delisted: bool = False) -> list[SymbolRecord]:
        f, d = self.fetcher, as_of
        payload = f.get("vci", f"{BASE}/price/symbols/getAll", feed="symbols", trading_date=d, name="getAll")
        return parse_symbols(payload, f.archive.path("symbols", d, "getAll"), include_delisted)

    def ticks(self, symbol: str, trading_date: date) -> list[Tick]:
        raise Unsupported("vci ticks are out of scope in S01")

    def bars(self, symbols: list[str], grain: Literal["1m", "1d"], to: date, count: int) -> list[Bar]:
        if grain != "1d":
            raise Unsupported("vci 1m bars are out of scope in S01")
        payload, raw = self._gap_chart(symbols, to, count)
        return parse_bars(payload, raw)

    def index_bars(self, codes: list[str], to: date, count: int) -> list[IndexBar]:
        """Index levels keep 2 decimals, so they cannot travel as integer-VND `Bar` (platform.md 1.2)."""
        payload, raw = self._gap_chart(codes, to, count)
        return parse_index_bars(payload, raw)

    def _gap_chart(self, symbols: list[str], to: date, count: int) -> tuple[bytes, Path]:
        f = self.fetcher
        body = {"timeFrame": "ONE_DAY", "symbols": symbols, "countBack": count,
                "to": int(datetime.combine(to, time(23, 59, 59), VN).timestamp())}
        # one file per request; long symbol lists are hashed to keep the file name short
        joined = ",".join(symbols)
        key = "-".join(symbols) if len(symbols) < 4 else hashlib.sha1(joined.encode()).hexdigest()[:12]
        name = f"{key}-1d-{count}"
        payload = f.get("vci", f"{BASE}/chart/OHLCChart/gap-chart", feed="bars_1d", trading_date=to,
                        name=name, method="POST", json=body)
        return payload, f.archive.path("bars_1d", to, name)
