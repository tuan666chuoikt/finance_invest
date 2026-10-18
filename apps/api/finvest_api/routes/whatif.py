from fastapi import APIRouter, Depends
from finvest_analytics.domain.models import WhatIfRequest
from finvest_analytics.domain.ports import MarketView
from finvest_analytics.sim import run_whatif
from sqlalchemy.engine import Engine

from ..deps import get_engine
from ..market_view import SqlMarketView

router = APIRouter(prefix="/api")


def get_market_view(engine: Engine = Depends(get_engine)) -> MarketView:
    return SqlMarketView(engine)  # one per request: snapshot() covers only the bars it served


@router.post("/whatif")
def whatif(req: WhatIfRequest, view: MarketView = Depends(get_market_view)) -> dict:
    # sync def: FastAPI runs it in the threadpool, so the blocking SQL does not stall the loop
    return run_whatif(req, view)
