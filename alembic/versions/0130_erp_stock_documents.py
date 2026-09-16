"""Internal stock receipt/issue documents."""

from alembic import op

revision = "0130_erp_stock_documents"
down_revision = "0129_dms_master_refresh_locks"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE TABLE IF NOT EXISTS erp_stock_documents (\n id uuid PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL,\n direction text NOT NULL CHECK(direction IN ('in','out')), doc_no text NOT NULL,\n doc_date date NOT NULL, fields jsonb NOT NULL, created_by uuid NOT NULL,\n created_at timestamptz NOT NULL DEFAULT now(),\n UNIQUE(tenant_id,doc_no))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_erp_stock_documents_workspace ON erp_stock_documents(tenant_id,workspace_client_id,doc_date)"
    )
    op.execute("ALTER TABLE erp_stock_documents ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON erp_stock_documents")
    op.execute(
        "CREATE POLICY tenant_isolation ON erp_stock_documents USING (tenant_id::text=current_setting('app.current_tenant_id',true) OR current_setting('app.bypass_rls',true)='on') WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true) OR current_setting('app.bypass_rls',true)='on')"
    )


def downgrade():
    op.execute("DROP TABLE erp_stock_documents")
