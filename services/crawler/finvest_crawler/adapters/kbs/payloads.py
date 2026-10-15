"""KBS tick-tape payload (data.md §1.2 K1), observed 2026-10-15 on FPT.

`GET https://kbbuddywts.kbsec.com.vn/iis-server/investment/trade/history/{SYM}?page=1&limit=50000` returns
`{"data": [row, ...]}` for the CURRENT session only (`?date=` is ignored), newest row first, one call per day.
An empty tape is `{"data": []}` with HTTP 200. Row fields we use (all JSON integers except `t` and `LC`):

- `t`   local time `YYYY-MM-DD HH:MM:SS:cc`, Asia/Ho_Chi_Minh, `cc` = centiseconds ("2026-10-15 14:45:07:44")
- `FMP` match price, VND (58000 = 58,000 VND, no scaling)
- `FV`  match volume, shares
- `AVO` accumulated volume, shares; unique per row and exactly the running sum of `FV` in chronological order,
        so it is the tick `seq`. Several rows share one `t`, so sort by `AVO`, never by `t` or array order.
- `LC`  side `"B"` / `"S"` / `""` (observed filled in the evening sample; `""` on the ATO/ATC auction prints)
Ignored: `TD` (dd/mm/yyyy), `SB`, `FT`, `FCV` (price change), `AVA` (accumulated value).
"""

from pathlib import Path
from typing import Literal

from finvest_market_data.domain.ports import PayloadShapeError
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidationError


class KbsRow(BaseModel):
    t: StrictStr = Field(pattern=r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d:\d\d$")
    FMP: StrictInt = Field(gt=0)
    FV: StrictInt = Field(ge=0)
    AVO: StrictInt = Field(ge=0)
    LC: Literal["B", "S", ""]


class KbsEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[KbsRow]


def validate_envelope(payload: bytes, raw_path: Path) -> KbsEnvelope:
    """Fail loudly (ADR-S-002): the error names the archived raw payload."""
    try:
        return KbsEnvelope.model_validate_json(payload)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(x) for x in first["loc"])
        raise PayloadShapeError(f"kbs payload shape changed at {loc}: {first['msg']}", raw_path) from e


