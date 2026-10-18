from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, MetaData, String, Table

metadata = MetaData()  # separate from market data: user data, own lifecycle

scenarios = Table(
    "scenarios",
    metadata,
    # Integer variant so SQLite tests autoincrement; Postgres uses the migration's identity column
    Column("id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True),
    Column("name", String, nullable=False),
    Column("symbol", String, nullable=False),
    Column("style", String, nullable=False),
    Column("amount_vnd", BigInteger, nullable=False),
    Column("buy_date", Date, nullable=False),
    Column("sell_date", Date),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
