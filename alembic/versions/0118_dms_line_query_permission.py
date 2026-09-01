"""Add the LINE DMS query permission to operator profiles."""

from alembic import op

revision = "0118_dms_line_query_permission"
down_revision = ("0117_action_nonces", "0116_erp_team_members")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE dms_operator_profiles "
        "ADD COLUMN IF NOT EXISTS can_query_dms BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE dms_operator_profiles DROP COLUMN IF EXISTS can_query_dms")
