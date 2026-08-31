"""Add membership-keyed Cowork LINE identities and one-time tokens."""

from alembic import op

from services.cowork_line.schema import DDL

revision = "0114_cowork_line_identity"
down_revision = "0113_erp_shared_express_live"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in DDL:
        op.execute(statement)
    for table in ("cowork_line_connect_tokens", "cowork_line_identities"):
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
    op.execute("DROP TABLE IF EXISTS cowork_line_connect_tokens")
    op.execute("DROP TABLE IF EXISTS cowork_line_identities")
