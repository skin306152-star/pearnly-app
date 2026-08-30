# -*- coding: utf-8 -*-
"""Database guardrails for the managed Express endpoint lifecycle."""

from __future__ import annotations

from core import db
from psycopg2.extensions import adapt
from services.erp.shared_express_lifecycle_ddl import (
    CATALOG_VALIDATION_DDL,
    INDEX_CONTRACT_DDL,
    LIFECYCLE_POLICY_DDL,
)

LIFECYCLE_GATE_GUC = "app.erp_endpoint_lifecycle"
LIFECYCLE_TENANT_GUC = "app.erp_endpoint_lifecycle_tenant_id"
LIFECYCLE_ACTOR_GUC = "app.erp_endpoint_lifecycle_actor_id"
LIFECYCLE_ENDPOINT_GUC = "app.erp_endpoint_lifecycle_endpoint_id"
LIFECYCLE_ACTION_GUC = "app.erp_endpoint_lifecycle_action"
LIFECYCLE_SOURCE_WORKSPACE_GUC = "app.erp_endpoint_lifecycle_source_workspace_id"
LIFECYCLE_TARGET_WORKSPACE_GUC = "app.erp_endpoint_lifecycle_target_workspace_id"
LIFECYCLE_GENERATION_GUC = "app.erp_endpoint_lifecycle_expected_generation"
LIFECYCLE_OPERATION_GUC = "app.erp_endpoint_lifecycle_operation_id"

_LIFECYCLE_SCHEMA_READY: bool | None = None


def lifecycle_schema_ready() -> bool:
    return _LIFECYCLE_SCHEMA_READY is True


def _sql_literal(value: str) -> str:
    return adapt(value).getquoted().decode("utf-8")


_SENSITIVE_GUARD_FUNCTION_DDL = """
CREATE OR REPLACE FUNCTION public.guard_erp_endpoint_lifecycle_columns()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
DECLARE
    v_action text := current_setting('app.erp_endpoint_lifecycle_action', true);
    v_expected text := current_setting('app.erp_endpoint_lifecycle_expected_generation', true);
    v_source text := current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true);
    v_target text := current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true);
    v_scrubbed jsonb;
BEGIN
    IF OLD.binding_generation = 0 THEN
        RETURN NEW;
    END IF;
    IF current_setting('app.erp_endpoint_lifecycle', true) <> 'on'
       OR current_setting('app.current_tenant_id', true) <> OLD.tenant_id::text
       OR current_setting('app.current_user_id', true) <> current_setting('app.erp_endpoint_lifecycle_actor_id', true)
       OR current_setting('app.erp_endpoint_lifecycle_endpoint_id', true) <> OLD.id::text
       OR current_setting('app.erp_endpoint_lifecycle_operation_id', true) !~
           '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
       OR v_expected !~ '^[1-9][0-9]*$'
       OR v_expected::bigint <> OLD.binding_generation
       OR v_source IS DISTINCT FROM COALESCE(OLD.workspace_client_id::text, '')
    THEN
        RAISE EXCEPTION 'erp.endpoint_lifecycle_gate_required';
    END IF;
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.name IS DISTINCT FROM OLD.name
       OR NEW.adapter IS DISTINCT FROM OLD.adapter
       OR NEW.is_default IS DISTINCT FROM OLD.is_default
       OR NEW.auto_push IS DISTINCT FROM OLD.auto_push
       OR NEW.last_used_at IS DISTINCT FROM OLD.last_used_at
       OR NEW.last_status IS DISTINCT FROM OLD.last_status
       OR NEW.success_count IS DISTINCT FROM OLD.success_count
       OR NEW.failure_count IS DISTINCT FROM OLD.failure_count
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.bound_account_set IS DISTINCT FROM OLD.bound_account_set
       OR NEW.bound_profile_key IS DISTINCT FROM OLD.bound_profile_key
       OR NEW.live_account_set IS DISTINCT FROM OLD.live_account_set
       OR NEW.live_profile_key IS DISTINCT FROM OLD.live_profile_key
       OR NEW.agent_last_seen_at IS DISTINCT FROM OLD.agent_last_seen_at
       OR NEW.agent_version IS DISTINCT FROM OLD.agent_version
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
    THEN
        RAISE EXCEPTION 'erp endpoint lifecycle may only change lifecycle columns';
    END IF;
    IF NEW.binding_generation <> OLD.binding_generation + 1 THEN
        RAISE EXCEPTION 'erp.endpoint_stale_generation';
    END IF;
    IF v_action = 'rebind' THEN
        IF OLD.revoked_at IS NOT NULL OR OLD.enabled OR NOT OLD.shared_scope
           OR OLD.workspace_client_id IS NULL
           OR v_target IS NULL OR v_target = ''
           OR NEW.workspace_client_id::text IS DISTINCT FROM v_target
           OR NEW.enabled OR NOT NEW.shared_scope
           OR NEW.revoked_at IS NOT NULL OR NEW.revoked_by IS NOT NULL
           OR NEW.config IS DISTINCT FROM OLD.config
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_rebind';
        END IF;
    ELSIF v_action = 'enable' THEN
        IF OLD.revoked_at IS NOT NULL OR OLD.enabled OR NOT OLD.shared_scope
           OR NEW.workspace_client_id IS DISTINCT FROM OLD.workspace_client_id
           OR NOT NEW.enabled OR NOT NEW.shared_scope
           OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
           OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by
           OR NEW.config IS DISTINCT FROM OLD.config
           OR v_target IS DISTINCT FROM v_source
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_enable';
        END IF;
    ELSIF v_action = 'disable' THEN
        IF OLD.revoked_at IS NOT NULL OR NOT OLD.enabled OR NOT OLD.shared_scope
           OR NEW.workspace_client_id IS DISTINCT FROM OLD.workspace_client_id
           OR NEW.enabled OR NOT NEW.shared_scope
           OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
           OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by
           OR NEW.config IS DISTINCT FROM OLD.config
           OR v_target IS DISTINCT FROM v_source
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_disable';
        END IF;
    ELSIF v_action = 'revoke' THEN
        IF OLD.revoked_at IS NOT NULL OR OLD.enabled OR NOT OLD.shared_scope
           OR NEW.workspace_client_id IS NOT NULL OR NEW.enabled OR NEW.shared_scope
           OR NEW.revoked_at IS NULL
           OR NEW.revoked_by::text IS DISTINCT FROM current_setting('app.erp_endpoint_lifecycle_actor_id', true)
           OR v_target IS DISTINCT FROM ''
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_revoke';
        END IF;
        v_scrubbed := OLD.config - ARRAY[
            'agent_token', 'agent_token_hash', 'agent_token_tail', 'agent_token_created_at'
        ]::text[];
        IF NEW.config IS DISTINCT FROM v_scrubbed THEN
            RAISE EXCEPTION 'erp.endpoint_revoke_token_scrub_required';
        END IF;
    ELSE
        RAISE EXCEPTION 'erp.endpoint_lifecycle_action_required';
    END IF;
    RETURN NEW;
END
$pearnly$
""".strip()

_BUSY_HELPER_FUNCTION_DDL = """
CREATE OR REPLACE FUNCTION public.erp_managed_endpoint_has_activity(p_endpoint_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
    SELECT EXISTS (
        SELECT 1
        FROM public.erp_endpoints endpoint
        WHERE endpoint.id = $1
          AND endpoint.binding_generation > 0
          AND endpoint.adapter = 'express'
          AND endpoint.revoked_at IS NULL
          AND endpoint.tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
          AND endpoint.workspace_client_id IS NOT NULL
          AND EXISTS (
              SELECT 1
              FROM public.workspace_clients workspace
              WHERE workspace.id = endpoint.workspace_client_id
                AND workspace.tenant_id = endpoint.tenant_id
                AND workspace.is_active = TRUE
          )
          AND EXISTS (
              SELECT 1
              FROM public.users actor
              JOIN public.memberships membership ON membership.user_id = actor.id
              JOIN public.roles role ON role.id = membership.role_id
              WHERE actor.id::text = pg_catalog.current_setting('app.current_user_id', true)
                AND actor.tenant_id = endpoint.tenant_id
                AND actor.is_active = TRUE
                AND membership.tenant_id = endpoint.tenant_id
                AND membership.status = 'active'
                AND role.name = 'owner'
          )
          AND EXISTS (
              SELECT 1
              FROM public.erp_push_logs push_log
              WHERE push_log.endpoint_id = endpoint.id
                AND (
                    push_log.status IN ('pending', 'retrying')
                    OR push_log.next_retry_at IS NOT NULL
                    OR push_log.lease_owner IS NOT NULL
                    OR push_log.lease_expires_at IS NOT NULL
                )
          )
    )
$pearnly$
""".strip()

_HELPER_ACL_DDL = (
    "REVOKE ALL ON FUNCTION public.erp_managed_endpoint_has_activity(uuid) FROM PUBLIC",
    """
DO $pearnly$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'pearnly_app') THEN
        EXECUTE 'GRANT EXECUTE ON FUNCTION public.erp_managed_endpoint_has_activity(uuid) TO pearnly_app';
    END IF;
END
$pearnly$
""".strip(),
)


def _replace_constraint(name: str, expression: str, normalized: str) -> str:
    return f"""
DO $pearnly$
DECLARE
    v_definition text;
BEGIN
    SELECT regexp_replace(lower(pg_get_constraintdef(oid)), '[[:space:]()]', '', 'g')
      INTO v_definition
      FROM pg_catalog.pg_constraint
     WHERE conrelid = 'erp_endpoints'::regclass AND conname = {_sql_literal(name)};
    IF v_definition IS NOT NULL AND v_definition <> {_sql_literal(normalized)} THEN
        ALTER TABLE erp_endpoints DROP CONSTRAINT "{name}";
        v_definition := NULL;
    END IF;
    IF v_definition IS NULL THEN
        ALTER TABLE erp_endpoints ADD CONSTRAINT {name} CHECK ({expression}) NOT VALID;
    END IF;
END
$pearnly$
""".strip()


_TRIGGER_CONTRACT_DDL = """
DO $pearnly$
DECLARE
    v_enabled "char";
    v_tgtype smallint;
    v_tgattr text;
    v_has_when boolean;
    v_function oid;
BEGIN
    SELECT trigger_meta.tgenabled, trigger_meta.tgtype, trigger_meta.tgattr::text,
           trigger_meta.tgqual IS NOT NULL, trigger_meta.tgfoid
      INTO v_enabled, v_tgtype, v_tgattr, v_has_when, v_function
      FROM pg_catalog.pg_trigger trigger_meta
     WHERE trigger_meta.tgrelid = 'erp_endpoints'::regclass
       AND trigger_meta.tgname = 'erp_endpoints_lifecycle_columns_guard'
       AND NOT trigger_meta.tgisinternal;
    IF NOT FOUND THEN
        CREATE TRIGGER erp_endpoints_lifecycle_columns_guard
        BEFORE UPDATE OF tenant_id, workspace_client_id, binding_generation, enabled,
            shared_scope, revoked_at, revoked_by, updated_at ON public.erp_endpoints
        FOR EACH ROW
        EXECUTE FUNCTION public.guard_erp_endpoint_lifecycle_columns();
    ELSIF v_enabled IS DISTINCT FROM 'O' OR v_tgtype IS DISTINCT FROM 19
       OR v_tgattr IS DISTINCT FROM (
           SELECT string_agg(attribute.attnum::text, ' ' ORDER BY array_position(
               ARRAY['tenant_id', 'workspace_client_id', 'binding_generation', 'enabled',
                     'shared_scope', 'revoked_at', 'revoked_by', 'updated_at'], attribute.attname
           ))
           FROM pg_catalog.pg_attribute attribute
           WHERE attribute.attrelid = 'erp_endpoints'::regclass
             AND attribute.attname = ANY (ARRAY[
                 'tenant_id', 'workspace_client_id', 'binding_generation', 'enabled',
                 'shared_scope', 'revoked_at', 'revoked_by', 'updated_at'
             ])
             AND attribute.attnum > 0 AND NOT attribute.attisdropped
       ) OR v_has_when
       OR v_function IS DISTINCT FROM 'public.guard_erp_endpoint_lifecycle_columns()'::regprocedure
    THEN
        RAISE EXCEPTION 'erp_endpoints_lifecycle_columns_guard does not match lifecycle contract';
    END IF;
END
$pearnly$
""".strip()


_STRUCTURE_DDL = (
    "ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ",
    "ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS revoked_by UUID",
    _replace_constraint(
        "erp_endpoints_managed_scope_chk",
        "binding_generation = 0 OR (tenant_id IS NOT NULL AND adapter = 'express' AND (workspace_client_id IS NOT NULL OR revoked_at IS NOT NULL))",
        "checkbinding_generation=0ortenant_idisnotnullandadapter='express'::textandworkspace_client_idisnotnullorrevoked_atisnotnull",
    ),
    "ALTER TABLE erp_endpoints VALIDATE CONSTRAINT erp_endpoints_managed_scope_chk",
    _replace_constraint(
        "erp_endpoints_revoked_pair_chk",
        "(revoked_at IS NULL) = (revoked_by IS NULL)",
        "checkrevoked_atisnull=revoked_byisnull",
    ),
    "ALTER TABLE erp_endpoints VALIDATE CONSTRAINT erp_endpoints_revoked_pair_chk",
    _replace_constraint(
        "erp_endpoints_revoked_terminal_chk",
        "revoked_at IS NULL OR (binding_generation > 0 AND tenant_id IS NOT NULL AND adapter = 'express' AND enabled = FALSE AND shared_scope = FALSE AND workspace_client_id IS NULL)",
        "checkrevoked_atisnullorbinding_generation>0andtenant_idisnotnullandadapter='express'::textandenabled=falseandshared_scope=falseandworkspace_client_idisnull",
    ),
    "ALTER TABLE erp_endpoints VALIDATE CONSTRAINT erp_endpoints_revoked_terminal_chk",
    INDEX_CONTRACT_DDL,
    _SENSITIVE_GUARD_FUNCTION_DDL,
    "REVOKE ALL ON FUNCTION public.guard_erp_endpoint_lifecycle_columns() FROM PUBLIC",
    _TRIGGER_CONTRACT_DDL,
    _BUSY_HELPER_FUNCTION_DDL,
    *_HELPER_ACL_DDL,
    *LIFECYCLE_POLICY_DDL,
    CATALOG_VALIDATION_DDL,
)

SHARED_EXPRESS_LIFECYCLE_DDL = _STRUCTURE_DDL


def apply_shared_express_lifecycle_schema(cur) -> None:
    for statement in SHARED_EXPRESS_LIFECYCLE_DDL:
        cur.execute(statement)


def ensure_shared_express_lifecycle_schema() -> None:
    global _LIFECYCLE_SCHEMA_READY
    try:
        with db.get_cursor(commit=True) as cur:
            apply_shared_express_lifecycle_schema(cur)
    except Exception:
        _LIFECYCLE_SCHEMA_READY = False
        raise
    _LIFECYCLE_SCHEMA_READY = True


def _reset_lifecycle_gate(cur) -> None:
    cur.execute(
        "SELECT set_config(%s, 'off', true), "
        "set_config(%s, '', true), set_config(%s, '', true), set_config(%s, '', true), "
        "set_config(%s, '', true), set_config(%s, '', true), set_config(%s, '', true), "
        "set_config(%s, '', true), set_config(%s, '', true)",
        (
            LIFECYCLE_GATE_GUC,
            LIFECYCLE_TENANT_GUC,
            LIFECYCLE_ACTOR_GUC,
            LIFECYCLE_ENDPOINT_GUC,
            LIFECYCLE_ACTION_GUC,
            LIFECYCLE_SOURCE_WORKSPACE_GUC,
            LIFECYCLE_TARGET_WORKSPACE_GUC,
            LIFECYCLE_GENERATION_GUC,
            LIFECYCLE_OPERATION_GUC,
        ),
    )


def enable_shared_express_lifecycle_access(
    cur,
    *,
    tenant_id: object,
    actor_user_id: object,
    endpoint_id: object,
    action: str,
    source_workspace_id: object,
    target_workspace_id: object,
    expected_generation: int,
) -> bool:
    """Validate the current owner context before setting the exact tx-local gate."""
    _reset_lifecycle_gate(cur)
    if not lifecycle_schema_ready():
        return False
    tenant = str(tenant_id or "").strip()
    actor = str(actor_user_id or "").strip()
    endpoint = str(endpoint_id or "").strip()
    source = "" if source_workspace_id is None else str(source_workspace_id).strip()
    target = "" if target_workspace_id is None else str(target_workspace_id).strip()
    if (
        not tenant
        or not actor
        or not endpoint
        or action not in {"rebind", "enable", "disable", "revoke"}
    ):
        return False
    if (
        not isinstance(expected_generation, int)
        or isinstance(expected_generation, bool)
        or expected_generation < 1
    ):
        return False
    cur.execute(
        "SELECT current_setting('app.current_tenant_id', true) = %s "
        "AND current_setting('app.current_user_id', true) = %s "
        "AND current_setting('app.current_workspace_id', true) = %s AS matches",
        (tenant, actor, source),
    )
    context = cur.fetchone()
    if not context or not bool(context.get("matches")):
        return False
    cur.execute(
        "SELECT actor.id FROM users actor "
        "WHERE actor.id = %s AND actor.tenant_id = %s AND actor.is_active = TRUE FOR SHARE",
        (actor, tenant),
    )
    if not cur.fetchone():
        return False
    cur.execute(
        "SELECT membership.id FROM memberships membership "
        "JOIN roles role ON role.id = membership.role_id "
        "WHERE membership.user_id = %s AND membership.tenant_id = %s "
        "AND membership.status = 'active' AND role.name = 'owner' FOR SHARE",
        (actor, tenant),
    )
    if not cur.fetchone():
        return False
    cur.execute(
        "SELECT id FROM workspace_clients WHERE id = %s AND tenant_id = %s "
        "AND is_active = TRUE FOR SHARE",
        (source, tenant),
    )
    if not cur.fetchone():
        return False
    if action == "rebind" and not target:
        return False
    if action in {"enable", "disable"} and target != source:
        return False
    if action == "revoke" and target:
        return False
    cur.execute(
        "SELECT set_config(%s, 'on', true), set_config(%s, %s, true), set_config(%s, %s, true), "
        "set_config(%s, %s, true), set_config(%s, %s, true), set_config(%s, %s, true), "
        "set_config(%s, %s, true), set_config(%s, %s, true), set_config(%s, %s, true)",
        (
            LIFECYCLE_GATE_GUC,
            LIFECYCLE_TENANT_GUC,
            tenant,
            LIFECYCLE_ACTOR_GUC,
            actor,
            LIFECYCLE_ENDPOINT_GUC,
            endpoint,
            LIFECYCLE_ACTION_GUC,
            action,
            LIFECYCLE_SOURCE_WORKSPACE_GUC,
            source,
            LIFECYCLE_TARGET_WORKSPACE_GUC,
            target,
            LIFECYCLE_GENERATION_GUC,
            str(expected_generation),
            LIFECYCLE_OPERATION_GUC,
            "",
        ),
    )
    return True


def endpoint_has_managed_activity(cur, endpoint_id: object) -> bool:
    cur.execute("SELECT public.erp_managed_endpoint_has_activity(%s) AS busy", (str(endpoint_id),))
    row = cur.fetchone()
    return bool(row and row.get("busy"))


__all__ = [
    "LIFECYCLE_ACTION_GUC",
    "LIFECYCLE_ACTOR_GUC",
    "LIFECYCLE_ENDPOINT_GUC",
    "LIFECYCLE_GENERATION_GUC",
    "LIFECYCLE_GATE_GUC",
    "LIFECYCLE_OPERATION_GUC",
    "LIFECYCLE_SOURCE_WORKSPACE_GUC",
    "LIFECYCLE_TARGET_WORKSPACE_GUC",
    "LIFECYCLE_TENANT_GUC",
    "SHARED_EXPRESS_LIFECYCLE_DDL",
    "apply_shared_express_lifecycle_schema",
    "enable_shared_express_lifecycle_access",
    "endpoint_has_managed_activity",
    "ensure_shared_express_lifecycle_schema",
    "lifecycle_schema_ready",
]
