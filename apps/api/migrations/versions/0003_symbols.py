"""symbols reference table (F-004, data.md §3)

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE symbols (
            symbol      TEXT PRIMARY KEY,
            exchange    TEXT NOT NULL
                CONSTRAINT symbols_exchange_check CHECK (exchange IN ('HOSE','HNX','UPCOM')),
            type        TEXT NOT NULL CONSTRAINT symbols_type_check CHECK (type IN ('STOCK','ETF')),
            name_vi     TEXT NOT NULL,
            name_en     TEXT NOT NULL,
            icb_code2   TEXT,
            listed_at   DATE,
            delisted_at DATE,
            is_delisted BOOLEAN NOT NULL DEFAULT false,
            source      TEXT NOT NULL,
            fetched_at  TIMESTAMPTZ NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE symbols")
