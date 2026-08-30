"""Allow the owner-only promotion from legacy to managed Express."""

from alembic import op

from services.erp.shared_express_enrollment_schema import SHARED_EXPRESS_ENROLLMENT_RLS_DDL

revision = "0111_erp_shared_express_enrollment"
down_revision = "0110_erp_shared_express_managed_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in SHARED_EXPRESS_ENROLLMENT_RLS_DDL:
        op.execute(statement)


def downgrade() -> None:
    """Expand-only archive; the promotion policy is required by the managed route."""
