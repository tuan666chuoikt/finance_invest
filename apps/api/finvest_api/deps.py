import os
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

VN = ZoneInfo("Asia/Ho_Chi_Minh")


@lru_cache
def get_engine() -> Engine:
    url = os.environ.get("FINVEST_DATABASE_URL", "postgresql+psycopg://finvest:finvest@localhost:5432/finvest")
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def vn_iso(ts: datetime | None) -> str | None:
    """ISO-8601 in Asia/Ho_Chi_Minh (ADR-S-006); a naive value (SQLite) is taken as UTC."""
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=ZoneInfo("UTC"))
    return ts.astimezone(VN).isoformat(timespec="milliseconds")
