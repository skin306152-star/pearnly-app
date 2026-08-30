"""Protect tenant-owned managed Express endpoints."""

from alembic import op

from services.erp.shared_express_managed_schema import SHARED_EXPRESS_MANAGED_DDL

revision = "0110_erp_shared_express_managed_access"
down_revision = "0109_erp_shared_express_binding"
branch_labels = None
depends_on = None

_DDL = SHARED_EXPRESS_MANAGED_DDL


def upgrade() -> None:
    for statement in _DDL:
        op.execute(statement)


def downgrade() -> None:
    """Expand-only archive: startup and managed ownership rely on this shape."""
