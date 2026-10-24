"""jobs (F-034, data.md §3 + progress/summary/error JSONB, platform.md §2.6)

Revision ID: 0007
Revises: 0006
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE jobs (
            id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            kind        TEXT NOT NULL,
            args        JSONB NOT NULL DEFAULT '{}',
            status      TEXT NOT NULL CHECK (status IN ('running', 'done', 'failed')),
            created_at  TIMESTAMPTZ NOT NULL,
            finished_at TIMESTAMPTZ,
            progress    JSONB,
            summary     JSONB,
            error       JSONB,
            log         TEXT
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE jobs")
