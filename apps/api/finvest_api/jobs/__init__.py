from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, MetaData, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()  # own lifecycle, like scenarios

_json = JSON().with_variant(JSONB, "postgresql")

jobs = Table(
    "jobs",
    metadata,
    Column("id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True),
    Column("kind", String, nullable=False),
    Column("args", _json, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True)),
    Column("progress", _json),
    Column("summary", _json),
    Column("error", _json),
    Column("log", Text),
)
