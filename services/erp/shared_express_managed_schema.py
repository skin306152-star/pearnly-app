"""Database ownership boundary for tenant-managed Express endpoints."""

from __future__ import annotations

from core import db
from psycopg2.extensions import adapt

MANAGED_EXPRESS_GATE_GUC = "app.erp_managed_express_owner"
MANAGED_EXPRESS_TENANT_GUC = "app.erp_managed_express_tenant_id"
MANAGED_EXPRESS_WORKSPACE_GUC = "app.erp_managed_express_workspace_id"
MANAGED_EXPRESS_ACTOR_GUC = "app.erp_managed_express_actor_id"

# None means startup has not attempted ensure; only success enables shared branches.
_MANAGED_FOUNDATION_READY: bool | None = None


def managed_foundation_ready() -> bool:
    return _MANAGED_FOUNDATION_READY is True


def _sql_literal(value: str) -> str:
    return adapt(value).getquoted().decode("utf-8")


def _sql_identifier(value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("SQL identifier must be non-empty and NUL-free")
    return '"' + value.replace('"', '""') + '"'


def _check_constraint(
    name: str,
    expression: str,
    normalized: str,
    *,
    compatible: tuple[str, ...] = (),
) -> tuple[str, str]:
    accepted = ", ".join(_sql_literal(value) for value in (normalized, *compatible))
    contract = f"""
DO $pearnly$
DECLARE
    v_definition TEXT;
BEGIN
    SELECT regexp_replace(lower(pg_get_constraintdef(oid)), '[[:space:]()]', '', 'g')
      INTO v_definition
      FROM pg_constraint
     WHERE conrelid = {_sql_literal('erp_endpoints')}::regclass
       AND conname = {_sql_literal(name)};
    IF NOT FOUND THEN
        ALTER TABLE erp_endpoints
            ADD CONSTRAINT {_sql_identifier(name)} CHECK ({expression}) NOT VALID;
    ELSIF v_definition NOT IN ({accepted}) THEN
        RAISE EXCEPTION {_sql_literal(name + ' does not match the F1-B3B2a contract')};
    END IF;
END
$pearnly$
"""
    return contract, f"ALTER TABLE erp_endpoints VALIDATE CONSTRAINT {_sql_identifier(name)}"


_USER_COLUMN_CONTRACT_DDL = """
DO $pearnly$
DECLARE
    v_nullable BOOLEAN;
BEGIN
    SELECT NOT attnotnull
      INTO v_nullable
      FROM pg_attribute
     WHERE attrelid = 'erp_endpoints'::regclass
       AND attname = 'user_id'
       AND attnum > 0
       AND NOT attisdropped;
    IF NOT FOUND OR v_nullable IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'erp_endpoints.user_id must be nullable for managed creator deletion';
    END IF;
END
$pearnly$
"""

_ORPHAN_TENANT_INVENTORY_DDL = """
DO $pearnly$
DECLARE
    v_orphans BIGINT;
BEGIN
    SELECT count(*)
      INTO v_orphans
      FROM erp_endpoints endpoint
      LEFT JOIN tenants tenant ON tenant.id = endpoint.tenant_id
     WHERE endpoint.tenant_id IS NOT NULL
       AND tenant.id IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION
            'erp_endpoints orphan tenant_id blocks managed FK: % row(s)', v_orphans;
    END IF;
END
$pearnly$
"""

_TENANT_FK_CONTRACT_DDL = """
DO $pearnly$
DECLARE
    v_delete "char"; v_valid BOOLEAN; v_columns TEXT[]; v_parent_columns TEXT[];
BEGIN
    SELECT constraint_meta.confdeltype,
           constraint_meta.convalidated,
           ARRAY(
               SELECT attribute.attname::TEXT
                 FROM unnest(constraint_meta.conkey) WITH ORDINALITY key_column(attnum, position)
                 JOIN pg_attribute attribute
                   ON attribute.attrelid = constraint_meta.conrelid
                  AND attribute.attnum = key_column.attnum
                ORDER BY key_column.position
           ),
           ARRAY(
               SELECT attribute.attname::TEXT
                 FROM unnest(constraint_meta.confkey) WITH ORDINALITY key_column(attnum, position)
                 JOIN pg_attribute attribute
                   ON attribute.attrelid = constraint_meta.confrelid
                  AND attribute.attnum = key_column.attnum
                ORDER BY key_column.position
           )
      INTO v_delete, v_valid, v_columns, v_parent_columns
      FROM pg_constraint constraint_meta
     WHERE constraint_meta.conrelid = 'erp_endpoints'::regclass
       AND constraint_meta.conname = 'erp_endpoints_tenant_id_fkey'
       AND constraint_meta.contype = 'f'
       AND constraint_meta.confrelid = 'tenants'::regclass;
    IF NOT FOUND THEN
        ALTER TABLE erp_endpoints
            ADD CONSTRAINT erp_endpoints_tenant_id_fkey
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE NOT VALID;
    ELSIF v_valid IS DISTINCT FROM TRUE
       OR v_delete <> 'c'
       OR v_columns IS DISTINCT FROM ARRAY['tenant_id']::TEXT[]
       OR v_parent_columns IS DISTINCT FROM ARRAY['id']::TEXT[]
    THEN
        RAISE EXCEPTION
            'erp_endpoints_tenant_id_fkey does not match the F1-B3B2a contract';
    END IF;
END
$pearnly$
"""

_USER_FK_CONTRACT_DDL = """
DO $pearnly$
DECLARE
    v_delete "char"; v_valid BOOLEAN; v_columns TEXT[]; v_parent_columns TEXT[];
BEGIN
    SELECT constraint_meta.confdeltype,
           constraint_meta.convalidated,
           ARRAY(
               SELECT attribute.attname::TEXT
                 FROM unnest(constraint_meta.conkey) WITH ORDINALITY key_column(attnum, position)
                 JOIN pg_attribute attribute
                   ON attribute.attrelid = constraint_meta.conrelid
                  AND attribute.attnum = key_column.attnum
                ORDER BY key_column.position
           ),
           ARRAY(
               SELECT attribute.attname::TEXT
                 FROM unnest(constraint_meta.confkey) WITH ORDINALITY key_column(attnum, position)
                 JOIN pg_attribute attribute
                   ON attribute.attrelid = constraint_meta.confrelid
                  AND attribute.attnum = key_column.attnum
                ORDER BY key_column.position
           )
      INTO v_delete, v_valid, v_columns, v_parent_columns
      FROM pg_constraint constraint_meta
     WHERE constraint_meta.conrelid = 'erp_endpoints'::regclass
       AND constraint_meta.conname = 'erp_endpoints_user_id_fkey'
       AND constraint_meta.contype = 'f'
       AND constraint_meta.confrelid = 'users'::regclass;
    IF NOT FOUND
       OR v_valid IS DISTINCT FROM TRUE
       OR v_delete <> 'c'
       OR v_columns IS DISTINCT FROM ARRAY['user_id']::TEXT[]
       OR v_parent_columns IS DISTINCT FROM ARRAY['id']::TEXT[]
    THEN
        RAISE EXCEPTION
            'erp_endpoints_user_id_fkey must remain users(id) ON DELETE CASCADE';
    END IF;
END
$pearnly$
"""

_CREATOR_DELETE_FUNCTION_DDL = """
CREATE OR REPLACE FUNCTION public.preserve_managed_erp_endpoints_on_user_delete()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
BEGIN
    EXECUTE format(
        'UPDATE %I.erp_endpoints '
        'SET user_id = NULL, updated_at = clock_timestamp() '
        'WHERE user_id = $1 AND binding_generation > 0',
        TG_TABLE_SCHEMA
    ) USING OLD.id;
    RETURN OLD;
END
$pearnly$
"""

_CREATOR_DELETE_TRIGGER_DDL = """
DO $pearnly$
DECLARE
    v_definition TEXT; v_security_definer BOOLEAN; v_config TEXT[];
BEGIN
    SELECT procedure_meta.prosecdef, procedure_meta.proconfig
      INTO v_security_definer, v_config
      FROM pg_proc procedure_meta
     WHERE procedure_meta.oid = 'public.preserve_managed_erp_endpoints_on_user_delete()'::regprocedure;
    IF NOT FOUND
       OR v_security_definer IS DISTINCT FROM TRUE
       OR v_config IS DISTINCT FROM ARRAY['search_path=pg_catalog']::TEXT[]
    THEN
        RAISE EXCEPTION
            'preserve_managed_erp_endpoints_on_user_delete must be SECURITY DEFINER with fixed pg_catalog search_path';
    END IF;
    SELECT lower(pg_get_triggerdef(trigger_meta.oid))
      INTO v_definition
      FROM pg_trigger trigger_meta
     WHERE trigger_meta.tgrelid = 'users'::regclass
       AND trigger_meta.tgname = 'erp_endpoints_preserve_managed_creator_delete'
       AND NOT trigger_meta.tgisinternal;
    IF NOT FOUND THEN
        CREATE TRIGGER erp_endpoints_preserve_managed_creator_delete
        BEFORE DELETE ON public.users
        FOR EACH ROW
        EXECUTE FUNCTION public.preserve_managed_erp_endpoints_on_user_delete();
    ELSIF position('before delete on' IN v_definition) = 0
       OR position('for each row' IN v_definition) = 0
       OR position('preserve_managed_erp_endpoints_on_user_delete' IN v_definition) = 0
    THEN
        RAISE EXCEPTION
            'erp_endpoints_preserve_managed_creator_delete does not match the F1-B3B2a contract';
    END IF;
END
$pearnly$
"""

_CREATOR_UPDATE_FUNCTION_DDL = """
CREATE OR REPLACE FUNCTION public.prevent_managed_erp_endpoint_creator_change()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
BEGIN
    IF OLD.binding_generation > 0
       AND NEW.user_id IS DISTINCT FROM OLD.user_id
       AND pg_trigger_depth() = 1
    THEN
        RAISE EXCEPTION 'managed ERP endpoint creator is immutable';
    END IF;
    RETURN NEW;
END
$pearnly$
"""

_MANAGED_CLEANUP_FUNCTION_DDL = """CREATE OR REPLACE FUNCTION public.purge_managed_erp_endpoints_for_users(p_user_ids uuid[]) RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $pearnly$ DECLARE v_deleted BIGINT; BEGIN IF p_user_ids IS NULL OR cardinality(p_user_ids) > 1000 THEN RAISE EXCEPTION 'managed endpoint cleanup requires at most 1000 user ids'; END IF; DELETE FROM public.erp_endpoints WHERE user_id = ANY (p_user_ids) AND binding_generation > 0; GET DIAGNOSTICS v_deleted = ROW_COUNT; RETURN v_deleted; END $pearnly$"""

_MANAGED_CLEANUP_GRANT_DDL = (
    "REVOKE ALL ON FUNCTION public.purge_managed_erp_endpoints_for_users(uuid[]) FROM PUBLIC"
)

_CREATOR_UPDATE_TRIGGER_DDL = """
DO $pearnly$
DECLARE
    v_definition TEXT; v_security_definer BOOLEAN; v_config TEXT[];
BEGIN
    SELECT procedure_meta.prosecdef, procedure_meta.proconfig
      INTO v_security_definer, v_config
      FROM pg_proc procedure_meta
     WHERE procedure_meta.oid = 'public.prevent_managed_erp_endpoint_creator_change()'::regprocedure;
    IF NOT FOUND
       OR v_security_definer IS DISTINCT FROM TRUE
       OR v_config IS DISTINCT FROM ARRAY['search_path=pg_catalog']::TEXT[]
    THEN
        RAISE EXCEPTION
            'prevent_managed_erp_endpoint_creator_change must be SECURITY DEFINER with fixed pg_catalog search_path';
    END IF;
    SELECT lower(pg_get_triggerdef(trigger_meta.oid))
      INTO v_definition
      FROM pg_trigger trigger_meta
     WHERE trigger_meta.tgrelid = 'erp_endpoints'::regclass
       AND trigger_meta.tgname = 'erp_endpoints_managed_creator_immutable'
       AND NOT trigger_meta.tgisinternal;
    IF NOT FOUND THEN
        CREATE TRIGGER erp_endpoints_managed_creator_immutable
        BEFORE UPDATE OF user_id ON erp_endpoints
        FOR EACH ROW
        EXECUTE FUNCTION public.prevent_managed_erp_endpoint_creator_change();
    ELSIF position('before update of user_id' IN v_definition) = 0
       OR position('for each row' IN v_definition) = 0
       OR position('prevent_managed_erp_endpoint_creator_change' IN v_definition) = 0
    THEN
        RAISE EXCEPTION
            'erp_endpoints_managed_creator_immutable does not match the F1-B3B2a contract';
    END IF;
END
$pearnly$
"""
SHARED_EXPRESS_MANAGED_STRUCTURE_DDL = (
    "ALTER TABLE erp_endpoints ALTER COLUMN user_id DROP NOT NULL",
    _USER_COLUMN_CONTRACT_DDL,
    *_check_constraint(
        "erp_endpoints_legacy_creator_chk",
        "binding_generation > 0 OR user_id IS NOT NULL",
        "checkbinding_generation>0oruser_idisnotnull",
    ),
    *_check_constraint(
        "erp_endpoints_managed_scope_chk",
        "binding_generation = 0 OR (tenant_id IS NOT NULL "
        "AND workspace_client_id IS NOT NULL AND adapter = 'express')",
        "checkbinding_generation=0ortenant_idisnotnullandworkspace_client_idisnotnull"
        "andadapter='express'::text",
        compatible=(
            "checkbinding_generation=0ortenant_idisnotnullandadapter='express'::textand"
            "workspace_client_idisnotnullorrevoked_atisnotnull",
        ),
    ),
    *_check_constraint(
        "erp_endpoints_shared_generation_chk",
        "NOT shared_scope OR binding_generation > 0",
        "checknotshared_scopeorbinding_generation>0",
    ),
    _ORPHAN_TENANT_INVENTORY_DDL,
    _TENANT_FK_CONTRACT_DDL,
    "ALTER TABLE erp_endpoints VALIDATE CONSTRAINT erp_endpoints_tenant_id_fkey",
    _USER_FK_CONTRACT_DDL,
    _CREATOR_DELETE_FUNCTION_DDL,
    "REVOKE ALL ON FUNCTION public.preserve_managed_erp_endpoints_on_user_delete() FROM PUBLIC",
    _CREATOR_DELETE_TRIGGER_DDL,
    _CREATOR_UPDATE_FUNCTION_DDL,
    "REVOKE ALL ON FUNCTION public.prevent_managed_erp_endpoint_creator_change() FROM PUBLIC",
    _CREATOR_UPDATE_TRIGGER_DDL,
    _MANAGED_CLEANUP_FUNCTION_DDL,
    _MANAGED_CLEANUP_GRANT_DDL,
)


_MANAGED_OWNER_PREDICATE = """
current_setting('app.erp_managed_express_owner', true) = 'on'
AND current_setting('app.erp_managed_express_tenant_id', true) = current_setting('app.current_tenant_id', true)
AND current_setting('app.erp_managed_express_workspace_id', true) = current_setting('app.current_workspace_id', true)
AND current_setting('app.erp_managed_express_actor_id', true)
    = current_setting('app.current_user_id', true)
AND binding_generation > 0
AND adapter = 'express'
AND tenant_id::text = current_setting('app.current_tenant_id', true)
AND workspace_client_id::text = current_setting('app.current_workspace_id', true)
AND EXISTS (SELECT 1 FROM workspace_clients managed_workspace
    WHERE managed_workspace.id = erp_endpoints.workspace_client_id
      AND managed_workspace.tenant_id = erp_endpoints.tenant_id AND managed_workspace.is_active = TRUE)
AND EXISTS (SELECT 1 FROM memberships managed_membership JOIN roles managed_role ON managed_role.id = managed_membership.role_id
    WHERE managed_membership.user_id::text = current_setting('app.current_user_id', true)
      AND managed_membership.tenant_id = erp_endpoints.tenant_id AND managed_membership.status = 'active' AND managed_role.name = 'owner')
""".strip()

_SHARED_SELECT_PREDICATE = """
current_setting('app.erp_shared_express_endpoint', true) = 'on'
AND current_setting('app.erp_shared_express_tenant_id', true) = current_setting('app.current_tenant_id', true)
AND current_setting('app.erp_shared_express_workspace_id', true) = current_setting('app.current_workspace_id', true)
AND binding_generation > 0
AND adapter = 'express' AND enabled = TRUE AND shared_scope = TRUE
AND tenant_id IS NOT NULL AND workspace_client_id IS NOT NULL
AND tenant_id::text = current_setting('app.erp_shared_express_tenant_id', true)
AND workspace_client_id::text = current_setting('app.erp_shared_express_workspace_id', true)
AND tenant_id::text = current_setting('app.current_tenant_id', true)
AND workspace_client_id::text = current_setting('app.current_workspace_id', true)
""".strip()

SHARED_EXPRESS_MANAGED_RLS_DDL = (
    "ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY",
    "DROP POLICY IF EXISTS tenant_isolation ON erp_endpoints",
    "DROP POLICY IF EXISTS erp_endpoints_legacy_user_all ON erp_endpoints",
    "DROP POLICY IF EXISTS erp_endpoints_shared_express_select ON erp_endpoints",
    "DROP POLICY IF EXISTS erp_endpoints_managed_owner_select ON erp_endpoints",
    "DROP POLICY IF EXISTS erp_endpoints_managed_owner_update ON erp_endpoints",
    "DROP POLICY IF EXISTS erp_endpoints_no_managed_delete ON erp_endpoints",
    "CREATE POLICY erp_endpoints_legacy_user_all ON erp_endpoints FOR ALL "
    "USING (binding_generation = 0 AND (current_setting('app.bypass_rls', true) = 'on' OR "
    "user_id::text = current_setting('app.current_user_id', true))) "
    "WITH CHECK (binding_generation = 0 AND (current_setting('app.bypass_rls', true) = 'on' OR "
    "user_id::text = current_setting('app.current_user_id', true)))",
    "CREATE POLICY erp_endpoints_shared_express_select ON erp_endpoints FOR SELECT USING ("
    + _SHARED_SELECT_PREDICATE
    + ")",
    "CREATE POLICY erp_endpoints_managed_owner_select ON erp_endpoints FOR SELECT USING ("
    + _MANAGED_OWNER_PREDICATE
    + ")",
    "CREATE POLICY erp_endpoints_managed_owner_update ON erp_endpoints FOR UPDATE USING ("
    + _MANAGED_OWNER_PREDICATE
    + ") WITH CHECK ("
    + _MANAGED_OWNER_PREDICATE
    + ")",
    "CREATE POLICY erp_endpoints_no_managed_delete ON erp_endpoints "
    "AS RESTRICTIVE FOR DELETE USING (binding_generation = 0)",
)

SHARED_EXPRESS_MANAGED_DDL = SHARED_EXPRESS_MANAGED_STRUCTURE_DDL + SHARED_EXPRESS_MANAGED_RLS_DDL


def apply_shared_express_managed_rls(cur) -> None:
    for statement in SHARED_EXPRESS_MANAGED_RLS_DDL:
        cur.execute(statement)


def apply_shared_express_managed_foundation(cur) -> None:
    for statement in SHARED_EXPRESS_MANAGED_DDL:
        cur.execute(statement)


def ensure_shared_express_managed_foundation() -> None:
    global _MANAGED_FOUNDATION_READY
    try:
        with db.get_cursor(commit=True) as cur:
            apply_shared_express_managed_foundation(cur)
    except Exception:
        _MANAGED_FOUNDATION_READY = False
        raise
    _MANAGED_FOUNDATION_READY = True


def _reset_managed_gate(cur) -> None:
    cur.execute(
        "SELECT set_config(%s, 'off', true), set_config(%s, '', true), "
        "set_config(%s, '', true), set_config(%s, '', true)",
        (
            MANAGED_EXPRESS_GATE_GUC,
            MANAGED_EXPRESS_TENANT_GUC,
            MANAGED_EXPRESS_WORKSPACE_GUC,
            MANAGED_EXPRESS_ACTOR_GUC,
        ),
    )


def enable_managed_express_owner_access(
    cur, *, tenant_id: object, workspace_client_id: object, actor_user_id: object
) -> bool:
    """Lock live owner authority, then enable managed SELECT/UPDATE for this transaction."""
    _reset_managed_gate(cur)
    if not managed_foundation_ready():
        return False
    tenant = str(tenant_id).strip() if tenant_id is not None else ""
    workspace = str(workspace_client_id).strip() if workspace_client_id is not None else ""
    actor = str(actor_user_id).strip() if actor_user_id is not None else ""
    if not tenant or not workspace or not actor:
        return False

    cur.execute(
        "SELECT current_setting('app.current_tenant_id', true) = %s "
        "AND current_setting('app.current_workspace_id', true) = %s "
        "AND current_setting('app.current_user_id', true) = %s AS matches",
        (tenant, workspace, actor),
    )
    context = cur.fetchone()
    if not context or not bool(context.get("matches")):
        return False

    cur.execute(
        "SELECT membership.id FROM memberships membership "
        "JOIN roles role ON role.id = membership.role_id "
        "WHERE membership.user_id = %s AND membership.tenant_id = %s "
        "AND membership.status = 'active' AND role.name = 'owner' "
        "FOR SHARE OF membership, role",
        (actor, tenant),
    )
    if not cur.fetchone():
        return False
    cur.execute(
        "SELECT id FROM users WHERE id = %s AND tenant_id = %s AND is_active = TRUE FOR SHARE",
        (actor, tenant),
    )
    if not cur.fetchone():
        return False
    cur.execute(
        "SELECT id FROM workspace_clients WHERE id = %s AND tenant_id = %s "
        "AND is_active = TRUE FOR SHARE",
        (workspace, tenant),
    )
    if not cur.fetchone():
        return False

    cur.execute(
        "SELECT set_config(%s, 'on', true), set_config(%s, %s, true), "
        "set_config(%s, %s, true), set_config(%s, %s, true)",
        (
            MANAGED_EXPRESS_GATE_GUC,
            MANAGED_EXPRESS_TENANT_GUC,
            tenant,
            MANAGED_EXPRESS_WORKSPACE_GUC,
            workspace,
            MANAGED_EXPRESS_ACTOR_GUC,
            actor,
        ),
    )
    return True
