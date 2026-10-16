"""bars_1d_src (versioned source-adjusted daily bars) and index_1d (F-012, data.md §3)

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE bars_1d_src (
            symbol       TEXT NOT NULL,
            trading_date DATE NOT NULL,
            source       TEXT NOT NULL,
            fetched_at   TIMESTAMPTZ NOT NULL,
            adj_o        BIGINT NOT NULL,
            adj_h        BIGINT NOT NULL,
            adj_l        BIGINT NOT NULL,
            adj_c        BIGINT NOT NULL,
            v            BIGINT NOT NULL,
            value        BIGINT,
            PRIMARY KEY (symbol, trading_date, source, fetched_at)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE index_1d (
            index_code   TEXT NOT NULL,
            trading_date DATE NOT NULL,
            o            NUMERIC(12,2) NOT NULL,
            h            NUMERIC(12,2) NOT NULL,
            l            NUMERIC(12,2) NOT NULL,
            c            NUMERIC(12,2) NOT NULL,
            v            BIGINT NOT NULL,
            value        BIGINT,
            PRIMARY KEY (index_code, trading_date)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE index_1d")
    op.execute("DROP TABLE bars_1d_src")
