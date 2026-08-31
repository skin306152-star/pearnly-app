"""Add ERP team member access profiles."""

from alembic import op

revision = "0116_erp_team_members"
down_revision = "0115_cowork_line_friendship"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS erp_team_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            workspace_client_id BIGINT NOT NULL REFERENCES workspace_clients(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            modules JSONB NOT NULL DEFAULT '[]'::jsonb,
            erp_system TEXT,
            erp_endpoint_id UUID REFERENCES erp_endpoints(id) ON DELETE SET NULL,
            invited_by UUID NOT NULL REFERENCES users(id),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id),
            CHECK (erp_system IS NULL OR erp_system IN ('mrerp', 'express'))
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_erp_team_members_tenant_workspace "
        "ON erp_team_members (tenant_id, workspace_client_id, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS erp_team_members")
