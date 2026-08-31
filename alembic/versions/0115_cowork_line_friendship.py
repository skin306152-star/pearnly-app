"""Track verified friendship for Cowork LINE identities."""

from alembic import op

revision = "0115_cowork_line_friendship"
down_revision = "0114_cowork_line_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE cowork_line_identities "
        "ADD COLUMN IF NOT EXISTS friendship_ready BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE cowork_line_identities "
        "ADD COLUMN IF NOT EXISTS friendship_checked_at TIMESTAMPTZ"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE cowork_line_identities DROP COLUMN IF EXISTS friendship_checked_at")
    op.execute("ALTER TABLE cowork_line_identities DROP COLUMN IF EXISTS friendship_ready")
