# -*- coding: utf-8 -*-
"""Canonical SQL for the managed Express live-profile writer."""

LIVE_DDL = (
    """
CREATE OR REPLACE FUNCTION public.erp_managed_live_authenticate(p_endpoint_id uuid, p_token_digest text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $pearnly$
DECLARE v_endpoint jsonb;
BEGIN
    SELECT jsonb_build_object(
        'tenant_id', endpoint.tenant_id, 'enabled', endpoint.enabled,
        'shared_scope', endpoint.shared_scope,
        'workspace_client_id', endpoint.workspace_client_id, 'binding_generation', endpoint.binding_generation,
        'bound_account_set', endpoint.bound_account_set,
        'bound_profile_key', endpoint.bound_profile_key
    ) INTO v_endpoint
      FROM public.erp_endpoints endpoint
     WHERE endpoint.id = p_endpoint_id
       AND endpoint.config ->> 'agent_token_hash' = p_token_digest
       AND endpoint.adapter = 'express' AND endpoint.binding_generation > 0
       AND endpoint.revoked_at IS NULL AND endpoint.tenant_id IS NOT NULL
       AND endpoint.workspace_client_id IS NOT NULL AND endpoint.shared_scope = TRUE
       AND EXISTS (SELECT 1 FROM public.tenants tenant
                   WHERE tenant.id = endpoint.tenant_id AND tenant.status IN ('active', 'warning'))
       AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                   WHERE workspace.id = endpoint.workspace_client_id
                     AND workspace.tenant_id = endpoint.tenant_id AND workspace.is_active = TRUE)
     LIMIT 1 FOR UPDATE;
    RETURN v_endpoint;
END
$pearnly$
""".strip(),
    "REVOKE ALL ON FUNCTION public.erp_managed_live_authenticate(uuid, text) FROM PUBLIC",
    """
DO $pearnly$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'pearnly_app') THEN
        GRANT EXECUTE ON FUNCTION public.erp_managed_live_authenticate(uuid, text) TO pearnly_app;
    END IF;
END
$pearnly$
""".strip(),
    """
CREATE OR REPLACE FUNCTION public.guard_erp_endpoint_managed_live_columns()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $pearnly$
BEGIN
    IF OLD.binding_generation = 0 THEN RETURN NEW; END IF;
    IF pg_catalog.current_setting('app.erp_managed_live_heartbeat', true) <> 'on'
       OR pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true) <> OLD.id::text
       OR pg_catalog.current_setting('app.erp_managed_live_tenant_id', true) <> OLD.tenant_id::text
       OR pg_catalog.current_setting('app.current_tenant_id', true) <> OLD.tenant_id::text
       OR pg_catalog.current_setting('app.current_workspace_id', true) <> COALESCE(OLD.workspace_client_id::text, '')
       OR pg_catalog.current_setting('app.erp_managed_live_generation', true) <> OLD.binding_generation::text
       OR OLD.adapter <> 'express' OR NOT OLD.enabled OR NOT OLD.shared_scope
       OR OLD.revoked_at IS NOT NULL OR OLD.tenant_id IS NULL OR OLD.workspace_client_id IS NULL
       OR NOT EXISTS (SELECT 1 FROM public.tenants tenant
                      WHERE tenant.id = OLD.tenant_id AND tenant.status IN ('active', 'warning'))
       OR NOT EXISTS (SELECT 1 FROM public.workspace_clients workspace
                      WHERE workspace.id = OLD.workspace_client_id
                        AND workspace.tenant_id = OLD.tenant_id AND workspace.is_active = TRUE)
    THEN RAISE EXCEPTION 'erp.managed_live_gate_required'; END IF;
    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.name IS DISTINCT FROM OLD.name OR NEW.adapter IS DISTINCT FROM OLD.adapter
       OR NEW.config IS DISTINCT FROM OLD.config OR NEW.is_default IS DISTINCT FROM OLD.is_default
       OR NEW.auto_push IS DISTINCT FROM OLD.auto_push OR NEW.enabled IS DISTINCT FROM OLD.enabled
       OR NEW.last_used_at IS DISTINCT FROM OLD.last_used_at OR NEW.last_status IS DISTINCT FROM OLD.last_status
       OR NEW.success_count IS DISTINCT FROM OLD.success_count OR NEW.failure_count IS DISTINCT FROM OLD.failure_count
       OR NEW.created_at IS DISTINCT FROM OLD.created_at OR NEW.updated_at IS DISTINCT FROM OLD.updated_at
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.workspace_client_id IS DISTINCT FROM OLD.workspace_client_id
       OR NEW.shared_scope IS DISTINCT FROM OLD.shared_scope OR NEW.bound_account_set IS DISTINCT FROM OLD.bound_account_set
       OR NEW.bound_profile_key IS DISTINCT FROM OLD.bound_profile_key OR NEW.binding_generation IS DISTINCT FROM OLD.binding_generation
       OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by
    THEN RAISE EXCEPTION 'erp.managed_live_only_typed_fields'; END IF;
    RETURN NEW;
END
$pearnly$
""".strip(),
    """
CREATE OR REPLACE FUNCTION public.guard_erp_endpoint_managed_profile_confirm()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $pearnly$
BEGIN
    IF OLD.binding_generation = 0 THEN RETURN NEW; END IF;
    IF pg_catalog.current_setting('app.erp_endpoint_lifecycle', true) = 'on' THEN
        IF NEW.bound_account_set IS DISTINCT FROM OLD.bound_account_set
           OR NEW.bound_profile_key IS DISTINCT FROM OLD.bound_profile_key
           OR NEW.live_account_set IS DISTINCT FROM OLD.live_account_set
           OR NEW.live_profile_key IS DISTINCT FROM OLD.live_profile_key
           OR NEW.agent_last_seen_at IS DISTINCT FROM OLD.agent_last_seen_at
           OR NEW.agent_version IS DISTINCT FROM OLD.agent_version
        THEN RAISE EXCEPTION 'erp.managed_live_lifecycle_profile_immutable'; END IF;
        RETURN NEW;
    END IF;
    IF pg_catalog.current_setting('app.erp_managed_live_confirm', true) <> 'on'
       OR pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true) <> OLD.id::text
       OR pg_catalog.current_setting('app.erp_managed_live_tenant_id', true) <> OLD.tenant_id::text
       OR pg_catalog.current_setting('app.current_tenant_id', true) <> OLD.tenant_id::text
       OR pg_catalog.current_setting('app.current_workspace_id', true) <> COALESCE(OLD.workspace_client_id::text, '')
       OR pg_catalog.current_setting('app.erp_managed_live_actor_id', true) <> pg_catalog.current_setting('app.current_user_id', true)
       OR pg_catalog.current_setting('app.erp_managed_live_expected_generation', true) <> OLD.binding_generation::text
       OR OLD.adapter <> 'express' OR NOT OLD.enabled OR NOT OLD.shared_scope
       OR OLD.revoked_at IS NOT NULL OR OLD.tenant_id IS NULL OR OLD.workspace_client_id IS NULL
       OR NOT EXISTS (SELECT 1 FROM public.tenants tenant
                      WHERE tenant.id = OLD.tenant_id AND tenant.status IN ('active', 'warning'))
       OR NOT EXISTS (SELECT 1 FROM public.workspace_clients workspace
                      WHERE workspace.id = OLD.workspace_client_id
                        AND workspace.tenant_id = OLD.tenant_id AND workspace.is_active = TRUE)
    THEN RAISE EXCEPTION 'erp.managed_live_confirm_gate_required'; END IF;
    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.name IS DISTINCT FROM OLD.name OR NEW.adapter IS DISTINCT FROM OLD.adapter
       OR NEW.config IS DISTINCT FROM OLD.config OR NEW.is_default IS DISTINCT FROM OLD.is_default
       OR NEW.auto_push IS DISTINCT FROM OLD.auto_push OR NEW.enabled IS DISTINCT FROM OLD.enabled
       OR NEW.last_used_at IS DISTINCT FROM OLD.last_used_at OR NEW.last_status IS DISTINCT FROM OLD.last_status
       OR NEW.success_count IS DISTINCT FROM OLD.success_count OR NEW.failure_count IS DISTINCT FROM OLD.failure_count
       OR NEW.created_at IS DISTINCT FROM OLD.created_at OR NEW.updated_at IS DISTINCT FROM OLD.updated_at
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.workspace_client_id IS DISTINCT FROM OLD.workspace_client_id
       OR NEW.shared_scope IS DISTINCT FROM OLD.shared_scope OR NEW.live_account_set IS DISTINCT FROM OLD.live_account_set
       OR NEW.live_profile_key IS DISTINCT FROM OLD.live_profile_key OR NEW.agent_last_seen_at IS DISTINCT FROM OLD.agent_last_seen_at
       OR NEW.agent_version IS DISTINCT FROM OLD.agent_version OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
       OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by
       OR NEW.binding_generation <> OLD.binding_generation + 1
       OR NEW.bound_account_set IS DISTINCT FROM NEW.live_account_set
       OR NEW.bound_profile_key IS DISTINCT FROM NEW.live_profile_key
    THEN RAISE EXCEPTION 'erp.managed_live_confirm_only_profile'; END IF;
    RETURN NEW;
END
$pearnly$
""".strip(),
    "REVOKE ALL ON FUNCTION public.guard_erp_endpoint_managed_live_columns() FROM PUBLIC",
    "REVOKE ALL ON FUNCTION public.guard_erp_endpoint_managed_profile_confirm() FROM PUBLIC",
    """
DROP TRIGGER IF EXISTS erp_endpoints_managed_live_columns_guard ON public.erp_endpoints;
CREATE TRIGGER erp_endpoints_managed_live_columns_guard
BEFORE UPDATE OF live_account_set, live_profile_key, agent_last_seen_at, agent_version
ON public.erp_endpoints FOR EACH ROW
EXECUTE FUNCTION public.guard_erp_endpoint_managed_live_columns()
""".strip(),
    """
DROP TRIGGER IF EXISTS erp_endpoints_managed_profile_confirm_guard ON public.erp_endpoints;
CREATE TRIGGER erp_endpoints_managed_profile_confirm_guard
BEFORE UPDATE OF bound_account_set, bound_profile_key, binding_generation
ON public.erp_endpoints FOR EACH ROW
EXECUTE FUNCTION public.guard_erp_endpoint_managed_profile_confirm()
""".strip(),
    """
DROP POLICY IF EXISTS erp_endpoints_managed_live_select ON public.erp_endpoints;
CREATE POLICY erp_endpoints_managed_live_select ON public.erp_endpoints FOR SELECT
USING (
    pg_catalog.current_setting('app.erp_managed_live_heartbeat', true) = 'on'
    AND id::text = pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
    AND workspace_client_id::text = pg_catalog.current_setting('app.current_workspace_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.erp_managed_live_tenant_id', true)
    AND binding_generation::text = pg_catalog.current_setting('app.erp_managed_live_generation', true)
    AND adapter = 'express' AND binding_generation > 0 AND revoked_at IS NULL
    AND enabled AND shared_scope
    AND workspace_client_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM public.tenants tenant
                WHERE tenant.id = erp_endpoints.tenant_id AND tenant.status IN ('active', 'warning'))
    AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                WHERE workspace.id = erp_endpoints.workspace_client_id
                  AND workspace.tenant_id = erp_endpoints.tenant_id AND workspace.is_active)
)
""".strip(),
    """
DROP POLICY IF EXISTS erp_endpoints_managed_live_update ON public.erp_endpoints;
CREATE POLICY erp_endpoints_managed_live_update ON public.erp_endpoints FOR UPDATE
USING (
    pg_catalog.current_setting('app.erp_managed_live_heartbeat', true) = 'on'
    AND id::text = pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.erp_managed_live_tenant_id', true)
    AND binding_generation::text = pg_catalog.current_setting('app.erp_managed_live_generation', true)
    AND adapter = 'express' AND binding_generation > 0 AND revoked_at IS NULL
    AND enabled AND shared_scope AND workspace_client_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM public.tenants tenant
                WHERE tenant.id = erp_endpoints.tenant_id AND tenant.status IN ('active', 'warning'))
    AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                WHERE workspace.id = erp_endpoints.workspace_client_id
                  AND workspace.tenant_id = erp_endpoints.tenant_id AND workspace.is_active)
)
WITH CHECK (
    (pg_catalog.current_setting('app.erp_managed_live_heartbeat', true) = 'on'
     OR pg_catalog.current_setting('app.erp_managed_live_confirm', true) = 'on')
    AND id::text = pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.erp_managed_live_tenant_id', true)
    AND ((pg_catalog.current_setting('app.erp_managed_live_heartbeat', true) = 'on'
          AND binding_generation::text = pg_catalog.current_setting('app.erp_managed_live_generation', true))
         OR (pg_catalog.current_setting('app.erp_managed_live_confirm', true) = 'on'
             AND binding_generation::text = (NULLIF(pg_catalog.current_setting('app.erp_managed_live_expected_generation', true), '')::bigint + 1)::text))
    AND adapter = 'express' AND binding_generation > 0 AND revoked_at IS NULL
    AND enabled AND shared_scope
    AND EXISTS (SELECT 1 FROM public.tenants tenant
                WHERE tenant.id = erp_endpoints.tenant_id AND tenant.status IN ('active', 'warning'))
    AND workspace_client_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                WHERE workspace.id = erp_endpoints.workspace_client_id
                  AND workspace.tenant_id = erp_endpoints.tenant_id AND workspace.is_active)
)
""".strip(),
    """
DROP POLICY IF EXISTS erp_endpoints_managed_live_confirm ON public.erp_endpoints;
CREATE POLICY erp_endpoints_managed_live_confirm ON public.erp_endpoints FOR UPDATE
USING (
    pg_catalog.current_setting('app.erp_managed_live_confirm', true) = 'on'
    AND id::text = pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.erp_managed_live_tenant_id', true)
    AND workspace_client_id::text = pg_catalog.current_setting('app.current_workspace_id', true)
    AND binding_generation::text = pg_catalog.current_setting('app.erp_managed_live_expected_generation', true)
    AND adapter = 'express' AND binding_generation > 0 AND revoked_at IS NULL
    AND enabled AND shared_scope AND workspace_client_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM public.tenants tenant
                WHERE tenant.id = erp_endpoints.tenant_id AND tenant.status IN ('active', 'warning'))
    AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                WHERE workspace.id = erp_endpoints.workspace_client_id
                  AND workspace.tenant_id = erp_endpoints.tenant_id AND workspace.is_active)
    AND EXISTS (SELECT 1 FROM public.users actor JOIN public.memberships membership ON membership.user_id = actor.id
                JOIN public.roles role ON role.id = membership.role_id
                WHERE actor.id::text = pg_catalog.current_setting('app.current_user_id', true)
                  AND actor.id::text = pg_catalog.current_setting('app.erp_managed_live_actor_id', true)
                  AND actor.tenant_id = erp_endpoints.tenant_id AND actor.is_active
                  AND membership.tenant_id = erp_endpoints.tenant_id AND membership.status = 'active'
                  AND role.name = 'owner')
)
WITH CHECK (
    pg_catalog.current_setting('app.erp_managed_live_confirm', true) = 'on'
    AND id::text = pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.erp_managed_live_tenant_id', true)
    AND workspace_client_id::text = pg_catalog.current_setting('app.current_workspace_id', true)
    AND binding_generation::text = (NULLIF(pg_catalog.current_setting('app.erp_managed_live_expected_generation', true), '')::bigint + 1)::text
    AND adapter = 'express' AND enabled AND shared_scope AND revoked_at IS NULL
    AND EXISTS (SELECT 1 FROM public.tenants tenant
                WHERE tenant.id = erp_endpoints.tenant_id AND tenant.status IN ('active', 'warning'))
    AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                WHERE workspace.id = erp_endpoints.workspace_client_id
                  AND workspace.tenant_id = erp_endpoints.tenant_id AND workspace.is_active)
    AND bound_account_set IS NOT DISTINCT FROM live_account_set
    AND bound_profile_key IS NOT DISTINCT FROM live_profile_key
)
""".strip(),
    """
DROP POLICY IF EXISTS erp_endpoints_managed_live_confirm_select ON public.erp_endpoints;
CREATE POLICY erp_endpoints_managed_live_confirm_select ON public.erp_endpoints FOR SELECT
USING (
    pg_catalog.current_setting('app.erp_managed_live_confirm', true) = 'on'
    AND id::text = pg_catalog.current_setting('app.erp_managed_live_endpoint_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
    AND tenant_id::text = pg_catalog.current_setting('app.erp_managed_live_tenant_id', true)
    AND binding_generation::text IN (
        pg_catalog.current_setting('app.erp_managed_live_expected_generation', true),
        (NULLIF(pg_catalog.current_setting('app.erp_managed_live_expected_generation', true), '')::bigint + 1)::text
    )
    AND adapter = 'express' AND binding_generation > 0 AND revoked_at IS NULL
    AND enabled AND shared_scope
    AND EXISTS (SELECT 1 FROM public.tenants tenant
                WHERE tenant.id = erp_endpoints.tenant_id AND tenant.status IN ('active', 'warning'))
    AND workspace_client_id::text = pg_catalog.current_setting('app.current_workspace_id', true)
    AND EXISTS (SELECT 1 FROM public.workspace_clients workspace
                WHERE workspace.id = erp_endpoints.workspace_client_id
                  AND workspace.tenant_id = erp_endpoints.tenant_id AND workspace.is_active)
    AND EXISTS (SELECT 1 FROM public.users actor JOIN public.memberships membership ON membership.user_id = actor.id
                JOIN public.roles role ON role.id = membership.role_id
                WHERE actor.id::text = pg_catalog.current_setting('app.current_user_id', true)
                  AND actor.id::text = pg_catalog.current_setting('app.erp_managed_live_actor_id', true)
                  AND actor.tenant_id = erp_endpoints.tenant_id AND actor.is_active
                  AND membership.tenant_id = erp_endpoints.tenant_id AND membership.status = 'active'
                  AND role.name = 'owner')
)
""".strip(),
    """
DO $pearnly$
DECLARE v_cfg text[]; v_trigger boolean; v_policy boolean; v_security_definer boolean;
BEGIN
    SELECT p.proconfig, p.prosecdef INTO v_cfg, v_security_definer FROM pg_catalog.pg_proc p
     WHERE p.oid = 'public.erp_managed_live_authenticate(uuid, text)'::pg_catalog.regprocedure;
    IF v_cfg IS DISTINCT FROM ARRAY['search_path=pg_catalog']::text[] OR v_security_definer IS DISTINCT FROM TRUE
    THEN RAISE EXCEPTION 'managed live auth security contract mismatch'; END IF;
    IF pg_catalog.has_function_privilege('public', 'public.erp_managed_live_authenticate(uuid, text)', 'EXECUTE') THEN RAISE EXCEPTION 'managed live auth ACL mismatch'; END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'pearnly_app')
       AND NOT pg_catalog.has_function_privilege('pearnly_app', 'public.erp_managed_live_authenticate(uuid, text)', 'EXECUTE')
    THEN RAISE EXCEPTION 'managed live app ACL mismatch'; END IF;
    SELECT p.proconfig INTO v_cfg FROM pg_catalog.pg_proc p
     WHERE p.oid = 'public.guard_erp_endpoint_managed_live_columns()'::pg_catalog.regprocedure;
    IF v_cfg IS DISTINCT FROM ARRAY['search_path=pg_catalog']::text[] THEN RAISE EXCEPTION 'managed live trigger search_path mismatch'; END IF;
    IF pg_catalog.has_function_privilege('public', 'public.guard_erp_endpoint_managed_live_columns()', 'EXECUTE') THEN RAISE EXCEPTION 'managed live trigger ACL mismatch'; END IF;
    SELECT p.proconfig INTO v_cfg FROM pg_catalog.pg_proc p
     WHERE p.oid = 'public.guard_erp_endpoint_managed_profile_confirm()'::pg_catalog.regprocedure;
    IF v_cfg IS DISTINCT FROM ARRAY['search_path=pg_catalog']::text[] THEN RAISE EXCEPTION 'managed profile confirm trigger search_path mismatch'; END IF;
    IF pg_catalog.has_function_privilege('public', 'public.guard_erp_endpoint_managed_profile_confirm()', 'EXECUTE') THEN RAISE EXCEPTION 'managed profile confirm trigger ACL mismatch'; END IF;
    SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_trigger t WHERE t.tgrelid = 'public.erp_endpoints'::regclass AND t.tgname = 'erp_endpoints_managed_live_columns_guard' AND NOT t.tgisinternal) INTO v_trigger;
    IF NOT v_trigger THEN RAISE EXCEPTION 'managed live trigger missing'; END IF;
    SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_trigger t WHERE t.tgrelid = 'public.erp_endpoints'::regclass AND t.tgname = 'erp_endpoints_managed_profile_confirm_guard' AND NOT t.tgisinternal) INTO v_trigger;
    IF NOT v_trigger THEN RAISE EXCEPTION 'managed profile confirm trigger missing'; END IF;
    SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_policy p WHERE p.polrelid = 'public.erp_endpoints'::regclass AND p.polname = 'erp_endpoints_managed_live_update' AND position('app.erp_managed_live_generation' IN pg_catalog.pg_get_expr(p.polqual, p.polrelid)) > 0) INTO v_policy;
    IF NOT v_policy THEN RAISE EXCEPTION 'managed live policy missing'; END IF;
END
$pearnly$
""".strip(),
)
