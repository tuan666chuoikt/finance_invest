"""SQLAlchemy Core tables for the market-data store (data.md §3). Core only, no ORM (ADR-S-001)."""

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Identity,
    Integer,
    MetaData,
    Numeric,
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

symbols = Table(
    "symbols",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("exchange", Text, nullable=False),
    Column("type", Text, nullable=False),  # STOCK|ETF
    Column("name_vi", Text, nullable=False),
    Column("name_en", Text, nullable=False),
    Column("icb_code2", Text),
    Column("listed_at", Date),
    Column("delisted_at", Date),
    Column("is_delisted", Boolean, nullable=False, server_default="false"),
    Column("source", Text, nullable=False),
    Column("fetched_at", TZ, nullable=False),
    CheckConstraint("exchange IN ('HOSE','HNX','UPCOM')", name="symbols_exchange_check"),
    CheckConstraint("type IN ('STOCK','ETF')", name="symbols_type_check"),
)

# current + history of index constituents; history starts at crawl start (V6 has no past)
symbol_index_membership = Table(
    "symbol_index_membership",
    metadata,
    Column("index_code", Text, primary_key=True),
    Column("symbol", Text, primary_key=True),
    Column("valid_from", Date, primary_key=True),
    Column("valid_to", Date),
)

# versioned snapshots of the source-adjusted series (data.md §1.4 (2)); value = nominal VND
bars_1d_src = Table(
    "bars_1d_src",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("trading_date", Date, primary_key=True),
    Column("source", Text, primary_key=True),
    Column("fetched_at", TZ, primary_key=True),
    Column("adj_o", BigInteger, nullable=False),
    Column("adj_h", BigInteger, nullable=False),
    Column("adj_l", BigInteger, nullable=False),
    Column("adj_c", BigInteger, nullable=False),
    Column("v", BigInteger, nullable=False),
    Column("value", BigInteger),
)

index_1d = Table(
    "index_1d",
    metadata,
    Column("index_code", Text, primary_key=True),
    Column("trading_date", Date, primary_key=True),
    Column("o", Numeric(12, 2), nullable=False),
    Column("h", Numeric(12, 2), nullable=False),
    Column("l", Numeric(12, 2), nullable=False),
    Column("c", Numeric(12, 2), nullable=False),
    Column("v", BigInteger, nullable=False),
    Column("value", BigInteger),
)
