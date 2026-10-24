import gzip
from datetime import date
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.kbs import KbsSource
from finvest_crawler.adapters.registry import make_source, source_for
from finvest_crawler.adapters.ssi import SsiSource
from finvest_crawler.adapters.vci import VciSource
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from finvest_market_data.domain.models import Bar
from finvest_market_data.domain.ports import Unsupported

FIX = Path(__file__).parent / "fixtures"
D = date(2026, 10, 15)


def fetcher(tmp_path) -> Fetcher:
    def handler(req):
        name = "ssi/history" if "ssi.com.vn" in str(req.url) else "vci/gap_chart"
        return httpx.Response(200, content=gzip.decompress((FIX / name / "FPT-1d.json.gz").read_bytes()))

    buckets = {n: TokenBucket(100) for n in ("kbs", "vci", "ssi")}
    return Fetcher(httpx.Client(transport=httpx.MockTransport(handler)), buckets, Archive(tmp_path), "ua")


def test_make_source_by_name(tmp_path):
    f = fetcher(tmp_path)
    assert [type(make_source(n, f)) for n in ("kbs", "vci", "ssi")] == [KbsSource, VciSource, SsiSource]


def test_unknown_name_lists_known(tmp_path):
    with pytest.raises(ValueError, match="kbs, vci, ssi"):
        make_source("cafef", fetcher(tmp_path))


def test_defaults_follow_settings(tmp_path):
    s, f = Settings(), fetcher(tmp_path)
    assert [source_for(r, s, f).name for r in ("ticks", "symbols", "bars")] == ["kbs", "vci", "vci"]
    assert isinstance(source_for("snapshot", s, f), SsiSource)
    for k in (KbsSource, VciSource):
        with pytest.raises(Unsupported):
            k(f).snapshot_bars(D)


@pytest.mark.parametrize("name", ["vci", "ssi"])
def test_bars_swap_changes_no_calling_code(tmp_path, name):
    src = source_for("bars", Settings(source_bars=name), fetcher(tmp_path))
    bars = src.bars(["FPT"], "1d", D, 50)
    b = bars[0]
    assert isinstance(b, Bar) and b.symbol == "FPT" and b.source == name
    assert isinstance(b.c, int) and 10_000 < b.c < 200_000 and b.v > 0
    assert b.ts.utcoffset().total_seconds() == 0
