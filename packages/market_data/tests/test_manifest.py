import hashlib
from dataclasses import replace
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from finvest_market_data.domain.manifest import Manifest, canonical_line, checksum, dedupe
from finvest_market_data.domain.models import Bar, Tick

TS = datetime(2026, 10, 15, 7, 45, 8, 160000, tzinfo=UTC)
VN = ZoneInfo("Asia/Ho_Chi_Minh")


def tick(seq: int, price: int = 58000, ts: datetime = TS, side: str | None = None) -> Tick:
    return Tick("FPT", ts, seq, price, 100, side, "kbs")  # type: ignore[arg-type]


def test_checksum_matches_independent_sha256_and_ignores_order() -> None:
    a, b = tick(1234500), tick(1234600)
    lines = [
        "FPT,2026-10-15T07:45:08.160000+00:00,1234500,58000,100,\n",
        "FPT,2026-10-15T07:45:08.160000+00:00,1234600,58000,100,\n",
    ]
    want = "sha256:" + hashlib.sha256("".join(lines).encode()).hexdigest()
    assert checksum([a, b]) == want == checksum([b, a])


def test_canonical_line_side() -> None:
    assert canonical_line(tick(1, side="B")).endswith(",100,B")


def test_dedupe_keeps_last_and_returns_displaced() -> None:
    first, other, last = tick(1, 58000), tick(2), tick(1, 58100)
    kept, displaced = dedupe([first, other, last])
    assert kept == [last, other]
    assert displaced == [first]


def test_non_utc_ts_rejected() -> None:
    with pytest.raises(ValueError):
        tick(1, ts=datetime(2026, 10, 15, 7, 0))
    with pytest.raises(ValueError):
        tick(1, ts=TS.astimezone(VN))


def test_tick_and_bar_validation() -> None:
    with pytest.raises(ValueError):
        replace(tick(1), price=0)
    with pytest.raises(ValueError):
        replace(tick(1), volume=-1)
    with pytest.raises(ValueError):
        Bar("FPT", TS, 1, 1, 0, 1, 1, None, "vci")


def test_manifest_to_dict_keys_and_vn_time() -> None:
    t = datetime(2026, 10, 15, 8, 20, 3, tzinfo=UTC)
    m = Manifest(
        "ticks", date(2026, 10, 15), "kbs", t, t, "partial", None, 2, 3, "sha256:x", 1,
        (("ABC", "http_429"),), ("XYZ",), "cli:--only", t, 1,
    )
    d = m.to_dict()
    assert list(d) == [
        "feed", "trading_date", "source", "started_at", "finished_at", "status", "reason", "requests",
        "rows", "checksum", "symbols_fetched", "symbols_no_trades", "symbols_skipped", "universe",
    ]
    assert d["started_at"] == "2026-10-15T15:20:03+07:00"
    assert d["symbols_no_trades"] == ["XYZ"]
    assert d["symbols_skipped"] == [{"symbol": "ABC", "reason": "http_429"}]
    assert d["universe"] == {"source": "cli:--only", "as_of": "2026-10-15T15:20:03+07:00", "count": 1}
