"""事务所与 ERP 商户关系锚。

Revision ID: 0104_accounting_engagements
Revises: 0103_accounting_firm_profiles
Create Date: 2026-08-27
"""

from alembic import op

revision = "0104_accounting_engagements"
down_revision = "0103_accounting_firm_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS accounting_engagements (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
            firm_workspace_client_id bigint REFERENCES workspace_clients(id) ON DELETE RESTRICT,
            merchant_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
            merchant_workspace_client_id bigint REFERENCES workspace_clients(id) ON DELETE RESTRICT,
            status text NOT NULL DEFAULT 'pending_merchant'
                CHECK (status IN ('pending_merchant', 'pending_firm', 'active', 'suspended', 'ended')),
            is_primary boolean NOT NULL DEFAULT true,
            merchant_accepted_at timestamptz,
            firm_accepted_at timestamptz,
            active_from timestamptz,
            ended_at timestamptz,
            created_by_admin_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_accounting_engagement_distinct_tenants
                CHECK (firm_tenant_id <> merchant_tenant_id),
            CONSTRAINT ck_accounting_engagement_active_ready CHECK (
                status <> 'active' OR (
                    firm_workspace_client_id IS NOT NULL
                    AND merchant_workspace_client_id IS NOT NULL
                    AND merchant_accepted_at IS NOT NULL
                    AND firm_accepted_at IS NOT NULL
                    AND active_from IS NOT NULL
                )
            ),
            CONSTRAINT ck_accounting_engagement_ended_at CHECK (
                status <> 'ended' OR ended_at IS NOT NULL
            )
        )
        """)
    indexes = (
        "CREATE INDEX IF NOT EXISTS ix_engagement_firm_status "
        "ON accounting_engagements (firm_tenant_id, status)",
        "CREATE INDEX IF NOT EXISTS ix_engagement_merchant_status "
        "ON accounting_engagements (merchant_tenant_id, status)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_engagement_primary_merchant_open "
        "ON accounting_engagements (merchant_tenant_id) "
        "WHERE is_primary AND status <> 'ended'",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_engagement_firm_workspace_open "
        "ON accounting_engagements (firm_tenant_id, firm_workspace_client_id) "
        "WHERE firm_workspace_client_id IS NOT NULL AND status <> 'ended'",
    )
    for ddl in indexes:
        op.execute(ddl)
    op.execute("ALTER TABLE accounting_engagements ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS participant_tenant_isolation ON accounting_engagements")
    predicate = (
        "(firm_tenant_id::text = current_setting('app.current_tenant_id', true) "
        "OR merchant_tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "OR current_setting('app.bypass_rls', true) = 'on'"
    )
    op.execute(
        "CREATE POLICY participant_tenant_isolation ON accounting_engagements FOR ALL "
        f"USING ({predicate}) WITH CHECK ({predicate})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS participant_tenant_isolation ON accounting_engagements")
    op.execute("DROP TABLE IF EXISTS accounting_engagements")
