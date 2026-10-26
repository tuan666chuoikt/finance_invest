"""VCI IQ corporate events (data.md §1.2 V5, §3; VN§6): pure parse plus paged fetch. No DB, no budget."""

import re
import unicodedata
from datetime import date, datetime, timedelta
from fractions import Fraction
from pathlib import Path

from finvest_market_data.domain.models import CorporateAction
from pydantic import TypeAdapter

from finvest_crawler.adapters.vci.payloads import VciEvent, VciEventsPage, validate
from finvest_crawler.fetch import Fetcher

URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/events"
FROM_DATE = "20100101"
MAX_PAGES = 40  # shortcut: runaway guard (50 x 40 events per symbol), raise if a symbol ever needs more
_PAGE = TypeAdapter(VciEventsPage)
_PRICE = re.compile(r"giá\s+(\d{1,3}(?:[.,]\d{3})+|\d+)\s*đồng")
Anomaly = tuple[str, str]  # (source_event_id, rule)


def _d(x: datetime | None) -> date | None:
    return x.date() if x else None


def _ratio(r) -> tuple[int, int] | tuple[None, None]:
    """exerciseRatio r = b/a -> (a, b): 0.1 -> (10, 1), 0.15 -> (20, 3)."""
    if r is None or r <= 0:
        return None, None
    f = Fraction(r).limit_denominator(1000)
    return (f.denominator, f.numerator) if f.numerator else (None, None)


def _map(e: VciEvent) -> tuple[str | None, int | None]:
    """-> (type or None if unmapped, issue_price)."""
    title = unicodedata.normalize("NFC", e.eventTitleVi).casefold()
    if e.eventCode == "DIV":
        if e.valuePerShare is not None or "cổ tức bằng cổ phiếu" not in title:
            return "cash_dividend", None  # without valuePerShare: amount missing, flagged by the caller
        return "stock_dividend", None
    if e.eventCode == "ISS":
        if "thưởng" in title:
            return "stock_dividend", None
        if "cbcnv" in title or "esop" in title:
            return "listing_change", None
        if "quyền mua" in title or "phát hành thêm" in title:
            m = _PRICE.search(title)
            return "rights", int(re.sub(r"[.,]", "", m.group(1))) if m else None
    return None, None


def parse_events(
    payload: bytes, raw_path: Path = Path("<unarchived>")
) -> tuple[list[CorporateAction], list[Anomaly], bool]:
    """Pure: one V5 page -> (rows, (source_event_id, anomaly_rule), last page)."""
    page = validate(_PAGE, payload, raw_path, "vci_iq").data
    rows: list[CorporateAction] = []
    anomalies: list[Anomaly] = []
    for e in page.content:
        kind, price = _map(e)
        if kind is None or e.exrightDate is None:
            anomalies.append((e.id, "corporate_action_unmapped"))
            continue
        a, b = (None, None) if kind == "cash_dividend" else _ratio(e.exerciseRatio)
        cash = int(e.valuePerShare) if kind == "cash_dividend" and e.valuePerShare is not None else None
        missing = (cash is None) if kind == "cash_dividend" else (a is None and kind != "listing_change")
        if missing or (kind == "rights" and price is None):
            anomalies.append((e.id, "corporate_action_amount_missing"))  # row kept, the value stays NULL
        rows.append(CorporateAction(
            e.ticker, kind, e.exrightDate.date(), _d(e.recordDate), _d(e.payoutDate),  # type: ignore[arg-type]
            a, b, cash, price, "vci_iq", e.id, _d(e.publicDate), e.eventTitleVi))
    return rows, anomalies, page.last


def fetch_events(
    fetcher: Fetcher, symbol: str, run_date: date
) -> tuple[list[CorporateAction], list[Anomaly], int]:
    """All V5 pages of `symbol` (page 0.. until `last`); toDate is required by the source (data.md V5)."""
    rows: list[CorporateAction] = []
    anomalies: list[Anomaly] = []
    start = fetcher.requests
    to = run_date + timedelta(days=400)
    q = f"?ticker={symbol}&fromDate={FROM_DATE}&toDate={to:%Y%m%d}&eventCode=DIV,ISS"
    for page in range(MAX_PAGES):
        name, feed = f"{symbol}-p{page}", "corporate_actions"
        payload = fetcher.get("vci_iq", f"{URL}{q}&page={page}&size=50", feed=feed, trading_date=run_date,
                              name=name, archive=False)
        r, a, last = parse_events(payload, fetcher.archive.path(feed, run_date, name))
        fetcher.archive.write(feed, run_date, name, payload)  # only after the shape was accepted
        rows += r
        anomalies += a
        if last:
            break
    return rows, anomalies, fetcher.requests - start
