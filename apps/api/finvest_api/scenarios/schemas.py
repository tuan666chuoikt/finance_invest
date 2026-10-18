from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, ValidationInfo, field_validator


class ScenarioIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    symbol: Annotated[
        str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=12)
    ]
    style: Literal["lump_sum", "dca"]
    amount_vnd: int = Field(strict=True, ge=1, le=100_000_000_000)  # no floats / strings
    buy_date: date
    sell_date: date | None = None

    @field_validator("sell_date")
    @classmethod
    def _after_buy(cls, v: date | None, info: ValidationInfo):
        buy = info.data.get("buy_date")
        if v is not None and buy is not None and v < buy:
            raise ValueError("sell_date must be on or after buy_date")
        return v


class Scenario(ScenarioIn):
    id: int
    created_at: str
    updated_at: str
