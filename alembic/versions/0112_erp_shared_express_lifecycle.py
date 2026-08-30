"""Add CAS guardrails for the managed Express endpoint lifecycle."""

from alembic import op

from services.erp.shared_express_lifecycle_schema import SHARED_EXPRESS_LIFECYCLE_DDL

revision = "0112_erp_shared_express_lifecycle"
down_revision = "0111_erp_shared_express_enrollment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in SHARED_EXPRESS_LIFECYCLE_DDL:
        op.execute(statement)


def downgrade() -> None:
    """Expand-only archive: managed lifecycle protections are not downgraded."""
