"""Add durable ERP master refresh requests."""

from alembic import op

from services.erp.target_projection_schema import DDL

revision = "0120_erp_target_refresh_requests"
down_revision = "0119_erp_target_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in DDL:
        if "erp_target_refresh_requests" in statement or "erp_target_refresh_" in statement:
            op.execute(statement)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS erp_target_refresh_requests")
