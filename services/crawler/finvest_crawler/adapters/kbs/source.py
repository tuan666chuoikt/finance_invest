from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from finvest_market_data.domain.models import Bar, IndexBar, SymbolRecord, Tick
from finvest_market_data.domain.ports import SourceNoLongerServes, Unsupported

from finvest_crawler.adapters.kbs.payloads import validate_envelope
from finvest_crawler.fetch import Fetcher

VN = ZoneInfo("Asia/Ho_Chi_Minh")
URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/trade/history/{symbol}?page=1&limit=50000"


def _local(t: str) -> datetime:
    head, cc = t.rsplit(":", 1)
    return datetime.strptime(head, "%Y-%m-%d %H:%M:%S").replace(microsecond=int(cc) * 10_000, tzinfo=VN)


def parse_ticks(
    payload: bytes, symbol: str, trading_date: date, raw_path: Path = Path("<unarchived>")
) -> list[Tick]:
    """Pure: KBS tape -> ticks sorted by `seq` (AVO); SourceNoLongerServes if tape is not `trading_date`."""
    rows = [(_local(r.t), r) for r in validate_envelope(payload, raw_path).data]
    if not rows:
        raise SourceNoLongerServes(symbol, None)
    served = {ts.date() for ts, _ in rows}
    if served != {trading_date}:
        raise SourceNoLongerServes(symbol, max(served))
    ticks = [Tick(symbol, ts.astimezone(UTC), r.AVO, r.FMP, r.FV, r.LC or None, "kbs") for ts, r in rows]
    return sorted(ticks, key=lambda x: x.seq)


class KbsSource:
    name = "kbs"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def ticks(self, symbol: str, trading_date: date) -> list[Tick]:
        f = self.fetcher
        url = URL.format(symbol=symbol)
        payload = f.get("kbs", url, feed="ticks", trading_date=trading_date, name=symbol, archive=False)
        path = f.archive.path("ticks", trading_date, symbol)
        ticks = parse_ticks(payload, symbol, trading_date, path)
        if not path.exists():  # archive = cache of accepted tapes only (ADR-S-008, platform.md 4 v1.2)
            f.archive.write("ticks", trading_date, symbol, payload)
        return ticks

    def symbols(self, as_of: date, include_delisted: bool = False) -> list[SymbolRecord]:
        raise Unsupported("kbs has no symbol list")

    def index_members(self, index_code: str, as_of: date) -> list[str]:
        raise Unsupported("kbs has no index members")

    def bars(self, symbols: list[str], grain: Literal["1m", "1d"], to: date, count: int) -> list[Bar]:
        raise Unsupported("kbs adapter serves ticks only")

    def index_bars(self, codes: list[str], to: date, count: int) -> list[IndexBar]:
        raise Unsupported("kbs index bars are not implemented")
