"""The `MarketDataSource` port (codebase.md §3), S01 subset. Adapters raise `Unsupported` otherwise."""

from datetime import date
from pathlib import Path
from typing import Literal, Protocol

from finvest_market_data.domain.models import Bar, IndexBar, SymbolRecord, Tick


class SourceError(Exception):
    """Base of every source failure."""


class Unsupported(SourceError):
    """This source does not implement the requested method."""


class SourceNoLongerServes(SourceError):
    """The source can no longer serve the requested session (manifest reason `source_no_longer_serves`).

    `served_date` is the session the source did serve instead, or None when it served nothing.
    """

    def __init__(self, symbol: str, served_date: date | None = None) -> None:
        super().__init__(f"{symbol}: source serves {served_date or 'no session'}, not the requested one")
        self.symbol, self.served_date = symbol, served_date


class PayloadShapeError(SourceError):
    """Payload failed schema validation; `raw_path` points at the saved raw bytes."""

    def __init__(self, message: str, raw_path: Path) -> None:
        super().__init__(f"{message} (raw: {raw_path})")
        self.raw_path = raw_path


class MarketDataSource(Protocol):
    name: str

    def symbols(self, as_of: date, include_delisted: bool = False) -> list[SymbolRecord]: ...

    def ticks(self, symbol: str, trading_date: date) -> list[Tick]: ...

    def index_members(self, index_code: str, as_of: date) -> list[str]: ...

    def bars(self, symbols: list[str], grain: Literal["1m", "1d"], to: date, count: int) -> list[Bar]: ...

    def index_bars(self, codes: list[str], to: date, count: int) -> list[IndexBar]: ...

    def archive_name(self, symbols: list[str], count: int) -> str: ...
