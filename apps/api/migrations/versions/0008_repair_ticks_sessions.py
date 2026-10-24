"""repair the ticks ledger rows from the ticks table (platform.md §4 v1.12)

Revision ID: 0008
Revises: 0007
"""

from alembic import op
from finvest_market_data.infrastructure.repositories import repair_crawl_sessions_from_ticks

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    repair_crawl_sessions_from_ticks(op.get_bind())


def downgrade() -> None:
    pass  # data repair: the old (too small) counts are not worth restoring
