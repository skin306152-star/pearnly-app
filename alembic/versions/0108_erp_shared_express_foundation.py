"""Add the dormant shared Express endpoint foundation."""

from alembic import op

revision = "0108_erp_shared_express_foundation"
down_revision = "0107_sales_line_item_type"
branch_labels = None
depends_on = None

_DDL = (
    "ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT",
    "ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS "
    "shared_scope BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE erp_push_logs ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_erp_endpoints_shared_express_workspace "
    "ON erp_endpoints (tenant_id, workspace_client_id, adapter) "
    "WHERE enabled = TRUE AND shared_scope = TRUE AND adapter = 'express' "
    "AND tenant_id IS NOT NULL AND workspace_client_id IS NOT NULL",
    """
DO $pearnly$
DECLARE
    v_unique BOOLEAN;
    v_valid BOOLEAN;
    v_ready BOOLEAN;
    v_live BOOLEAN;
    v_columns TEXT[];
    v_predicate TEXT;
    v_definition TEXT;
BEGIN
    SELECT
        index_meta.indisunique,
        index_meta.indisvalid,
        index_meta.indisready,
        index_meta.indislive,
        ARRAY(
            SELECT attribute.attname::TEXT
            FROM unnest(index_meta.indkey) WITH ORDINALITY AS key_column(attnum, position)
            JOIN pg_attribute attribute
              ON attribute.attrelid = index_meta.indrelid
             AND attribute.attnum = key_column.attnum
            WHERE key_column.position <= index_meta.indnkeyatts
            ORDER BY key_column.position
        ),
        regexp_replace(
            replace(lower(pg_get_expr(index_meta.indpred, index_meta.indrelid)), '::text', ''),
            '[[:space:]()]', '', 'g'
        ),
        regexp_replace(lower(pg_get_indexdef(index_meta.indexrelid)), '[[:space:]]+', ' ', 'g')
    INTO v_unique, v_valid, v_ready, v_live, v_columns, v_predicate, v_definition
    FROM pg_index index_meta
    JOIN pg_class index_relation ON index_relation.oid = index_meta.indexrelid
    JOIN pg_namespace index_namespace ON index_namespace.oid = index_relation.relnamespace
    JOIN pg_class table_relation ON table_relation.oid = index_meta.indrelid
    WHERE index_namespace.nspname = current_schema()
      AND index_relation.relname = 'uq_erp_endpoints_shared_express_workspace'
      AND table_relation.relname = 'erp_endpoints';

    IF NOT FOUND
       OR v_unique IS DISTINCT FROM TRUE
       OR v_valid IS DISTINCT FROM TRUE
       OR v_ready IS DISTINCT FROM TRUE
       OR v_live IS DISTINCT FROM TRUE
       OR v_columns IS DISTINCT FROM ARRAY['tenant_id', 'workspace_client_id', 'adapter']::TEXT[]
       OR v_predicate NOT IN (
           'enabled=trueandshared_scope=trueandadapter=''express''andtenant_idisnotnullandworkspace_client_idisnotnull',
           'enabledistrueandshared_scopeistrueandadapter=''express''andtenant_idisnotnullandworkspace_client_idisnotnull',
           'enabledandshared_scopeandadapter=''express''andtenant_idisnotnullandworkspace_client_idisnotnull'
       )
       OR position(
           ' using btree (tenant_id, workspace_client_id, adapter) where ' IN v_definition
       ) = 0
    THEN
        RAISE EXCEPTION
            'uq_erp_endpoints_shared_express_workspace does not match the F1 shared Express contract';
    END IF;
END
$pearnly$
""",
    "ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY",
    "DROP POLICY IF EXISTS erp_endpoints_shared_express_select ON erp_endpoints",
    "CREATE POLICY erp_endpoints_shared_express_select ON erp_endpoints FOR SELECT USING ("
    "current_setting('app.erp_shared_express_endpoint', true) = 'on' "
    "AND current_setting('app.erp_shared_express_tenant_id', true) "
    "= current_setting('app.current_tenant_id', true) "
    "AND current_setting('app.erp_shared_express_workspace_id', true) "
    "= current_setting('app.current_workspace_id', true) "
    "AND adapter = 'express' AND enabled = TRUE AND shared_scope = TRUE "
    "AND tenant_id IS NOT NULL AND workspace_client_id IS NOT NULL "
    "AND tenant_id::text = current_setting('app.erp_shared_express_tenant_id', true) "
    "AND workspace_client_id::text "
    "= current_setting('app.erp_shared_express_workspace_id', true) "
    "AND tenant_id::text = current_setting('app.current_tenant_id', true) "
    "AND workspace_client_id::text = current_setting('app.current_workspace_id', true))",
    "ALTER TABLE erp_push_logs ENABLE ROW LEVEL SECURITY",
    "DROP POLICY IF EXISTS erp_push_logs_shared_express_select ON erp_push_logs",
    "CREATE POLICY erp_push_logs_shared_express_select ON erp_push_logs FOR SELECT USING ("
    "current_setting('app.erp_shared_express_endpoint', true) = 'on' "
    "AND current_setting('app.erp_shared_express_tenant_id', true) "
    "= current_setting('app.current_tenant_id', true) "
    "AND current_setting('app.erp_shared_express_workspace_id', true) "
    "= current_setting('app.current_workspace_id', true) "
    "AND tenant_id IS NOT NULL AND workspace_client_id IS NOT NULL "
    "AND tenant_id::text = current_setting('app.erp_shared_express_tenant_id', true) "
    "AND workspace_client_id::text "
    "= current_setting('app.erp_shared_express_workspace_id', true) "
    "AND tenant_id::text = current_setting('app.current_tenant_id', true) "
    "AND workspace_client_id::text = current_setting('app.current_workspace_id', true) "
    "AND EXISTS (SELECT 1 FROM erp_endpoints shared_endpoint "
    "WHERE shared_endpoint.id = erp_push_logs.endpoint_id "
    "AND shared_endpoint.adapter = 'express' "
    "AND shared_endpoint.enabled = TRUE AND shared_endpoint.shared_scope = TRUE "
    "AND shared_endpoint.tenant_id = erp_push_logs.tenant_id "
    "AND shared_endpoint.workspace_client_id = erp_push_logs.workspace_client_id))",
)


def upgrade() -> None:
    for statement in _DDL:
        op.execute(statement)


def downgrade() -> None:
    """Expand-only foundation: preserve columns, index and policies on downgrade."""
