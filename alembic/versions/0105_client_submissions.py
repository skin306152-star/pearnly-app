"""ERP 已确认单据直达 Cowork 的 outbox。

Revision ID: 0105_client_submissions
Revises: 0104_accounting_engagements
Create Date: 2026-08-27
"""

from alembic import op

revision = "0105_client_submissions"
down_revision = "0104_accounting_engagements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_submissions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            product_scope text NOT NULL DEFAULT 'erp' CHECK (product_scope = 'erp'),
            engagement_id uuid NOT NULL REFERENCES accounting_engagements(id) ON DELETE RESTRICT,
            source_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
            source_workspace_client_id bigint NOT NULL REFERENCES workspace_clients(id) ON DELETE RESTRICT,
            source_document_type text NOT NULL CHECK (source_document_type IN ('purchase', 'sales')),
            source_document_id text NOT NULL,
            source_revision integer NOT NULL CHECK (source_revision > 0),
            source_hash text NOT NULL,
            target_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
            target_workspace_client_id bigint NOT NULL REFERENCES workspace_clients(id) ON DELETE RESTRICT,
            snapshot_json jsonb NOT NULL,
            original_file_ref text,
            status text NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'delivered', 'failed', 'superseded')),
            cowork_history_id uuid REFERENCES ocr_history(id) ON DELETE SET NULL,
            attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
            next_attempt_at timestamptz,
            last_error text,
            created_at timestamptz NOT NULL DEFAULT now(),
            delivered_at timestamptz,
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_client_submission_revision UNIQUE (
                engagement_id, source_document_type, source_document_id, source_revision
            ),
            CONSTRAINT ck_client_submission_distinct_tenants
                CHECK (source_tenant_id <> target_tenant_id),
            CONSTRAINT ck_client_submission_delivered_ready CHECK (
                status <> 'delivered' OR delivered_at IS NOT NULL
            )
        )
        """)
    op.execute(
        "ALTER TABLE client_submissions "
        "DROP CONSTRAINT IF EXISTS ck_client_submission_delivered_ready"
    )
    op.execute(
        "ALTER TABLE client_submissions "
        "ADD CONSTRAINT ck_client_submission_delivered_ready "
        "CHECK (status <> 'delivered' OR delivered_at IS NOT NULL)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_client_submission_due "
        "ON client_submissions (status, next_attempt_at, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_client_submission_source "
        "ON client_submissions (source_tenant_id, source_workspace_client_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_client_submission_target "
        "ON client_submissions (target_tenant_id, target_workspace_client_id, created_at DESC)"
    )
    op.execute("ALTER TABLE client_submissions ENABLE ROW LEVEL SECURITY")
    for policy in (
        "participant_tenant_isolation",
        "client_submission_participant_read",
        "client_submission_source_insert",
        "client_submission_system_update",
        "client_submission_system_delete",
    ):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON client_submissions")
    current = "current_setting('app.current_tenant_id', true)"
    bypass = "current_setting('app.bypass_rls', true) = 'on'"
    participant = f"source_tenant_id::text = {current} OR target_tenant_id::text = {current}"
    valid_source = (
        f"source_tenant_id::text = {current} AND EXISTS ("
        "SELECT 1 FROM accounting_engagements e "
        "WHERE e.id = client_submissions.engagement_id "
        "AND e.status IN ('active', 'suspended') "
        "AND e.merchant_tenant_id = client_submissions.source_tenant_id "
        "AND e.merchant_workspace_client_id = client_submissions.source_workspace_client_id "
        "AND e.firm_tenant_id = client_submissions.target_tenant_id "
        "AND e.firm_workspace_client_id = client_submissions.target_workspace_client_id)"
    )
    op.execute(
        "CREATE POLICY client_submission_participant_read ON client_submissions "
        f"FOR SELECT USING (({participant}) OR {bypass})"
    )
    op.execute(
        "CREATE POLICY client_submission_source_insert ON client_submissions "
        f"FOR INSERT WITH CHECK (({valid_source}) OR {bypass})"
    )
    op.execute(
        "CREATE POLICY client_submission_system_update ON client_submissions "
        f"FOR UPDATE USING ({bypass}) WITH CHECK ({bypass})"
    )
    op.execute(
        "CREATE POLICY client_submission_system_delete ON client_submissions "
        f"FOR DELETE USING ({bypass})"
    )


def downgrade() -> None:
    for policy in (
        "client_submission_participant_read",
        "client_submission_source_insert",
        "client_submission_system_update",
        "client_submission_system_delete",
    ):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON client_submissions")
    op.execute("DROP TABLE IF EXISTS client_submissions")
