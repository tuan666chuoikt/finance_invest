"""The only place a source name is resolved (F-010 G/W/T 3, codebase.md §3 config swap)."""

from typing import Literal

from finvest_market_data.domain.ports import MarketDataSource

from finvest_crawler.adapters.kbs import KbsSource
from finvest_crawler.adapters.ssi import SsiSource
from finvest_crawler.adapters.vci import VciSource
from finvest_crawler.fetch import Fetcher
from finvest_crawler.settings import Settings

SOURCES = {"kbs": KbsSource, "vci": VciSource, "ssi": SsiSource}


def make_source(name: str, fetcher: Fetcher) -> MarketDataSource:
    if name not in SOURCES:
        raise ValueError(f"unknown source {name!r}; known: {', '.join(SOURCES)}")
    return SOURCES[name](fetcher)


def source_for(
    role: Literal["ticks", "symbols", "bars", "snapshot"], settings: Settings, fetcher: Fetcher
) -> MarketDataSource:
    return make_source(getattr(settings, f"source_{role}"), fetcher)
