from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from finvest_market_data.infrastructure.tables import symbols
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine

from ..deps import get_engine, vn_iso
from ..errors import ApiError
from ..scenarios.schemas import Scenario, ScenarioIn
from ..scenarios.tables import scenarios as t

router = APIRouter(prefix="/api")


def _out(row) -> dict:
    d = dict(row._mapping)
    d["created_at"], d["updated_at"] = vn_iso(d["created_at"]), vn_iso(d["updated_at"])
    return d


def _check_symbol(c, sym: str) -> None:
    if c.execute(select(symbols.c.symbol).where(symbols.c.symbol == sym)).first() is None:  # delisted allowed
        raise ApiError("SYMBOL_UNKNOWN", 422, f"unknown symbol {sym}", {"symbol": sym})


def _not_found(id: int) -> ApiError:
    return ApiError("NOT_FOUND", 404, f"unknown scenario {id}", {"id": id})


@router.get("/scenarios", response_model=list[Scenario])
def list_scenarios(engine: Engine = Depends(get_engine)):
    with engine.connect() as c:
        rows = c.execute(select(t).order_by(t.c.created_at.desc(), t.c.id.desc()))
        return [_out(r) for r in rows]


@router.post("/scenarios", response_model=Scenario, status_code=201)
def create_scenario(body: ScenarioIn, engine: Engine = Depends(get_engine)):
    now = datetime.now(UTC)
    with engine.begin() as c:
        _check_symbol(c, body.symbol)
        vals = dict(**body.model_dump(), created_at=now, updated_at=now)
        row = c.execute(insert(t).values(**vals).returning(t)).one()
    return _out(row)


@router.put("/scenarios/{id}", response_model=Scenario)
def replace_scenario(id: int, body: ScenarioIn, engine: Engine = Depends(get_engine)):
    with engine.begin() as c:
        _check_symbol(c, body.symbol)
        vals = dict(**body.model_dump(), updated_at=datetime.now(UTC))
        row = c.execute(update(t).where(t.c.id == id).values(**vals).returning(t)).first()
    if row is None:
        raise _not_found(id)
    return _out(row)


@router.delete("/scenarios/{id}", status_code=204)
def delete_scenario(id: int, engine: Engine = Depends(get_engine)):
    with engine.begin() as c:
        if c.execute(delete(t).where(t.c.id == id)).rowcount == 0:
            raise _not_found(id)
    return Response(status_code=204)
