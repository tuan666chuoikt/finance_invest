"""VCI payloads (data.md §1.2 V2, V3), recorded 2026-10-15.

V3 `GET https://trading.vietcap.com.vn/api/price/symbols/getAll`: a bare JSON list, 3,683 rows. Fields used:
- `symbol`     ticker
- `board`      `HSX|HNX|UPCOM|DELISTED|BOND`; NO `delisted` flag: delisted = `board == "DELISTED"`
- `type`       `STOCK|ETF|CW|BOND|FU|UNIT_TRUST|DEBENTURE`
- `organName` / `enOrganName`  Vietnamese / English name (null on some rows)
- `icbCode2`   ICB level-2 code (null on ~52 % of rows)
Ignored: `id`, `sid`, `enOrganShortName`, `organShortName`, `productGrpID`.

V2 `POST .../api/chart/OHLCChart/gap-chart`: a list with one column-oriented object per requested symbol:
`{"symbol", "o","h","l","c","v","t", "accumulatedVolume", "accumulatedValue", "minBatchTruncTime"}`.
`o/h/l/c` are JSON numbers (VND, source-adjusted so floats like 65182.47 occur), `v` shares,
`t` epoch seconds as STRINGS at 00:00 UTC of the trading day.
`accumulatedValue` is nominal traded value in MIXED units: million VND on most bars (474,963.63 on a
6,618,016-share day; VN30 2026-10-16 = 6,386,472.73) but raw VND on old bars (VN30 2012-02-06 =
222,242,000,000); null on some old bars. The adapter picks the unit per bar (`source._value_vnd`).
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from finvest_market_data.domain.ports import PayloadShapeError
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError


class VciSymbol(BaseModel):
    model_config = ConfigDict(extra="allow")
    symbol: str
    board: str
    type: str
    organName: str | None = None
    enOrganName: str | None = None
    icbCode2: str | None = None


class VciMember(BaseModel):
    model_config = ConfigDict(extra="allow")
    symbol: str


class VciBars(BaseModel):
    model_config = ConfigDict(extra="allow")
    symbol: str
    o: list[Decimal]
    h: list[Decimal]
    l: list[Decimal]  # noqa: E741 - OHLC convention
    c: list[Decimal]
    v: list[int]
    t: list[int]
    accumulatedValue: list[Decimal | None]  # mixed: million or raw VND; null on old bars


class VciEvent(BaseModel):
    """V5 event (data.md §1.2 V5); dates are `YYYY-MM-DDT00:00:00` strings."""

    model_config = ConfigDict(extra="allow")
    id: str
    ticker: str
    eventCode: str
    eventTitleVi: str = ""
    publicDate: datetime | None = None
    recordDate: datetime | None = None
    exrightDate: datetime | None = None
    payoutDate: datetime | None = None  # cash only
    valuePerShare: Decimal | None = None  # cash only, VND
    exerciseRatio: Decimal | None = None


class VciEventsData(BaseModel):
    model_config = ConfigDict(extra="allow")
    content: list[VciEvent]
    last: bool


class VciEventsPage(BaseModel):
    """V5 envelope. HTTP 200 with `status 400` ("Invalid datetime") has no `data`: fails here, loudly."""

    model_config = ConfigDict(extra="allow")
    data: VciEventsData


def validate[T](adapter: TypeAdapter[T], payload: bytes, raw_path: Path, source: str = "vci") -> T:
    """Fail loudly (ADR-S-002): the error names the archived raw payload."""
    try:
        return adapter.validate_json(payload)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(x) for x in first["loc"])
        raise PayloadShapeError(f"{source} payload shape changed at {loc}: {first['msg']}", raw_path) from e
