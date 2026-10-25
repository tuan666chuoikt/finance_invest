import gzip
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.vci import VciSource
from finvest_crawler.adapters.vci.source import parse_bars, parse_index_bars, parse_symbols
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_market_data.domain.ports import PayloadShapeError, Unsupported

FIX = Path(__file__).parent / "fixtures/vci"
D = date(2026, 10, 15)


def load(name: str) -> bytes:
    return gzip.decompress((FIX / name).read_bytes())


def bars_payload(**over) -> bytes:
    s = {"symbol": "FPT", "o": [1], "h": [1], "l": [1], "c": [1], "v": [10], "t": ["1792022400"],
         "accumulatedValue": [0.001]}
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


def test_symbols_include_delisted_adds_only_delisted_stocks():
    raw = load("symbols_getAll/sample.json.gz")
    syms = parse_symbols(raw, include_delisted=True)
    gone = [s for s in syms if s.is_delisted]
    assert len(syms) == 32 and len(gone) == 5  # hand count: 27 + 5 DELISTED STOCK; DELISTED CW, BOND stay out
    assert {s.type for s in gone} == {"STOCK"} and {s.exchange for s in gone} == {"UPCOM"}  # placeholder
    assert not any(s.is_delisted for s in parse_symbols(raw))


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


def test_bars_fixture_first_bar_and_nominal_value():
    b = parse_bars(load("gap_chart/FPT-1d.json.gz"))[0]
    assert (b.o, b.h, b.l, b.c, b.v) == (65819, 66637, 64819, 65001, 6618016)  # half-up from .84/.03/.83/.65
    assert b.value == 474963630000  # accumulatedValue 474963.63 million VND
    assert b.trading_date == date(2026, 8, 4)
    assert b.l <= b.value // b.v <= b.h * 1.15  # 71768 VND: nominal price = adjusted close x 1.1 bonus


def test_value_is_rounded_half_up_to_one_vnd():
    (b,) = parse_bars(bars_payload(accumulatedValue=[0.0000015]))
    assert b.value == 2  # 1.5 VND


def test_index_bars_keep_two_decimals():
    (b,) = parse_index_bars(bars_payload(
        symbol="VNINDEX", o=[1700.104], h=[1720.555], l=[1699.99], c=[1710.25], v=[2_000_000],
        accumulatedValue=[20000.5]))
    assert (str(b.o), str(b.h), str(b.c), b.value) == ("1700.10", "1720.56", "1710.25", 20000500000)
    assert (b.index_code, b.trading_date) == ("VNINDEX", date(2026, 10, 15))


def test_missing_accumulated_value_is_a_shape_error():
    raw = json.loads(bars_payload())
    del raw[0]["accumulatedValue"]
    with pytest.raises(PayloadShapeError):
        parse_bars(json.dumps(raw).encode())


@pytest.mark.parametrize(("c", "want"), [("65182.47", 65182), ("65182.5", 65183), ("58000", 58000)])
def test_close_rounding(c, want):
    (b,) = parse_bars(bars_payload(c=[json.loads(c)], o=[1], h=[json.loads(c)]))
    assert b.c == want


@pytest.mark.parametrize("bad", [bars_payload(c=[]), bars_payload(v=["x"]),
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
    src = VciSource(f)
    assert len(src.symbols(D)) == 27
    assert len(src.bars(["FPT"], "1d", D, 50)) == 50
    assert seen[0][:2] == ("GET", "https://trading.vietcap.com.vn/api/price/symbols/getAll")
    assert seen[1][:2] == ("POST", "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart")
    body = json.loads(seen[1][2])
    assert (body["timeFrame"], body["symbols"], body["countBack"]) == ("ONE_DAY", ["FPT"], 50)
    assert body["to"] == int(datetime(2026, 10, 15, 16, 59, 59, tzinfo=UTC).timestamp())
    assert (tmp_path / "symbols/2026-10-15/getAll.json.gz").exists()
    assert (tmp_path / "bars_1d/2026-10-15/FPT-1d-50.json.gz").exists()
    src.symbols(D)
    assert len(seen) == 2  # second call replayed from the archive
    with pytest.raises(Unsupported):
        src.ticks("FPT", D)
    with pytest.raises(Unsupported):
        src.bars(["FPT"], "1m", D, 1)


def test_bar_with_zero_close_is_dropped_not_fatal(caplog):
    # recorded live 2026-10-16 (ABI 2009-09-16: o/h/l > 0, c = 0, v = 10500) and the v = 0 placeholder rows
    assert parse_bars(bars_payload(c=[0]), Path("/arch/x.json.gz")) == []
    assert "vci bar dropped" in caplog.text
    assert parse_bars(bars_payload(o=[0], h=[0], l=[0], c=[0], v=[0])) == []


@pytest.mark.parametrize(("av", "want"), [(222242000000, 222_242_000_000), (6386472.73, 6_386_472_730_000),
                                          (20000.5, 20_000_500_000)])
def test_index_value_unit_is_mixed(av, want):
    (b,) = parse_index_bars(bars_payload(symbol="VN30", v=[10**7], accumulatedValue=[av]))
    assert b.value == want  # raw VND (2012-02-06) vs million VND (2026-10-16)


def test_index_value_outside_ratio_band_is_dropped_and_bar_kept(caplog):
    # 20000.5 million VND = 2e10; / 2 = 1e10 per unit (live VNINDEX bug) -> dropped; / 4e5 = 5e4 -> kept
    (bad,) = parse_index_bars(bars_payload(symbol="VNINDEX", c=[1710.25], v=[2], accumulatedValue=[20000.5]))
    assert (bad.value, str(bad.c)) == (None, "1710.25")
    assert "vci index value dropped" in caplog.text
    (ok,) = parse_index_bars(bars_payload(symbol="VNINDEX", v=[400_000], accumulatedValue=[20000.5]))
    assert ok.value == 20_000_500_000
    (zero,) = parse_index_bars(bars_payload(symbol="VNINDEX", v=[400_000], accumulatedValue=[0]))
    assert zero.value is None
    (stock,) = parse_bars(bars_payload(v=[2], c=[10000], accumulatedValue=[20000.5]))
    assert stock.value == 20001  # stocks path unchanged: ratio 1 to v x c, outside the index band yet kept


@pytest.mark.parametrize(("av", "want"), [(474963.63, 474_963_630_000), (474963630000, 474_963_630_000)])
def test_stock_value_unit_is_picked_by_ratio_to_volume_x_close(av, want):
    (b,) = parse_bars(bars_payload(v=[6_618_016], c=[65000], accumulatedValue=[av]))
    assert b.value == want  # ratio 1.10 to v x c either way


@pytest.mark.parametrize("av", [1e19, -5])
def test_value_outside_bigint_is_none_and_bar_is_kept(av, caplog):
    # v x c = 1e17: million reading 1e19 > 2**63 - 1; negative is never valid
    (b,) = parse_bars(bars_payload(v=[10**9], c=[10**8], accumulatedValue=[av]), Path("/arch/x.json.gz"))
    assert b.value is None and b.c == 10**8
    assert caplog.text.count("vci value dropped") == 1 and "/arch/x.json.gz" in caplog.text


def test_vn30_fixture_values_fit_bigint_and_have_no_era_jump():
    bars = parse_index_bars(load("gap_chart/VN30-1d.json.gz"))
    vals = [b.value for b in bars]
    assert len(bars) <= 60 and {date(2012, 2, 6), date(2026, 10, 16)} <= {b.trading_date for b in bars}
    assert all(v is not None and 0 < v < 2**63 for v in vals)
    assert max(vals) / min(vals) < 1e4  # a 1e6 era mix-up would exceed this
    assert {b.trading_date: b.value for b in bars}[date(2026, 10, 16)] == 6_386_472_732_020


def test_archive_name_matches_the_file_gap_chart_writes(tmp_path):
    f = Fetcher(httpx.Client(transport=httpx.MockTransport(
        lambda req: httpx.Response(200, content=load("gap_chart/FPT-1d.json.gz")))),
        {"vci": TokenBucket(100)}, Archive(tmp_path), "ua")
    src = VciSource(f)
    assert src.archive_name(["FPT"], 8) == "FPT-1d-8"
    many = [f"S{i:02d}" for i in range(50)]
    src.bars(many, "1d", D, 8)
    assert (tmp_path / f"bars_1d/2026-10-15/{src.archive_name(many, 8)}.json.gz").exists()
    assert len(src.archive_name(many, 8)) < 30
