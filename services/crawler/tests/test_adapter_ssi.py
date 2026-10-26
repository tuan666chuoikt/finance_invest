import gzip
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.ssi import SsiSource
from finvest_crawler.adapters.ssi.source import parse_bars, parse_snapshot, parse_symbols
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_market_data.domain.ports import PayloadShapeError, SourceNoLongerServes, Unsupported

FIX = Path(__file__).parent / "fixtures/ssi/history"
D = date(2026, 10, 15)


def load() -> bytes:
    return gzip.decompress((FIX / "FPT-1d.json.gz").read_bytes())


def payload(s="ok", **data) -> bytes:
    d = {"t": [1792022400], "o": [57.5], "h": [58.2], "l": [57.3], "c": [58], "v": [4964400], "s": s}
    return json.dumps({"data": {**d, **data}}).encode()


def test_fixture_thousand_vnd_to_vnd():
    bars = parse_bars(load(), "FPT")
    assert len(bars) == 50 and all(b.source == "ssi" for b in bars)
    last = bars[-1]
    assert (last.o, last.h, last.l, last.c, last.v) == (57500, 58200, 57300, 58000, 4964400)
    assert last.ts == datetime(2026, 10, 14, 17, 0, tzinfo=UTC)


@pytest.mark.parametrize(("c", "want"), [(58, 58000), (58.1, 58100), (58.0004, 58000), (58.0005, 58001)])
def test_close_unit(c, want):
    assert parse_bars(payload(c=[c]), "FPT")[0].c == want


def test_no_data_is_empty_and_unknown_status_is_error():
    assert parse_bars(json.dumps({"data": {"s": "no_data"}}).encode(), "FPT") == []
    with pytest.raises(PayloadShapeError):
        parse_bars(payload(s="error"), "FPT")


@pytest.mark.parametrize("bad", [payload(c=[]), payload(c=[0]), b"<html>", b'{"data": {}}'])
def test_bad_payloads_are_shape_errors(bad):
    with pytest.raises(PayloadShapeError):
        parse_bars(bad, "FPT", Path("/arch/x.json.gz"))


def test_source_requests_and_archives(tmp_path):
    seen = []

    def handler(req):
        seen.append(req.url)
        return httpx.Response(200, content=load())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    f = Fetcher(client, {"ssi": TokenBucket(100)}, Archive(tmp_path), "ua")
    src = SsiSource(f)
    assert len(src.bars(["FPT"], "1d", D, 20)) == 20  # trimmed to the newest `count`
    (u,) = seen
    assert (u.host, u.path) == ("iboard-api.ssi.com.vn", "/statistics/charts/history")
    q = dict(u.params)
    end = int(datetime(2026, 10, 15, 16, 59, 59, tzinfo=UTC).timestamp())  # end of 15 Oct, Asia/Ho_Chi_Minh
    assert (q["resolution"], q["symbol"], q["to"]) == ("1D", "FPT", str(end))
    assert (tmp_path / "bars_1d_ssi/2026-10-15/FPT-1d-20.json.gz").exists()
    for call in (lambda: src.index_members("VN30", D), lambda: src.ticks("FPT", D),
                 lambda: src.bars(["FPT"], "1m", D, 1)):
        with pytest.raises(Unsupported):
            call()


def test_s1_fixture_listed_at():
    raw = (Path(__file__).parent / "fixtures/ssi/exchange/hose.json.gz").read_bytes()
    recs = parse_symbols(gzip.decompress(raw), "HOSE")
    assert len(recs) == 46 and all(r.exchange == "HOSE" and r.source == "ssi" for r in recs)
    dated = {r.symbol: r.listed_at for r in recs if r.listed_at}
    assert len(dated) == 5 and dated["AAN"] == date(2026, 5, 22)  # "0" -> None, 41 rows


def test_s1_row_without_first_trading_date_is_none():
    rows = [{"stockSymbol": "AAA", "stockType": "s"}, {"stockSymbol": "BBB", "stockType": "w"}]
    p = json.dumps({"data": rows})
    (r,) = parse_symbols(p.encode(), "HNX")
    assert (r.symbol, r.listed_at) == ("AAA", None)  # warrants dropped, missing field tolerated


def test_symbols_makes_three_archived_calls(tmp_path):
    seen = []

    def handler(req):
        seen.append(req.url.path)
        return httpx.Response(200, content=b'{"data": []}')

    client = httpx.Client(transport=httpx.MockTransport(handler))
    f = Fetcher(client, {"ssi": TokenBucket(100)}, Archive(tmp_path), "ua")
    assert SsiSource(f).symbols(D) == []
    assert seen == ["/stock/exchange/hose", "/stock/exchange/hnx", "/stock/exchange/upcom"]
    assert (tmp_path / "symbols/2026-10-15/upcom.json.gz").exists()


S1 = date(2026, 10, 16)


def hose() -> bytes:
    return gzip.decompress((Path(__file__).parent / "fixtures/ssi/exchange/hose.json.gz").read_bytes())


def board(*rows, day="20261016") -> bytes:
    base = {"stockType": "s", "tradingDate": day, "openPrice": 10, "highest": 12, "lowest": 9,
            "matchedPrice": 11, "nmTotalTradedQty": 5, "nmTotalTradedValue": 55}
    return json.dumps({"data": [{**base, **r} for r in rows]}).encode()


def test_snapshot_fixture_aaa_and_row_accounting():
    bars, idle = parse_snapshot(hose(), S1)
    aaa = next(b for b in bars if b.symbol == "AAA")
    got = (aaa.o, aaa.h, aaa.l, aaa.c, aaa.v, aaa.value, aaa.source)
    assert got == (7090, 7190, 7020, 7100, 684300, 4855893000, "ssi")
    assert aaa.ts == datetime(2026, 10, 15, 17, 0, tzinfo=UTC)
    assert aaa.ref == 7000  # S1 refPrice, VND
    assert (len(bars), len(idle)) == (41, 5)  # 46 s|e rows = 41 traded + 5 without trades


def test_snapshot_filters_types_and_no_trade_rows():
    rows = [{"stockSymbol": "A"}, {"stockSymbol": "CW1", "stockType": "w"},
            {"stockSymbol": "Z", "nmTotalTradedQty": 0}, {"stockSymbol": "Y", "openPrice": 0}]
    bars, idle = parse_snapshot(board(*rows), S1)
    assert [b.symbol for b in bars] == ["A"] and idle == ["Z", "Y"]


def test_snapshot_ref_is_none_when_the_board_has_none():
    bars, _ = parse_snapshot(board({"stockSymbol": "A"}, {"stockSymbol": "B", "refPrice": 0},
                                   {"stockSymbol": "C", "refPrice": 10}), S1)
    assert [b.ref for b in bars] == [None, None, 10]


def test_snapshot_unknown_turnover_stays_none():
    bars, _ = parse_snapshot(board({"stockSymbol": "A", "nmTotalTradedValue": None}), S1)
    assert len(bars) == 1 and bars[0].value is None


def test_snapshot_other_session_is_no_longer_served():
    with pytest.raises(SourceNoLongerServes) as e:
        parse_snapshot(hose(), date(2026, 10, 17), exchange="HOSE")
    assert e.value.served_date == S1


@pytest.mark.parametrize("bad", [{"highest": 10}, {"lowest": 12}, {"matchedPrice": None}])
def test_snapshot_inconsistent_row_is_shape_error(bad):
    with pytest.raises(PayloadShapeError):
        parse_snapshot(board({"stockSymbol": "A", **bad}), S1)


def fetcher(handler, tmp_path) -> Fetcher:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Fetcher(client, {"ssi": TokenBucket(100)}, Archive(tmp_path), "ua")


def test_snapshot_bars_three_requests_archive_and_replay(tmp_path):
    seen = []

    def handler(req):
        seen.append(req.url.path)
        return httpx.Response(200, content=hose())

    f = fetcher(handler, tmp_path)
    first = SsiSource(f).snapshot_bars(S1)
    assert seen == ["/stock/exchange/hose", "/stock/exchange/hnx", "/stock/exchange/upcom"]
    assert (tmp_path / "bars_1d/2026-10-16/board-hose.json.gz").exists()
    assert SsiSource(f).snapshot_bars(S1) == first and len(seen) == 3  # replay: 0 requests


def test_snapshot_mismatch_is_not_archived(tmp_path):
    f = fetcher(lambda r: httpx.Response(200, content=hose()), tmp_path)
    with pytest.raises(SourceNoLongerServes):
        SsiSource(f).snapshot_bars(date(2026, 10, 17))
    assert not (tmp_path / "bars_1d/2026-10-17/board-hose.json.gz").exists()
