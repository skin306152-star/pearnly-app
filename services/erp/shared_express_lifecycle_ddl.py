# -*- coding: utf-8 -*-
"""SQL archive for the managed Express endpoint lifecycle schema."""

LIFECYCLE_POLICY_DDL = (
    "DROP POLICY IF EXISTS erp_endpoints_managed_lifecycle_select ON erp_endpoints",
    """CREATE POLICY erp_endpoints_managed_lifecycle_select ON erp_endpoints
       FOR SELECT
       USING (
           current_setting('app.erp_endpoint_lifecycle', true) = 'on'
           AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_action', true) IN ('rebind', 'enable', 'disable', 'revoke')
           AND erp_endpoints.id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_expected_generation', true) ~ '^[1-9][0-9]*$'
           AND erp_endpoints.tenant_id::text = current_setting('app.current_tenant_id', true)
           AND EXISTS (SELECT 1 FROM users lifecycle_actor
               JOIN memberships lifecycle_membership ON lifecycle_membership.user_id = lifecycle_actor.id
               JOIN roles lifecycle_role ON lifecycle_role.id = lifecycle_membership.role_id
               WHERE lifecycle_actor.id::text = current_setting('app.current_user_id', true)
                 AND lifecycle_actor.tenant_id = erp_endpoints.tenant_id AND lifecycle_actor.is_active = TRUE
                 AND lifecycle_membership.tenant_id = erp_endpoints.tenant_id
                 AND lifecycle_membership.status = 'active' AND lifecycle_role.name = 'owner')
           AND (
               (erp_endpoints.binding_generation::text = current_setting('app.erp_endpoint_lifecycle_expected_generation', true)
                AND erp_endpoints.binding_generation > 0 AND erp_endpoints.adapter = 'express'
                AND erp_endpoints.revoked_at IS NULL
                AND current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) = COALESCE(erp_endpoints.workspace_client_id::text, '')
                AND EXISTS (SELECT 1 FROM workspace_clients source_workspace
                    WHERE source_workspace.id = erp_endpoints.workspace_client_id
                      AND source_workspace.tenant_id = erp_endpoints.tenant_id AND source_workspace.is_active = TRUE))
               OR (erp_endpoints.binding_generation::text = (current_setting('app.erp_endpoint_lifecycle_expected_generation', true)::bigint + 1)::text
                AND erp_endpoints.binding_generation > 0 AND erp_endpoints.adapter = 'express'
                AND (
                    (current_setting('app.erp_endpoint_lifecycle_action', true) IN ('enable', 'disable')
                     AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                     AND erp_endpoints.workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                     AND erp_endpoints.enabled = (current_setting('app.erp_endpoint_lifecycle_action', true) = 'enable')
                     AND erp_endpoints.shared_scope = TRUE AND erp_endpoints.revoked_at IS NULL AND erp_endpoints.revoked_by IS NULL
                     AND EXISTS (SELECT 1 FROM workspace_clients source_workspace
                         WHERE source_workspace.id = erp_endpoints.workspace_client_id
                           AND source_workspace.tenant_id = erp_endpoints.tenant_id AND source_workspace.is_active = TRUE))
                    OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'rebind'
                     AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) <> ''
                     AND erp_endpoints.workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true)
                     AND erp_endpoints.enabled = FALSE AND erp_endpoints.shared_scope = TRUE
                     AND erp_endpoints.revoked_at IS NULL AND erp_endpoints.revoked_by IS NULL
                     AND EXISTS (SELECT 1 FROM workspace_clients target_workspace
                         WHERE target_workspace.id = erp_endpoints.workspace_client_id
                           AND target_workspace.tenant_id = erp_endpoints.tenant_id AND target_workspace.is_active = TRUE))
                    OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'revoke'
                     AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = ''
                     AND erp_endpoints.workspace_client_id IS NULL AND erp_endpoints.enabled = FALSE
                     AND erp_endpoints.shared_scope = FALSE AND erp_endpoints.revoked_at IS NOT NULL
                     AND erp_endpoints.revoked_by::text = current_setting('app.erp_endpoint_lifecycle_actor_id', true))
                ))
           )
       )""",
    "DROP POLICY IF EXISTS erp_endpoints_managed_lifecycle_update ON erp_endpoints",
    """CREATE POLICY erp_endpoints_managed_lifecycle_update ON erp_endpoints
       FOR UPDATE
       USING (
           current_setting('app.erp_endpoint_lifecycle', true) = 'on'
           AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_action', true) IN ('rebind', 'enable', 'disable', 'revoke')
           AND erp_endpoints.id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) = COALESCE(erp_endpoints.workspace_client_id::text, '')
           AND current_setting('app.erp_endpoint_lifecycle_expected_generation', true) ~ '^[1-9][0-9]*$'
           AND erp_endpoints.binding_generation >= current_setting('app.erp_endpoint_lifecycle_expected_generation', true)::bigint
           AND erp_endpoints.binding_generation > 0 AND erp_endpoints.adapter = 'express' AND erp_endpoints.revoked_at IS NULL
           AND erp_endpoints.tenant_id::text = current_setting('app.current_tenant_id', true)
           AND EXISTS (SELECT 1 FROM workspace_clients source_workspace
               WHERE source_workspace.id = erp_endpoints.workspace_client_id
                 AND source_workspace.tenant_id = erp_endpoints.tenant_id AND source_workspace.is_active = TRUE)
           AND EXISTS (SELECT 1 FROM users lifecycle_actor
               JOIN memberships lifecycle_membership ON lifecycle_membership.user_id = lifecycle_actor.id
               JOIN roles lifecycle_role ON lifecycle_role.id = lifecycle_membership.role_id
               WHERE lifecycle_actor.id::text = current_setting('app.current_user_id', true)
                 AND lifecycle_actor.tenant_id = erp_endpoints.tenant_id AND lifecycle_actor.is_active = TRUE
                 AND lifecycle_membership.tenant_id = erp_endpoints.tenant_id
                 AND lifecycle_membership.status = 'active' AND lifecycle_role.name = 'owner')
       )
       WITH CHECK (
           current_setting('app.erp_endpoint_lifecycle', true) = 'on'
           AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
           AND erp_endpoints.id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
           AND current_setting('app.erp_endpoint_lifecycle_expected_generation', true) ~ '^[1-9][0-9]*$'
           AND erp_endpoints.binding_generation::text = (current_setting('app.erp_endpoint_lifecycle_expected_generation', true)::bigint + 1)::text
           AND erp_endpoints.binding_generation > 0 AND erp_endpoints.adapter = 'express'
           AND erp_endpoints.tenant_id::text = current_setting('app.current_tenant_id', true)
           AND (
               (current_setting('app.erp_endpoint_lifecycle_action', true) = 'rebind'
                AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) <> ''
                AND erp_endpoints.workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true)
                AND erp_endpoints.enabled = FALSE AND erp_endpoints.shared_scope = TRUE
                AND erp_endpoints.revoked_at IS NULL AND erp_endpoints.revoked_by IS NULL
                AND EXISTS (SELECT 1 FROM workspace_clients target_workspace
                    WHERE target_workspace.id = erp_endpoints.workspace_client_id
                      AND target_workspace.tenant_id = erp_endpoints.tenant_id AND target_workspace.is_active = TRUE))
               OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'enable'
                AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                AND erp_endpoints.workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                AND erp_endpoints.enabled = TRUE AND erp_endpoints.shared_scope = TRUE
                AND erp_endpoints.revoked_at IS NULL AND erp_endpoints.revoked_by IS NULL)
               OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'disable'
                AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                AND erp_endpoints.workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                AND erp_endpoints.enabled = FALSE AND erp_endpoints.shared_scope = TRUE
                AND erp_endpoints.revoked_at IS NULL AND erp_endpoints.revoked_by IS NULL)
               OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'revoke'
                AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = ''
                AND erp_endpoints.workspace_client_id IS NULL AND erp_endpoints.enabled = FALSE
                AND erp_endpoints.shared_scope = FALSE AND erp_endpoints.revoked_at IS NOT NULL
                AND erp_endpoints.revoked_by::text = current_setting('app.erp_endpoint_lifecycle_actor_id', true))
           )
       )""",
)

INDEX_CONTRACT_DDL = """
DO $pearnly$
DECLARE v_unique boolean; v_keys smallint; v_definition text; v_predicate text; v_duplicate boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1
          FROM operation_logs
         WHERE target_type = 'erp_endpoint'
           AND action IN ('erp.endpoint.rebind', 'erp.endpoint.enable', 'erp.endpoint.disable', 'erp.endpoint.revoke')
           AND details ? 'operation_id'
         GROUP BY tenant_id, (details ->> 'operation_id')
        HAVING count(*) > 1
    ) INTO v_duplicate;
    IF v_duplicate THEN
        RAISE EXCEPTION 'duplicate tenant operation_id prevents lifecycle index contract';
    END IF;
    SELECT index_meta.indisunique, index_meta.indnkeyatts, pg_get_indexdef(index_meta.indexrelid), pg_get_expr(index_meta.indpred, index_meta.indrelid)
      INTO v_unique, v_keys, v_definition, v_predicate
      FROM pg_catalog.pg_index index_meta
     WHERE index_meta.indexrelid = pg_catalog.to_regclass('uq_operation_logs_erp_endpoint_lifecycle_operation');
    IF NOT FOUND THEN
        CREATE UNIQUE INDEX uq_operation_logs_erp_endpoint_lifecycle_operation
          ON operation_logs (tenant_id, (details ->> 'operation_id'))
          WHERE target_type = 'erp_endpoint' AND action IN ('erp.endpoint.rebind', 'erp.endpoint.enable', 'erp.endpoint.disable', 'erp.endpoint.revoke')
            AND details ? 'operation_id';
    ELSIF v_unique IS DISTINCT FROM TRUE OR v_keys IS DISTINCT FROM 2
       OR position('tenant_id' IN lower(v_definition)) = 0
       OR position('details ->> ''operation_id''' IN lower(v_definition)) = 0 OR v_predicate IS NULL
       OR position('target_type' IN lower(v_predicate)) = 0 OR position('operation_id' IN lower(v_predicate)) = 0
       OR position('erp.endpoint.rebind' IN v_predicate) = 0 OR position('erp.endpoint.enable' IN v_predicate) = 0
       OR position('erp.endpoint.disable' IN v_predicate) = 0 OR position('erp.endpoint.revoke' IN v_predicate) = 0
    THEN RAISE EXCEPTION 'uq_operation_logs_erp_endpoint_lifecycle_operation does not match lifecycle contract'; END IF;
END
$pearnly$
""".strip()

CATALOG_VALIDATION_DDL = """
DO $pearnly$
DECLARE v_type text; v_proconfig text[]; v_trigger_exists boolean; v_policy text; v_select_policy boolean;
    v_constraint_ok boolean;
BEGIN
    SELECT format_type(att.atttypid, att.atttypmod) INTO v_type FROM pg_catalog.pg_attribute att
     WHERE att.attrelid = 'erp_endpoints'::regclass AND att.attname = 'revoked_at' AND att.attnum > 0 AND NOT att.attisdropped;
    IF v_type IS DISTINCT FROM 'timestamp with time zone' THEN RAISE EXCEPTION 'erp_endpoints.revoked_at catalog contract mismatch'; END IF;
    SELECT format_type(att.atttypid, att.atttypmod) INTO v_type FROM pg_catalog.pg_attribute att
     WHERE att.attrelid = 'erp_endpoints'::regclass AND att.attname = 'revoked_by' AND att.attnum > 0 AND NOT att.attisdropped;
    IF v_type IS DISTINCT FROM 'uuid' THEN RAISE EXCEPTION 'erp_endpoints.revoked_by catalog contract mismatch'; END IF;
    SELECT count(*) = 3 AND bool_and(convalidated) FROM pg_catalog.pg_constraint constraint_meta
      WHERE constraint_meta.conrelid = 'erp_endpoints'::regclass
        AND constraint_meta.conname IN ('erp_endpoints_managed_scope_chk', 'erp_endpoints_revoked_pair_chk', 'erp_endpoints_revoked_terminal_chk')
        AND regexp_replace(lower(pg_get_constraintdef(constraint_meta.oid)), '[[:space:]()]', '', 'g') IN (
          'checkbinding_generation=0ortenant_idisnotnullandadapter=''express''::textandworkspace_client_idisnotnullorrevoked_atisnotnull',
          'checkrevoked_atisnull=revoked_byisnull',
          'checkrevoked_atisnullorbinding_generation>0andtenant_idisnotnullandadapter=''express''::textandenabled=falseandshared_scope=falseandworkspace_client_idisnull'
        ) INTO v_constraint_ok;
    IF v_constraint_ok IS DISTINCT FROM TRUE THEN RAISE EXCEPTION 'lifecycle constraint catalog contract mismatch'; END IF;
    SELECT proc.proconfig INTO v_proconfig FROM pg_catalog.pg_proc proc WHERE proc.oid = 'public.guard_erp_endpoint_lifecycle_columns()'::regprocedure;
    IF v_proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog']::text[] OR has_function_privilege('public', 'public.guard_erp_endpoint_lifecycle_columns()', 'EXECUTE')
    THEN RAISE EXCEPTION 'lifecycle trigger function ACL/search_path contract mismatch'; END IF;
    SELECT proc.proconfig INTO v_proconfig FROM pg_catalog.pg_proc proc WHERE proc.oid = 'public.erp_managed_endpoint_has_activity(uuid)'::regprocedure;
    IF v_proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog']::text[] OR has_function_privilege('public', 'public.erp_managed_endpoint_has_activity(uuid)', 'EXECUTE')
    THEN RAISE EXCEPTION 'managed activity helper ACL/search_path contract mismatch'; END IF;
    SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_trigger trigger_meta WHERE trigger_meta.tgrelid = 'erp_endpoints'::regclass
        AND trigger_meta.tgname = 'erp_endpoints_lifecycle_columns_guard' AND NOT trigger_meta.tgisinternal) INTO v_trigger_exists;
    IF NOT v_trigger_exists THEN RAISE EXCEPTION 'lifecycle trigger catalog contract missing'; END IF;
    SELECT pg_get_expr(policy.polqual, policy.polrelid) || pg_get_expr(policy.polwithcheck, policy.polrelid) INTO v_policy
      FROM pg_catalog.pg_policy policy WHERE policy.polrelid = 'erp_endpoints'::regclass AND policy.polname = 'erp_endpoints_managed_lifecycle_update';
    IF v_policy IS NULL OR position('erp_endpoint_lifecycle_expected_generation' IN v_policy) = 0
       OR position('erp_endpoint_lifecycle_source_workspace_id' IN v_policy) = 0 OR position('erp_endpoint_lifecycle_target_workspace_id' IN v_policy) = 0
       OR position('erp_endpoint_lifecycle_action' IN v_policy) = 0 OR position('erp_endpoint_lifecycle_actor_id' IN v_policy) = 0
    THEN RAISE EXCEPTION 'lifecycle policy catalog contract mismatch'; END IF;
    SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_policy policy
        WHERE policy.polrelid = 'erp_endpoints'::regclass
          AND policy.polname = 'erp_endpoints_managed_lifecycle_select'
          AND policy.polpermissive = TRUE AND policy.polcmd = 'r'
          AND position('erp_endpoint_lifecycle_expected_generation' IN pg_get_expr(policy.polqual, policy.polrelid)) > 0
          AND position('erp_endpoint_lifecycle_source_workspace_id' IN pg_get_expr(policy.polqual, policy.polrelid)) > 0
          AND position('erp_endpoint_lifecycle_actor_id' IN pg_get_expr(policy.polqual, policy.polrelid)) > 0) INTO v_select_policy;
    IF NOT v_select_policy THEN RAISE EXCEPTION 'lifecycle select policy catalog contract mismatch'; END IF;
END
$pearnly$
""".strip()
