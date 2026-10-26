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
    UniqueConstraint,
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
    Column("ca_checked_at", TZ),  # S05 (migration 0010): last V5 corporate-action read
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

# nominal daily bar (never adjusted, data.md §1.4 (1)); an observed row is never replaced by a reconstruction
bars_1d = Table(
    "bars_1d",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("trading_date", Date, primary_key=True),
    Column("o", BigInteger, nullable=False),
    Column("h", BigInteger, nullable=False),
    Column("l", BigInteger, nullable=False),
    Column("c", BigInteger, nullable=False),
    Column("ref", BigInteger),  # exchange reference price on the day; NULL when reconstructed
    Column("ceiling", BigInteger),
    Column("floor", BigInteger),
    Column("v", BigInteger, nullable=False),
    Column("value", BigInteger),
    Column("nominal_kind", Text, nullable=False),
    Column("source", Text, nullable=False),  # ssi|vci
    Column("fetched_at", TZ, nullable=False),
    CheckConstraint("nominal_kind IN ('observed','reconstructed')", name="bars_1d_nominal_kind_check"),
)

corporate_actions = Table(
    "corporate_actions",
    metadata,
    Column("id", BigInteger, Identity(), primary_key=True),
    Column("symbol", Text, nullable=False),
    Column("type", Text, nullable=False),  # cash_dividend|stock_dividend|rights|split|merge|listing_change
    Column("ex_date", Date),
    Column("record_date", Date),
    Column("pay_date", Date),
    Column("public_date", Date),
    Column("title", Text),  # raw eventTitleVi
    Column("ratio_a", Integer),
    Column("ratio_b", Integer),
    Column("cash_per_share", BigInteger),  # VND
    Column("issue_price", BigInteger),
    Column("source", Text, nullable=False),
    Column("source_event_id", Text, nullable=False),
    Column("fetched_at", TZ, nullable=False),
    UniqueConstraint("source", "source_event_id", name="corporate_actions_source_event_key"),
)

corporate_action_log = Table(
    "corporate_action_log",
    metadata,
    Column("id", BigInteger, Identity(), primary_key=True),
    Column("ca_id", BigInteger, nullable=False),
    Column("changed_at", TZ, nullable=False),
    Column("field", Text, nullable=False),
    Column("old", Text),
    Column("new", Text),
)

adj_factors = Table(
    "adj_factors",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("ex_date", Date, primary_key=True),
    Column("factor", Numeric(20, 12), nullable=False),
    Column("ca_id", BigInteger),
    Column("rules_version", Text, nullable=False),
)

recon_mismatches = Table(
    "recon_mismatches",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("trading_date", Date, primary_key=True),
    Column("ours", BigInteger, nullable=False),
    Column("theirs", BigInteger, nullable=False),
    Column("diff_pct", Numeric(8, 4), nullable=False),
    Column("checked_at", TZ, nullable=False),
)
