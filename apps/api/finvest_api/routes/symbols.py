from datetime import date

from fastapi import APIRouter, Depends, Query
from finvest_market_data.infrastructure.tables import bars_1d_src, symbols
from pydantic import BaseModel
from sqlalchemy import case, func, or_, select
from sqlalchemy.engine import Engine

from ..deps import get_engine, vn_iso
from ..errors import ApiError

router = APIRouter(prefix="/api")


class SymbolOut(BaseModel):
    symbol: str
    exchange: str
    type: str
    name_vi: str
    name_en: str
    delisted_at: date | None


class BarsRange(BaseModel):
    first: date
    last: date
    as_of: str


class SymbolDetail(SymbolOut):
    bars_1d: BarsRange | None


_COLS = [symbols.c[n] for n in ("symbol", "exchange", "type", "name_vi", "name_en", "delisted_at")]


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


@router.get("/symbols", response_model=list[SymbolOut])
def list_symbols(
    q: str = "",
    limit: int = Query(20, ge=1, le=200),
    include_delisted: bool = False,
    engine: Engine = Depends(get_engine),
):
    stmt = select(*_COLS).order_by(symbols.c.symbol).limit(limit)
    if not include_delisted:
        stmt = stmt.where(symbols.c.is_delisted.is_(False))
    if q := q.strip():
        pat = _like(q)
        # exact symbol match first; the order must precede limit, so rebuild it here
        stmt = stmt.order_by(None).order_by(
            case((symbols.c.symbol == q.upper(), 0), else_=1), symbols.c.symbol
        )
        stmt = stmt.where(
            or_(
                symbols.c.symbol.like(pat[1:].upper(), escape="\\"),  # prefix: drop the leading %
                symbols.c.name_vi.ilike(pat, escape="\\"),
                symbols.c.name_en.ilike(pat, escape="\\"),
            )
        )
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(stmt)]


@router.get("/symbols/{symbol}", response_model=SymbolDetail)
def get_symbol(symbol: str, engine: Engine = Depends(get_engine)):
    sym = symbol.upper()
    b = bars_1d_src.c
    with engine.connect() as c:
        row = c.execute(select(*_COLS).where(symbols.c.symbol == sym)).first()
        if row is None:
            raise ApiError("NOT_FOUND", 404, f"unknown symbol {sym}", {"symbol": sym})
        lo, hi, at = c.execute(
            select(func.min(b.trading_date), func.max(b.trading_date), func.max(b.fetched_at)).where(
                b.symbol == sym
            )
        ).one()
    rng = {"first": lo, "last": hi, "as_of": vn_iso(at)} if lo else None
    return {**row._mapping, "bars_1d": rng}
