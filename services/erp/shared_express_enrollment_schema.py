# -*- coding: utf-8 -*-
"""RLS promotion policy for legacy Express endpoint enrollment."""

from __future__ import annotations

from core import db

_ENROLLMENT_RLS_READY: bool | None = None


def enrollment_rls_ready() -> bool:
    return _ENROLLMENT_RLS_READY is True


_PROMOTION_USING = """
binding_generation = 0
AND adapter = 'express'
AND user_id::text = current_setting('app.current_user_id', true)
AND (tenant_id IS NULL OR tenant_id::text = current_setting('app.current_tenant_id', true))
""".strip()

_PROMOTION_CHECK = """
binding_generation = 1
AND adapter = 'express'
AND shared_scope = TRUE
AND user_id::text = current_setting('app.current_user_id', true)
AND tenant_id::text = current_setting('app.current_tenant_id', true)
AND workspace_client_id::text = current_setting('app.current_workspace_id', true)
AND EXISTS (
    SELECT 1 FROM workspace_clients workspace
    WHERE workspace.id = erp_endpoints.workspace_client_id
      AND workspace.tenant_id::text = current_setting('app.current_tenant_id', true)
      AND workspace.is_active = TRUE
)
AND EXISTS (
    SELECT 1 FROM memberships membership
    JOIN roles role ON role.id = membership.role_id
    WHERE membership.user_id::text = current_setting('app.current_user_id', true)
      AND membership.tenant_id::text = current_setting('app.current_tenant_id', true)
      AND membership.status = 'active'
      AND role.name = 'owner'
)
""".strip()

_LEGACY_ACTIVITY_FUNCTION_DDL = """
CREATE OR REPLACE FUNCTION public.erp_endpoint_has_legacy_activity(p_endpoint_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
    SELECT EXISTS (
        SELECT 1
        FROM public.erp_endpoints endpoint
        WHERE endpoint.id = $1
          AND endpoint.binding_generation = 0
          AND endpoint.adapter = 'express'
          AND endpoint.user_id::text = pg_catalog.current_setting('app.current_user_id', true)
          AND (
              endpoint.tenant_id IS NULL
              OR endpoint.tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
          )
          AND EXISTS (
              SELECT 1
              FROM public.erp_push_logs push_log
              WHERE push_log.endpoint_id = endpoint.id
                AND (
                    push_log.status IN ('pending', 'retrying')
                    OR push_log.next_retry_at IS NOT NULL
                    OR push_log.lease_owner IS NOT NULL
                )
          )
    )
$pearnly$
""".strip()

_LEGACY_ACTIVITY_FUNCTION_GRANT_DDL = (
    "REVOKE ALL ON FUNCTION public.erp_endpoint_has_legacy_activity(uuid) FROM PUBLIC",
    """
DO $pearnly$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'pearnly_app') THEN
        EXECUTE 'GRANT EXECUTE ON FUNCTION public.erp_endpoint_has_legacy_activity(uuid) TO pearnly_app';
    END IF;
END
$pearnly$
""".strip(),
)

_PROMOTION_GUARD_FUNCTION_DDL = """
CREATE OR REPLACE FUNCTION public.guard_erp_endpoint_enrollment_columns()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
BEGIN
    IF OLD.binding_generation = 0 AND NEW.binding_generation = 1 THEN
        IF NEW.id IS DISTINCT FROM OLD.id
           OR NEW.user_id IS DISTINCT FROM OLD.user_id
           OR NEW.name IS DISTINCT FROM OLD.name
           OR NEW.adapter IS DISTINCT FROM OLD.adapter
           OR NEW.config IS DISTINCT FROM OLD.config
           OR NEW.is_default IS DISTINCT FROM OLD.is_default
           OR NEW.auto_push IS DISTINCT FROM OLD.auto_push
           OR NEW.enabled IS DISTINCT FROM OLD.enabled
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
        THEN
            RAISE EXCEPTION 'ERP endpoint enrollment may only change binding columns';
        END IF;
    END IF;
    RETURN NEW;
END
$pearnly$
""".strip()

_PROMOTION_GUARD_REVOKE_DDL = (
    "REVOKE ALL ON FUNCTION " "public.guard_erp_endpoint_enrollment_columns() FROM PUBLIC"
)

_PROMOTION_GUARD_TRIGGER_DDL = """
DO $pearnly$
DECLARE
    v_enabled "char";
    v_tgtype SMALLINT;
    v_tgattr TEXT;
    v_has_when BOOLEAN;
    v_function OID;
BEGIN
    SELECT trigger_meta.tgenabled,
           trigger_meta.tgtype,
           trigger_meta.tgattr::text,
           trigger_meta.tgqual IS NOT NULL,
           trigger_meta.tgfoid
      INTO v_enabled, v_tgtype, v_tgattr, v_has_when, v_function
      FROM pg_trigger trigger_meta
     WHERE trigger_meta.tgrelid = 'erp_endpoints'::regclass
       AND trigger_meta.tgname = 'erp_endpoints_enrollment_columns_guard'
       AND NOT trigger_meta.tgisinternal;
    IF NOT FOUND THEN
        CREATE TRIGGER erp_endpoints_enrollment_columns_guard
        BEFORE UPDATE ON public.erp_endpoints
        FOR EACH ROW
        EXECUTE FUNCTION public.guard_erp_endpoint_enrollment_columns();
    ELSIF v_enabled IS DISTINCT FROM 'O'
       OR v_tgtype IS DISTINCT FROM 19
       OR v_tgattr IS DISTINCT FROM ''
       OR v_has_when
       OR v_function IS DISTINCT FROM 'public.guard_erp_endpoint_enrollment_columns()'::regprocedure
    THEN
        RAISE EXCEPTION
            'erp_endpoints_enrollment_columns_guard does not match the enrollment contract';
    END IF;
END
$pearnly$
""".strip()


SHARED_EXPRESS_ENROLLMENT_RLS_DDL = (
    _LEGACY_ACTIVITY_FUNCTION_DDL,
    *_LEGACY_ACTIVITY_FUNCTION_GRANT_DDL,
    _PROMOTION_GUARD_FUNCTION_DDL,
    _PROMOTION_GUARD_REVOKE_DDL,
    _PROMOTION_GUARD_TRIGGER_DDL,
    "ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY",
    "DROP POLICY IF EXISTS erp_endpoints_shared_express_enroll ON erp_endpoints",
    "CREATE POLICY erp_endpoints_shared_express_enroll ON erp_endpoints "
    "FOR UPDATE USING (" + _PROMOTION_USING + ") WITH CHECK (" + _PROMOTION_CHECK + ")",
)

SHARED_EXPRESS_ENROLLMENT_DDL = SHARED_EXPRESS_ENROLLMENT_RLS_DDL


def apply_shared_express_enrollment_rls(cur) -> None:
    for statement in SHARED_EXPRESS_ENROLLMENT_RLS_DDL:
        cur.execute(statement)


def ensure_shared_express_enrollment_rls() -> None:
    """Install the promotion policy independently from other startup ensures."""
    global _ENROLLMENT_RLS_READY
    try:
        with db.get_cursor(commit=True) as cur:
            apply_shared_express_enrollment_rls(cur)
    except Exception:
        _ENROLLMENT_RLS_READY = False
        raise
    _ENROLLMENT_RLS_READY = True
