"""crawl_sessions.symbols_no_trades (S02-1, data.md §3)

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE crawl_sessions ADD COLUMN symbols_no_trades INT")


def downgrade() -> None:
    op.execute("ALTER TABLE crawl_sessions DROP COLUMN symbols_no_trades")
