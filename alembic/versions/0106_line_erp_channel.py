"""独立 ERP LINE OA 绑定与会话表。"""

from alembic import op

revision = "0106_line_erp_channel"
down_revision = "0105_client_submissions"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE TABLE IF NOT EXISTS line_erp_bindings (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), line_user_id text UNIQUE NOT NULL, tenant_id uuid NOT NULL, user_id uuid NOT NULL, workspace_client_id bigint, display_name text, bound_at timestamptz DEFAULT now(), last_active_at timestamptz)"
    )
    op.execute(
        "CREATE TABLE IF NOT EXISTS line_erp_binding_codes (code text PRIMARY KEY, tenant_id uuid NOT NULL, user_id uuid NOT NULL, workspace_client_id bigint, expires_at timestamptz NOT NULL, used_at timestamptz)"
    )
    op.execute(
        "CREATE TABLE IF NOT EXISTS erp_line_sessions (tenant_id uuid NOT NULL, line_user_id text NOT NULL, state text NOT NULL, payload jsonb NOT NULL DEFAULT '{}', expires_at timestamptz NOT NULL, PRIMARY KEY (tenant_id,line_user_id))"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_line_erp_bindings_user ON line_erp_bindings(user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_line_erp_codes_expiry ON line_erp_binding_codes(expires_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_erp_line_sessions_expiry ON erp_line_sessions(expires_at)"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS erp_line_sessions")
    op.execute("DROP TABLE IF EXISTS line_erp_binding_codes")
    op.execute("DROP TABLE IF EXISTS line_erp_bindings")
