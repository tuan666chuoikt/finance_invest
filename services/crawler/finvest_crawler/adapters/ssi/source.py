"""SSI iBoard daily bars (S2). Unit rule (F-010 G/W/T 1): S2 quotes THOUSAND VND (`58` = 58,000 VND);
this adapter converts with `to_vnd(x, "thousand_vnd")` at the boundary,
so a `Bar` is integer VND exactly like VCI's."""

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from finvest_market_data.domain.models import Bar, IndexBar, SymbolRecord, Tick
from finvest_market_data.domain.ports import PayloadShapeError, SourceNoLongerServes, Unsupported
from finvest_market_data.domain.units import to_vnd
from pydantic import TypeAdapter

from finvest_crawler.adapters.ssi.payloads import SsiEnvelope, SsiExchange
from finvest_crawler.adapters.vci.payloads import validate
from finvest_crawler.fetch import Fetcher

VN = ZoneInfo("Asia/Ho_Chi_Minh")
URL = "https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol={symbol}&from={a}&to={b}"
EXCHANGE_URL = "https://iboard-query.ssi.com.vn/stock/exchange/{ex}"
_ENV = TypeAdapter(SsiEnvelope)
_EXCHANGE = TypeAdapter(SsiExchange)
_TYPES = {"s": "STOCK", "e": "ETF"}


def parse_symbols(payload: bytes, exchange: str, raw_path: Path = Path("<unarchived>")) -> list[SymbolRecord]:
    """Pure: S1 rows -> STOCK/ETF records; `firstTradingDate` "yyyymmdd" (0 = unknown) -> `listed_at`."""
    rows = validate(_EXCHANGE, payload, raw_path, "ssi").data
    return [
        SymbolRecord(r.stockSymbol, exchange, _TYPES[r.stockType], r.companyNameVi or "",
                     r.companyNameEn or "", None, False, "ssi", _day(r.firstTradingDate))
        for r in rows if r.stockType in _TYPES  # type: ignore[arg-type]
    ]


def _day(s: str | None) -> date | None:
    try:
        return datetime.strptime(s or "", "%Y%m%d").date()
    except ValueError:
        return None  # absent, "0" or garbage: unknown, never an error


def parse_snapshot(
    payload: bytes, session: date, raw_path: Path = Path("<unarchived>"), exchange: str = "?"
) -> tuple[list[Bar], list[str]]:
    """Pure: S1 board (VND) -> (one bar per traded stock/ETF, names with no trade).

    SourceNoLongerServes when the board shows another session (stale weekend board, data not yet rolled)."""
    rows = validate(_EXCHANGE, payload, raw_path, "ssi").data
    if rows and rows[0].tradingDate != session.strftime("%Y%m%d"):
        raise SourceNoLongerServes(exchange, _day(rows[0].tradingDate))
    ts = datetime.combine(session, time(), VN).astimezone(UTC)
    bars, idle = [], []
    for r in rows:
        if r.stockType not in _TYPES:
            continue
        if not r.nmTotalTradedQty or not r.openPrice:
            idle.append(r.stockSymbol)
            continue
        try:
            o, h, lo, c = (to_vnd(x, "vnd") for x in (r.openPrice, r.highest, r.lowest, r.matchedPrice))  # type: ignore[arg-type]
            if h < max(o, c) or lo > min(o, c):
                raise ValueError(f"high {h} / low {lo} do not bracket open {o} close {c}")
            value = to_vnd(r.nmTotalTradedValue or 0, "vnd")
            bars.append(Bar(r.stockSymbol, ts, o, h, lo, c, r.nmTotalTradedQty, value, "ssi"))
        except (ValueError, TypeError, ArithmeticError) as e:  # None price -> TypeError/InvalidOperation
            raise PayloadShapeError(f"ssi board {exchange} {r.stockSymbol}: {e}", raw_path) from e
    return bars, idle


def parse_bars(payload: bytes, symbol: str, raw_path: Path = Path("<unarchived>")) -> list[Bar]:
    """Pure: S2 column arrays (thousand VND) -> daily bars in integer VND."""
    d = validate(_ENV, payload, raw_path, "ssi").data
    if d.s == "no_data":
        return []
    if d.s != "ok" or not len(d.t) == len(d.o) == len(d.h) == len(d.l) == len(d.c) == len(d.v):
        raise PayloadShapeError(f"ssi payload shape changed: status {d.s!r} or ragged arrays", raw_path)
    bars = []
    for t, o, h, lo, c, v in zip(d.t, d.o, d.h, d.l, d.c, d.v, strict=True):
        day = datetime.fromtimestamp(t, UTC).date()  # t is 00:00 UTC of the trading day
        try:
            bars.append(Bar(symbol, datetime.combine(day, time(), VN).astimezone(UTC),
                            *(to_vnd(x, "thousand_vnd") for x in (o, h, lo, c)), v, None, "ssi"))
        except ValueError as e:
            raise PayloadShapeError(f"ssi bar {symbol} {day}: {e}", raw_path) from e
    return bars


class SsiSource:
    name = "ssi"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def symbols(self, as_of: date, include_delisted: bool = False) -> list[SymbolRecord]:
        """S1 x3 exchanges (live rows only; `include_delisted` is moot). Used for `listed_at`."""
        f, out = self.fetcher, []
        for ex in ("hose", "hnx", "upcom"):
            payload = f.get("ssi", EXCHANGE_URL.format(ex=ex), feed="symbols", trading_date=as_of, name=ex)
            out += parse_symbols(payload, ex.upper(), f.archive.path("symbols", as_of, ex))  # type: ignore[arg-type]
        return out

    def snapshot_bars(self, session: date) -> tuple[list[Bar], list[str]]:
        """S1 x3 exchanges: the finished session's bar for every listed name. A board of another session is
        never archived under `session`; a replay of an accepted day costs 0 requests."""
        f, bars, idle = self.fetcher, [], []
        for ex in ("hose", "hnx", "upcom"):
            name = f"board-{ex}"
            url = EXCHANGE_URL.format(ex=ex)
            payload = f.get("ssi", url, feed="bars_1d", trading_date=session, name=name, archive=False)
            path = f.archive.path("bars_1d", session, name)
            b, i = parse_snapshot(payload, session, path, ex.upper())
            if not path.exists():
                f.archive.write("bars_1d", session, name, payload)
            bars, idle = bars + b, idle + i
        return bars, idle

    def index_members(self, index_code: str, as_of: date) -> list[str]:
        raise Unsupported("ssi index members: use vci (smaller payload)")

    def ticks(self, symbol: str, trading_date: date) -> list[Tick]:
        raise Unsupported("ssi has no ticks")

    def bars(self, symbols: list[str], grain: Literal["1m", "1d"], to: date, count: int) -> list[Bar]:
        if grain != "1d":
            raise Unsupported("ssi 1m bars are out of scope in S01")
        f, out = self.fetcher, []
        end = datetime.combine(to, time(23, 59, 59), VN)
        # shortcut: count*7/5+10 calendar days assumes <=5 sessions a week; widen if bars come back short
        start = end - timedelta(days=count * 7 // 5 + 10)
        for s in symbols:
            name = f"{s}-1d-{count}"
            url = URL.format(symbol=s, a=int(start.timestamp()), b=int(end.timestamp()))
            payload = f.get("ssi", url, feed="bars_1d_ssi", trading_date=to, name=name)
            out += parse_bars(payload, s, f.archive.path("bars_1d_ssi", to, name))[-count:]
        return out

    def index_bars(self, codes: list[str], to: date, count: int) -> list[IndexBar]:
        raise Unsupported("ssi index bars are not implemented")
