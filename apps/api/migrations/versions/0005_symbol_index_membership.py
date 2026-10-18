"""symbol_index_membership (F-004, data.md §3)

Revision ID: 0005
Revises: 0004
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE symbol_index_membership (
            index_code TEXT NOT NULL,
            symbol     TEXT NOT NULL,
            valid_from DATE NOT NULL,
            valid_to   DATE,
            PRIMARY KEY (index_code, symbol, valid_from)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE symbol_index_membership")
