"""Add immutable ERP target projection snapshots and current heads."""

from alembic import op

from services.erp.target_projection_schema import DDL, TABLES

revision = "0119_erp_target_projection"
down_revision = "0118_dms_line_query_permission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in DDL:
        op.execute(statement)
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} FOR ALL "
            "USING (tenant_id::text = current_setting('app.current_tenant_id', true) "
            "OR current_setting('app.bypass_rls', true) = 'on') "
            "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true) "
            "OR current_setting('app.bypass_rls', true) = 'on')"
        )


def downgrade() -> None:
    """Expand-only archive: projection history is intentionally retained."""
