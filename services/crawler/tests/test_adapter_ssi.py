import gzip
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.ssi import SsiSource
from finvest_crawler.adapters.ssi.source import parse_bars
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_market_data.domain.ports import PayloadShapeError, Unsupported

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
    for call in (lambda: src.symbols(D), lambda: src.ticks("FPT", D), lambda: src.bars(["FPT"], "1m", D, 1)):
        with pytest.raises(Unsupported):
            call()
