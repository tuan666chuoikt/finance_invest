"""SSI iBoard payload (data.md §1.2 S2), recorded 2026-10-15.

`GET https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D&symbol=FPT&from=<epoch>&to=<epoch>`
returns `{"code", "message", "status", "data": {"t","o","h","l","c","v","s","nextTime"}}`: column arrays,
`t` epoch seconds (int) at 00:00 UTC of the trading day,
`o/h/l/c` in THOUSAND VND (58 = 58,000 VND; 58.1 = 58,100), `v` shares,
`s` is `"ok"` or `"no_data"` (arrays then absent). Prices are source-adjusted like V2.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SsiHistory(BaseModel):
    model_config = ConfigDict(extra="allow")
    s: str
    t: list[int] = []
    o: list[Decimal] = []
    h: list[Decimal] = []
    l: list[Decimal] = []  # noqa: E741 - OHLC convention
    c: list[Decimal] = []
    v: list[int] = []


class SsiEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: SsiHistory


class SsiRow(BaseModel):
    """S1 row (data.md §1.2); `firstTradingDate` is a `yyyymmdd` string, "0" when unknown."""

    model_config = ConfigDict(extra="allow")
    stockSymbol: str
    stockType: str
    companyNameVi: str | None = None
    companyNameEn: str | None = None
    firstTradingDate: str | None = None


class SsiExchange(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[SsiRow]
