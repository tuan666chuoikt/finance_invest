"""null index_1d.value rows whose value/volume ratio is out of band (data.md §1.2, sprint-04 B1)

Revision ID: 0009
Revises: 0008
"""

from alembic import op
from finvest_market_data.infrastructure.repositories import repair_index_1d_value

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    print(f"0009: index_1d.value nulled on {repair_index_1d_value(op.get_bind())} rows")


def downgrade() -> None:
    pass  # data repair: the bad values are not worth restoring
