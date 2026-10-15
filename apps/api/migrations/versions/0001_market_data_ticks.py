"""ticks hypertable, crawl_runs, crawl_sessions, data_anomalies (data.md §3, ADR-S-001)

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute(
        """
        CREATE TABLE ticks (
            symbol text NOT NULL,
            ts timestamptz NOT NULL,
            seq bigint NOT NULL,
            price bigint NOT NULL,
            volume bigint NOT NULL,
            side char(1),
            source text NOT NULL,
            PRIMARY KEY (symbol, ts, seq),
            CONSTRAINT ticks_side_check CHECK (side IN ('B','S'))
        )
        """
    )
    op.execute("SELECT create_hypertable('ticks', 'ts', chunk_time_interval => interval '1 day')")
    op.execute(
        "ALTER TABLE ticks SET (timescaledb.compress, timescaledb.compress_segmentby = 'symbol', "
        "timescaledb.compress_orderby = 'ts, seq')"
    )
    op.execute("SELECT add_compression_policy('ticks', interval '1 day')")

    op.create_table(
        "crawl_runs",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("feed", sa.Text, nullable=False),
        sa.Column("trading_date", sa.Date, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text),
        sa.Column("reason", sa.Text),
        sa.Column("requests", sa.Integer),
        sa.Column("rows", sa.BigInteger),
        sa.Column("manifest_path", sa.Text),
    )
    op.create_table(
        "crawl_sessions",
        sa.Column("feed", sa.Text, primary_key=True),
        sa.Column("trading_date", sa.Date, primary_key=True),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("symbols_fetched", sa.Integer),
        sa.Column("symbols_skipped", sa.Integer),
        sa.Column("rows", sa.BigInteger),
        sa.Column("checksum", sa.Text),
        sa.Column("reason", sa.Text),
    )
    op.create_table(
        "data_anomalies",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("symbol", sa.Text),
        sa.Column("trading_date", sa.Date),
        sa.Column("rule", sa.Text, nullable=False),
        sa.Column("value", sa.Text),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for t in ("data_anomalies", "crawl_sessions", "crawl_runs", "ticks"):
        op.execute(f"DROP TABLE IF EXISTS {t}")
