import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from finvest_crawler.adapters.vci.events import fetch_events, parse_events
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.ratelimit import TokenBucket
from finvest_market_data.domain.ports import PayloadShapeError

FIX = Path(__file__).parent / "fixtures/vci/events/FPT-2026.json"
RUN = date(2026, 10, 26)


def page(*events, last=True) -> bytes:
    return json.dumps({"status": 200, "data": {"content": list(events), "last": last}}).encode()


def ev(**over) -> dict:
    base = {"id": "x1", "ticker": "FPT", "eventCode": "DIV", "eventTitleVi": "",
            "publicDate": "2026-05-22T00:00:00", "recordDate": "2026-05-29T00:00:00",
            "exrightDate": "2026-05-28T00:00:00"}
    return {**base, **over}


def test_fixture_parses_to_four_rows():
    rows, anomalies, last = parse_events(FIX.read_bytes())
    assert anomalies == [] and last is True and len(rows) == 4
    by = {r.source_event_id: r for r in rows}
    cash = by["6a0fa234a6ca51ba73a2a0a0"]
    assert (cash.type, cash.cash_per_share, cash.ex_date, cash.pay_date, cash.public_date) == (
        "cash_dividend", 1000, date(2026, 5, 28), date(2026, 6, 10), date(2026, 5, 22))
    assert (cash.ratio_a, cash.ratio_b, cash.source, cash.symbol) == (None, None, "vci_iq", "FPT")
    bonus = by["69e6c30a9a7ad2360023b0c1"]
    assert (bonus.type, bonus.ratio_a, bonus.ratio_b, bonus.ex_date) == (
        "stock_dividend", 10, 1, date(2026, 9, 21))
    esop = [r for r in rows if r.type == "listing_change"]
    assert len(esop) == 2 and all(r.cash_per_share is None for r in esop)


def test_stock_dividend_by_title_and_neither():
    rows, anomalies, _ = parse_events(page(
        ev(id="a", eventTitleVi="Trả cổ tức bằng cổ phiếu tỉ lệ 15%", exerciseRatio=0.15),
        ev(id="b", eventTitleVi="Trả cổ tức - đợt 1")))
    a, b = rows
    assert (a.type, a.ratio_a, a.ratio_b) == ("stock_dividend", 20, 3)  # hand: 0.15 = 3/20
    assert (b.type, b.cash_per_share) == ("cash_dividend", None)
    assert anomalies == [("b", "corporate_action_amount_missing")]


def test_rights_price_forms_and_unparsed():
    t = "Phát hành thêm cổ phiếu tỉ lệ 20% giá {} đồng"
    rows, anomalies, _ = parse_events(page(
        *(ev(id=i, eventCode="ISS", eventTitleVi=t.format(p), exerciseRatio=0.2) for i, p in
          (("a", "10,000"), ("b", "10.000"), ("c", "15000"))),
        ev(id="d", eventCode="ISS", eventTitleVi="Quyền mua cổ phiếu", exerciseRatio=0.2)))
    assert [(r.type, r.issue_price, r.ratio_a, r.ratio_b) for r in rows] == [("rights", p, 5, 1) for p in
                                                                         (10000, 10000, 15000, None)]
    assert anomalies == [("d", "corporate_action_amount_missing")]


def test_unmapped_not_stored():
    rows, anomalies, last = parse_events(page(ev(id="u", eventCode="ISS", eventTitleVi="Chuyển sàn"),
                                              ev(id="v", exrightDate=None, valuePerShare=500), last=False))
    assert rows == [] and last is False
    assert anomalies == [("u", "corporate_action_unmapped"), ("v", "corporate_action_unmapped")]


def test_invalid_datetime_body_is_a_shape_error():
    with pytest.raises(PayloadShapeError):
        parse_events(b'{"status": 400, "exception": "Invalid datetime", "data": null}')


def make(tmp_path, responses):
    seen, it = [], iter(responses)

    def handler(req):
        seen.append(str(req.url))
        status, body = next(it)
        return httpx.Response(status, content=body)

    clock = lambda: 0.0  # noqa: E731
    f = Fetcher(httpx.Client(transport=httpx.MockTransport(handler)),
                {"vci_iq": TokenBucket(1000, clock=clock, sleep=lambda s: None)}, Archive(tmp_path), "ua",
                sleep=lambda s: None)
    return f, seen


def test_fetch_pages_until_last_and_archives(tmp_path):
    f, seen = make(tmp_path, [(200, page(ev(id="a", valuePerShare=1000), last=False)),
                              (200, page(ev(id="b", valuePerShare=2000)))])
    rows, anomalies, n = fetch_events(f, "FPT", RUN)
    assert [r.source_event_id for r in rows] == ["a", "b"] and anomalies == [] and n == 2
    assert all("toDate=20271130" in u and "fromDate=20100101" in u for u in seen)  # 2026-10-26 + 400 d
    assert "page=0&size=50" in seen[0] and "page=1&size=50" in seen[1]
    assert (tmp_path / "corporate_actions/2026-10-26/FPT-p1.json.gz").exists()
    assert fetch_events(f, "FPT", RUN)[2] == 0  # replay from the archive: no request


def test_bad_page_is_not_archived(tmp_path):
    f, _ = make(tmp_path, [(200, b'{"status": 400, "data": null}')])
    with pytest.raises(PayloadShapeError):
        fetch_events(f, "FPT", RUN)
    assert not (tmp_path / "corporate_actions/2026-10-26/FPT-p0.json.gz").exists()


def test_418_is_blocked_after_tries(tmp_path):
    f, seen = make(tmp_path, [(418, b"")] * 3)
    with pytest.raises(SourceBlocked) as e:
        fetch_events(f, "FPT", RUN)
    assert e.value.last_status == 418 and len(seen) == 3
