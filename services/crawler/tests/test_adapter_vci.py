import gzip
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.vci import VciSource
from finvest_crawler.adapters.vci.source import parse_bars, parse_symbols
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_market_data.domain.ports import PayloadShapeError, Unsupported

FIX = Path(__file__).parent / "fixtures/vci"
D = date(2026, 10, 15)


def load(name: str) -> bytes:
    return gzip.decompress((FIX / name).read_bytes())


def bars_payload(**over) -> bytes:
    s = {"symbol": "FPT", "o": [1], "h": [1], "l": [1], "c": [1], "v": [10], "t": ["1792022400"]}
    return json.dumps([{**s, **over}]).encode()


def test_symbols_fixture_filters_cw_delisted_and_other_boards():
    raw = json.loads(load("symbols_getAll/sample.json.gz"))
    assert {(r["board"], r["type"]) for r in raw} >= {
        ("HSX", "STOCK"), ("HSX", "ETF"), ("HSX", "CW"), ("HNX", "STOCK"), ("UPCOM", "STOCK"),
        ("DELISTED", "STOCK"), ("DELISTED", "CW")}  # fixture holds every kind we must drop or keep
    syms = parse_symbols(load("symbols_getAll/sample.json.gz"))
    assert len(syms) == 27  # hand count: 8 HSX stock + 3 ETF + 8 HNX stock + 8 UPCOM stock
    assert {s.exchange for s in syms} == {"HOSE", "HNX", "UPCOM"}
    assert {s.type for s in syms} == {"STOCK", "ETF"}
    assert not any(s.is_delisted for s in syms)
    first = syms[0]
    assert (first.symbol, first.exchange, first.icb_code2, first.source) == ("YEG", "HOSE", "5500", "vci")
    assert first.name_vi and first.name_en


def test_symbol_null_names_and_icb():
    row = {"symbol": "ABC", "type": "STOCK", "board": "UPCOM", "organName": None, "enOrganName": None,
           "icbCode2": None}
    (s,) = parse_symbols(json.dumps([row]).encode())
    assert (s.name_vi, s.name_en, s.icb_code2) == ("", "", None)


def test_bars_fixture_rounds_adjusted_floats_half_up():
    bars = parse_bars(load("gap_chart/FPT-1d.json.gz"))
    assert len(bars) == 50 and all(b.symbol == "FPT" and b.source == "vci" for b in bars)
    assert 65182 in {b.c for b in bars}  # fixture close 65182.47
    assert bars[-1].c == 58000 and bars[-1].v == 4964400  # integer close and volume unchanged
    assert bars[-1].ts == datetime(2026, 10, 14, 17, 0, tzinfo=UTC)  # 2026-10-15 00:00 Asia/Ho_Chi_Minh


@pytest.mark.parametrize(("c", "want"), [("65182.47", 65182), ("65182.5", 65183), ("58000", 58000)])
def test_close_rounding(c, want):
    (b,) = parse_bars(bars_payload(c=[json.loads(c)], o=[1], h=[json.loads(c)]))
    assert b.c == want


@pytest.mark.parametrize("bad", [bars_payload(c=[]), bars_payload(c=[0]), bars_payload(v=["x"]),
                                 bars_payload(t=["not-an-epoch"]), b"<html>"])
def test_bad_bars_are_shape_errors(bad):
    with pytest.raises(PayloadShapeError):
        parse_bars(bad, Path("/arch/x.json.gz"))


def test_renamed_symbol_field_names_archive_path():
    bad = load("symbols_getAll/sample.json.gz").replace(b'"board"', b'"market"')
    with pytest.raises(PayloadShapeError, match="board") as e:
        parse_symbols(bad, Path("/arch/symbols/getAll.json.gz"))
    assert e.value.raw_path == Path("/arch/symbols/getAll.json.gz")


def test_source_requests_and_archives(tmp_path):
    seen = []

    def handler(req):
        seen.append((req.method, str(req.url), req.content))
        ok = "getAll" in str(req.url)
        return httpx.Response(200, content=load(
            "symbols_getAll/sample.json.gz"
            if ok else "gap_chart/FPT-1d.json.gz"))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    f = Fetcher(client, {"vci": TokenBucket(100)}, Archive(tmp_path), "ua")
    src = VciSource(f, today=lambda: D)
    assert len(src.symbols()) == 27
    assert len(src.bars(["FPT"], "1d", D, 50)) == 50
    assert seen[0][:2] == ("GET", "https://trading.vietcap.com.vn/api/price/symbols/getAll")
    assert seen[1][:2] == ("POST", "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart")
    body = json.loads(seen[1][2])
    assert (body["timeFrame"], body["symbols"], body["countBack"]) == ("ONE_DAY", ["FPT"], 50)
    assert body["to"] == int(datetime(2026, 10, 15, 16, 59, 59, tzinfo=UTC).timestamp())
    assert (tmp_path / "symbols/2026-10-15/getAll.json.gz").exists()
    assert (tmp_path / "bars_1d/2026-10-15/FPT-1d-50.json.gz").exists()
    src.symbols()
    assert len(seen) == 2  # second call replayed from the archive
    with pytest.raises(Unsupported):
        src.ticks("FPT", D)
    with pytest.raises(Unsupported):
        src.bars(["FPT"], "1m", D, 1)
