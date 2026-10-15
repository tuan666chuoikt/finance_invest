"""SSI iBoard daily bars (S2). Unit rule (F-010 G/W/T 1): S2 quotes THOUSAND VND (`58` = 58,000 VND);
this adapter converts with `to_vnd(x, "thousand_vnd")` at the boundary,
so a `Bar` is integer VND exactly like VCI's."""

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from finvest_market_data.domain.models import Bar, SymbolRecord, Tick
from finvest_market_data.domain.ports import PayloadShapeError, Unsupported
from finvest_market_data.domain.units import to_vnd
from pydantic import TypeAdapter

from finvest_crawler.adapters.ssi.payloads import SsiEnvelope
from finvest_crawler.adapters.vci.payloads import validate
from finvest_crawler.fetch import Fetcher

VN = ZoneInfo("Asia/Ho_Chi_Minh")
URL = "https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol={symbol}&from={a}&to={b}"
_ENV = TypeAdapter(SsiEnvelope)


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

    def symbols(self) -> list[SymbolRecord]:
        raise Unsupported("ssi has no symbol list in S01")

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
