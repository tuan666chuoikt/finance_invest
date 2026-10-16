"""SQLAlchemy Core tables for the market-data store (data.md §3). Core only, no ORM (ADR-S-001)."""

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    Identity,
    Integer,
    MetaData,
    Table,
    Text,
    func,
)
from sqlalchemy import DateTime as _DT

metadata = MetaData()
TZ = _DT(timezone=True)

# hypertable on ts (1-day chunks, migration 0001); seq = KBS accumulated volume or VCI id (ADR-S-008)
ticks = Table(
    "ticks",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("ts", TZ, primary_key=True),
    Column("seq", BigInteger, primary_key=True),
    Column("price", BigInteger, nullable=False),  # integer VND
    Column("volume", BigInteger, nullable=False),
    Column("side", CHAR(1)),
    Column("source", Text, nullable=False),
    CheckConstraint("side IN ('B','S')", name="ticks_side_check"),
)

crawl_runs = Table(
    "crawl_runs",
    metadata,
    Column("id", BigInteger, Identity(), primary_key=True),
    Column("feed", Text, nullable=False),
    Column("trading_date", Date, nullable=False),
    Column("started_at", TZ, nullable=False),
    Column("finished_at", TZ),
    Column("status", Text),  # ok|partial|failed|blocked|missed
    Column("reason", Text),
    Column("requests", Integer),
    Column("rows", BigInteger),
    Column("manifest_path", Text),
)

crawl_sessions = Table(
    "crawl_sessions",
    metadata,
    Column("feed", Text, primary_key=True),
    Column("trading_date", Date, primary_key=True),
    Column("status", Text, nullable=False),
    Column("symbols_fetched", Integer),
    Column("symbols_no_trades", Integer),
    Column("symbols_skipped", Integer),
    Column("rows", BigInteger),
    Column("checksum", Text),
    Column("reason", Text),
)

data_anomalies = Table(
    "data_anomalies",
    metadata,
    Column("id", BigInteger, Identity(), primary_key=True),
    Column("symbol", Text),
    Column("trading_date", Date),
    Column("rule", Text, nullable=False),
    Column("value", Text),
    Column("detected_at", TZ, nullable=False, server_default=func.now()),
    Column("resolved_at", TZ),
)
