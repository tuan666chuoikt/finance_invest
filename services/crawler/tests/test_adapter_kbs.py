import gzip
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.kbs import KbsSource, parse_ticks
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher
from finvest_crawler.ratelimit import TokenBucket
from finvest_market_data.domain.ports import PayloadShapeError, SourceNoLongerServes, Unsupported

FIX = Path(__file__).parent / "fixtures/kbs/trade_history"
D = date(2026, 10, 15)


def load(name: str) -> bytes:
    return gzip.decompress((FIX / name).read_bytes())


def payload(*rows: dict) -> bytes:
    return json.dumps({"data": list(rows)}).encode()


def row(t="2026-10-15 14:45:08:16", fmp=58000, fv=100, avo=1234500, lc=""):
    return {"t": t, "FMP": fmp, "FV": fv, "AVO": avo, "LC": lc, "SB": "FPT", "extra": 1}


def test_fixture_parses_sorted_by_seq():
    ticks = parse_ticks(load("FPT-2026-10-15.json.gz"), "FPT", D)
    assert len(ticks) == 50
    assert all(a.seq < b.seq for a, b in zip(ticks, ticks[1:], strict=False))
    assert ticks[-1].ts == datetime(2026, 10, 15, 7, 45, 7, 440000, tzinfo=UTC)  # 14:45:07:44 local
    assert ticks[-1].side is None and ticks[-1].source == "kbs"  # ATC print has LC ""


def test_row_normalisation():
    (t,) = parse_ticks(payload(row()), "FPT", D)
    assert t.ts == datetime(2026, 10, 15, 7, 45, 8, 160000, tzinfo=UTC)
    assert (t.price, t.volume, t.seq, t.side) == (58000, 100, 1234500, None)
    assert parse_ticks(payload(row(lc="B")), "FPT", D)[0].side == "B"


def test_rows_sorted_by_avo_not_by_time():
    a = row(t="2026-10-15 14:00:00:00", avo=200, lc="S")
    b = row(t="2026-10-15 14:00:00:00", avo=100, lc="B")  # same t, array order is not seq order
    assert [t.seq for t in parse_ticks(payload(a, b), "FPT", D)] == [100, 200]


def test_other_session_raises_with_served_date():
    with pytest.raises(SourceNoLongerServes) as e:
        parse_ticks(load("FPT-2026-10-15.json.gz"), "FPT", date(2026, 10, 14))
    assert e.value.served_date == D


def test_empty_tape_raises():
    with pytest.raises(SourceNoLongerServes) as e:
        parse_ticks(load("empty.json.gz"), "FPT", D)
    assert e.value.served_date is None


def test_renamed_field_names_archive_path():
    bad = load("FPT-2026-10-15.json.gz").replace(b'"FMP"', b'"PRICE"')
    with pytest.raises(PayloadShapeError, match="FMP") as e:
        parse_ticks(bad, "FPT", D, Path("/arch/ticks/2026-10-15/FPT.json.gz"))
    assert e.value.raw_path == Path("/arch/ticks/2026-10-15/FPT.json.gz")


@pytest.mark.parametrize("bad", [row(fmp=0), row(lc="X"), row(fmp=58000.5), row(t="15/10/2026")])
def test_bad_values_are_shape_errors(bad):
    with pytest.raises(PayloadShapeError):
        parse_ticks(payload(bad), "FPT", D)


def test_not_json_is_shape_error():
    with pytest.raises(PayloadShapeError):
        parse_ticks(b"<html>", "FPT", D)


def test_source_requests_exactly_k1_url_and_archives(tmp_path):
    seen = []

    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200, content=load("FPT-2026-10-15.json.gz"))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    f = Fetcher(client, {"kbs": TokenBucket(100)}, Archive(tmp_path), "ua")
    src = KbsSource(f)
    assert len(src.ticks("FPT", D)) == 50
    assert seen == ["https://kbbuddywts.kbsec.com.vn/iis-server/investment/trade/history/FPT?page=1&limit=50000"]
    assert (tmp_path / "ticks/2026-10-15/FPT.json.gz").exists()
    with pytest.raises(Unsupported):
        src.symbols(D)
    with pytest.raises(Unsupported):
        src.bars(["FPT"], "1d", D, 1)


def _src(tmp_path, body):
    h = lambda req: httpx.Response(200, content=body)  # noqa: E731
    client = httpx.Client(transport=httpx.MockTransport(h))
    f = Fetcher(client, {"kbs": TokenBucket(100)}, Archive(tmp_path), "ua")
    return KbsSource(f), f


@pytest.mark.parametrize("body,d", [(b'{"data":[]}', D), (payload(row()), date(2026, 10, 14))])
def test_rejected_tape_is_never_archived(tmp_path, body, d):
    src, f = _src(tmp_path, body)
    with pytest.raises(SourceNoLongerServes):
        src.ticks("FPT", d)
    assert not f.archive.path("ticks", d, "FPT").exists()


def test_accepted_tape_written_once_then_replayed(tmp_path):
    src, f = _src(tmp_path, load("FPT-2026-10-15.json.gz"))
    src.ticks("FPT", D)
    p = f.archive.path("ticks", D, "FPT")
    m = p.stat().st_mtime_ns
    assert len(src.ticks("FPT", D)) == 50
    assert (f.requests, f.replays, p.stat().st_mtime_ns) == (1, 1, m)
