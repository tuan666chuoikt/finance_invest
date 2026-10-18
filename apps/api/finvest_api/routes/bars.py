from datetime import date

from fastapi import APIRouter, Depends
from finvest_market_data.infrastructure.tables import bars_1d_src as b
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from ..deps import get_engine, vn_iso

router = APIRouter(prefix="/api")


class BarsStatus(BaseModel):
    last_trading_date: date | None
    as_of: str | None
    source: str
    symbols: int


@router.get("/bars/1d/status", response_model=BarsStatus)
def bars_status(engine: Engine = Depends(get_engine)):
    with engine.connect() as c:
        last, at, n = c.execute(
            select(
                func.max(b.c.trading_date), func.max(b.c.fetched_at), func.count(func.distinct(b.c.symbol))
            )
        ).one()
    return {"last_trading_date": last, "as_of": vn_iso(at), "source": "vci", "symbols": n}
