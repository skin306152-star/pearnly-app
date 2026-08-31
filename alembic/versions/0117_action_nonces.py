"""Add neutral action authorization nonces for Steward workflows."""

from alembic import op

revision = "0117_action_nonces"
down_revision = "0116_cowork_line_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS action_nonces (
            token TEXT PRIMARY KEY,
            tenant_id UUID NOT NULL,
            workspace_client_id BIGINT NOT NULL,
            user_id TEXT NOT NULL DEFAULT '',
            action_ref TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            consumed_at TIMESTAMPTZ
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_action_nonces_expires " "ON action_nonces (expires_at)"
    )
    op.execute("ALTER TABLE action_nonces ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON action_nonces")
    op.execute(
        "CREATE POLICY tenant_isolation ON action_nonces FOR ALL "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true) "
        "OR current_setting('app.bypass_rls', true) = 'on') "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true) "
        "OR current_setting('app.bypass_rls', true) = 'on')"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS action_nonces")
