# -*- coding: utf-8 -*-
"""Dormant database foundation for tenant/workspace shared Express endpoints."""

from __future__ import annotations

from core import db
from core.rls import ERP_SHARED_EXPRESS_SELECT_DDL
from services.erp.shared_express_managed_schema import managed_foundation_ready
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for

SHARED_EXPRESS_SESSION_GUC = "app.erp_shared_express_endpoint"
SHARED_EXPRESS_TENANT_GUC = "app.erp_shared_express_tenant_id"
SHARED_EXPRESS_WORKSPACE_GUC = "app.erp_shared_express_workspace_id"
SHARED_EXPRESS_INDEX = "uq_erp_endpoints_shared_express_workspace"

_INDEX_CONTRACT_DDL = """
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
"""

SHARED_EXPRESS_DDL = (
    "ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT",
    "ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS "
    "shared_scope BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE erp_push_logs ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_erp_endpoints_shared_express_workspace "
    "ON erp_endpoints (tenant_id, workspace_client_id, adapter) "
    "WHERE enabled = TRUE AND shared_scope = TRUE AND adapter = 'express' "
    "AND tenant_id IS NOT NULL AND workspace_client_id IS NOT NULL",
    _INDEX_CONTRACT_DDL,
) + ERP_SHARED_EXPRESS_SELECT_DDL


def apply_shared_express_foundation(cur) -> None:
    """Apply the additive, idempotent DDL on an existing cursor."""
    for statement in SHARED_EXPRESS_DDL:
        cur.execute(statement)


def ensure_shared_express_foundation() -> None:
    """Startup dual-run for deployments that do not execute Alembic."""
    with db.get_cursor(commit=True) as cur:
        apply_shared_express_foundation(cur)


def enable_shared_express_select(cur, tenant_id: str, workspace_client_id: object) -> bool:
    """Bind shared visibility to the validated tenant and cursor workspace."""
    cur.execute(f"SET LOCAL {SHARED_EXPRESS_SESSION_GUC} = 'off'")
    if not managed_foundation_ready():
        return False
    tenant_scope = str(tenant_id).strip() if tenant_id is not None else ""
    workspace_scope = str(workspace_client_id).strip() if workspace_client_id is not None else ""
    if not tenant_scope or not workspace_scope:
        return False
    if not erp_shared_express_endpoint_enabled_for(tenant_scope):
        return False

    cur.execute(
        "SELECT current_setting('app.current_tenant_id', true) = %s "
        "AND current_setting('app.current_workspace_id', true) = %s AS matches",
        (tenant_scope, workspace_scope),
    )
    row = cur.fetchone()
    matches = row.get("matches") if hasattr(row, "get") else row[0] if row else False
    if not matches:
        return False

    cur.execute(
        "SELECT set_config('app.erp_shared_express_tenant_id', %s, true), "
        "set_config('app.erp_shared_express_workspace_id', %s, true), "
        "set_config('app.erp_shared_express_endpoint', 'on', true)",
        (tenant_scope, workspace_scope),
    )
    return True
