"""scenarios (F-055, data.md §3)

Revision ID: 0006
Revises: 0005
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE scenarios (
            id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name       TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 60),
            symbol     TEXT NOT NULL,
            style      TEXT NOT NULL CHECK (style IN ('lump_sum', 'dca')),
            amount_vnd BIGINT NOT NULL CHECK (amount_vnd > 0),
            buy_date   DATE NOT NULL,
            sell_date  DATE,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE scenarios")
