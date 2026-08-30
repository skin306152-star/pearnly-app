"""Add managed Express live heartbeat/profile confirmation guardrails."""

from alembic import op

from services.erp.shared_express_live_ddl import LIVE_DDL

revision = "0113_erp_shared_express_live"
down_revision = "0112_erp_shared_express_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in LIVE_DDL:
        op.execute(statement)


def downgrade() -> None:
    """Expand-only archive: managed live guardrails are not downgraded."""
