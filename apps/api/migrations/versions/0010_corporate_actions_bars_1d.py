"""CA tables, adj_factors, nominal bars_1d, recon_mismatches; the ssi board rows move (S05, data.md §3)

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op
from finvest_market_data.infrastructure import tables as t
from finvest_market_data.infrastructure.repositories import move_ssi_board_rows, restore_ssi_board_rows

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

NEW = (t.bars_1d, t.corporate_actions, t.corporate_action_log, t.adj_factors, t.recon_mismatches)


def upgrade() -> None:
    conn = op.get_bind()
    for table in NEW:
        table.create(conn)
    op.add_column("symbols", sa.Column("ca_checked_at", sa.DateTime(timezone=True)))
    print(f"0010: {move_ssi_board_rows(conn)} ssi rows moved to bars_1d (observed)")


def downgrade() -> None:
    conn = op.get_bind()
    print(f"0010: {restore_ssi_board_rows(conn)} observed rows moved back to bars_1d_src")
    op.drop_column("symbols", "ca_checked_at")
    for table in reversed(NEW):
        table.drop(conn)
