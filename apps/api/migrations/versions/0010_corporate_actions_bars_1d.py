"""CA tables, adj_factors, nominal bars_1d, recon_mismatches; the ssi board rows move (S05, data.md §3)

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op
from finvest_market_data.infrastructure.repositories import move_ssi_board_rows, restore_ssi_board_rows

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    # frozen DDL on purpose: never build it from the live tables.py metadata (later migrations alter these)
    op.create_table(
        "bars_1d",
        sa.Column("symbol", sa.Text, primary_key=True),
        sa.Column("trading_date", sa.Date, primary_key=True),
        sa.Column("o", sa.BigInteger, nullable=False),
        sa.Column("h", sa.BigInteger, nullable=False),
        sa.Column("l", sa.BigInteger, nullable=False),
        sa.Column("c", sa.BigInteger, nullable=False),
        sa.Column("ref", sa.BigInteger),
        sa.Column("ceiling", sa.BigInteger),
        sa.Column("floor", sa.BigInteger),
        sa.Column("v", sa.BigInteger, nullable=False),
        sa.Column("value", sa.BigInteger),
        sa.Column("nominal_kind", sa.Text, nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("fetched_at", TZ, nullable=False),
        sa.CheckConstraint("nominal_kind IN ('observed','reconstructed')", name="bars_1d_nominal_kind_check"),
    )
    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("symbol", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("ex_date", sa.Date),
        sa.Column("record_date", sa.Date),
        sa.Column("pay_date", sa.Date),
        sa.Column("public_date", sa.Date),
        sa.Column("title", sa.Text),
        sa.Column("ratio_a", sa.Integer),
        sa.Column("ratio_b", sa.Integer),
        sa.Column("cash_per_share", sa.BigInteger),
        sa.Column("issue_price", sa.BigInteger),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("source_event_id", sa.Text, nullable=False),
        sa.Column("fetched_at", TZ, nullable=False),
        sa.UniqueConstraint("source", "source_event_id", name="corporate_actions_source_event_key"),
    )
    op.create_table(
        "corporate_action_log",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("ca_id", sa.BigInteger, nullable=False),
        sa.Column("changed_at", TZ, nullable=False),
        sa.Column("field", sa.Text, nullable=False),
        sa.Column("old", sa.Text),
        sa.Column("new", sa.Text),
    )
    op.create_table(
        "adj_factors",
        sa.Column("symbol", sa.Text, primary_key=True),
        sa.Column("ex_date", sa.Date, primary_key=True),
        sa.Column("factor", sa.Numeric(20, 12), nullable=False),
        sa.Column("ca_id", sa.BigInteger),
        sa.Column("rules_version", sa.Text, nullable=False),
    )
    op.create_table(
        "recon_mismatches",
        sa.Column("symbol", sa.Text, primary_key=True),
        sa.Column("trading_date", sa.Date, primary_key=True),
        sa.Column("ours", sa.BigInteger, nullable=False),
        sa.Column("theirs", sa.BigInteger, nullable=False),
        sa.Column("diff_pct", sa.Numeric(8, 4), nullable=False),
        sa.Column("checked_at", TZ, nullable=False),
    )
    op.add_column("symbols", sa.Column("ca_checked_at", TZ))
    print(f"0010: {move_ssi_board_rows(op.get_bind())} ssi rows moved to bars_1d (observed)")


def downgrade() -> None:
    print(f"0010: {restore_ssi_board_rows(op.get_bind())} observed rows moved back to bars_1d_src")
    op.drop_column("symbols", "ca_checked_at")
    for name in ("recon_mismatches", "adj_factors", "corporate_action_log", "corporate_actions", "bars_1d"):
        op.drop_table(name)
