"""Read-only startup validation after the deployment job installs ERP guardrails."""

from core import db
from services.erp import shared_express_enrollment_schema as enrollment
from services.erp import shared_express_lifecycle_schema as lifecycle
from services.erp import shared_express_live_schema as live
from services.erp import shared_express_managed_schema as managed
from services.erp.shared_express_binding_schema import (
    SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL,
    _column_contract_ddl,
)
from services.erp.shared_express_lifecycle_ddl import CATALOG_VALIDATION_DDL
from services.erp.shared_express_schema import _INDEX_CONTRACT_DDL

# These are catalog-only contracts already used by the schema installer. The
# READ ONLY transaction below also prevents an accidental future DDL addition.
_CATALOG_CHECKS = (
    SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL,
    _column_contract_ddl(
        (
            ("user_id", "", "uuid", False, None),
            ("tenant_id", "", "uuid", False, None),
            ("workspace_client_id", "", "bigint", False, None),
            ("shared_scope", "", "boolean", True, "false"),
        )
    ),
    _INDEX_CONTRACT_DDL,
    CATALOG_VALIDATION_DDL,
    live.LIVE_DDL[-1],
)
_FUNCTIONS = {
    "preserve_managed_erp_endpoints_on_user_delete()": False,
    "prevent_managed_erp_endpoint_creator_change()": False,
    "purge_managed_erp_endpoints_for_users(uuid[])": False,
    "erp_endpoint_has_legacy_activity(uuid)": True,
    "guard_erp_endpoint_enrollment_columns()": False,
    "guard_erp_endpoint_lifecycle_columns()": False,
    "erp_managed_endpoint_has_activity(uuid)": True,
    "erp_managed_live_authenticate(uuid,text)": True,
    "guard_erp_endpoint_managed_live_columns()": False,
    "guard_erp_endpoint_managed_profile_confirm()": False,
}
_TRIGGERS = {
    "erp_endpoints_preserve_managed_creator_delete": (
        "users",
        "preserve_managed_erp_endpoints_on_user_delete",
        11,
        [],
    ),
    "erp_endpoints_managed_creator_immutable": (
        "erp_endpoints",
        "prevent_managed_erp_endpoint_creator_change",
        19,
        ["user_id"],
    ),
    "erp_endpoints_enrollment_columns_guard": (
        "erp_endpoints",
        "guard_erp_endpoint_enrollment_columns",
        19,
        [],
    ),
    "erp_endpoints_lifecycle_columns_guard": (
        "erp_endpoints",
        "guard_erp_endpoint_lifecycle_columns",
        19,
        [
            "tenant_id",
            "workspace_client_id",
            "binding_generation",
            "enabled",
            "shared_scope",
            "revoked_at",
            "revoked_by",
            "updated_at",
        ],
    ),
    "erp_endpoints_managed_live_columns_guard": (
        "erp_endpoints",
        "guard_erp_endpoint_managed_live_columns",
        19,
        ["live_account_set", "live_profile_key", "agent_last_seen_at", "agent_version"],
    ),
    "erp_endpoints_managed_profile_confirm_guard": (
        "erp_endpoints",
        "guard_erp_endpoint_managed_profile_confirm",
        19,
        ["bound_account_set", "bound_profile_key", "binding_generation"],
    ),
}
_POLICIES = {
    "erp_endpoints_legacy_user_all": ("*", True, "app.current_user_id"),
    "erp_endpoints_shared_express_select": ("r", True, "app.erp_shared_express_endpoint"),
    "erp_endpoints_managed_owner_select": ("r", True, "app.erp_managed_express_owner"),
    "erp_endpoints_managed_owner_update": ("w", True, "app.erp_managed_express_owner"),
    "erp_endpoints_no_managed_delete": ("d", False, "binding_generation"),
    "erp_endpoints_shared_express_enroll": ("w", True, "binding_generation"),
    "erp_endpoints_managed_lifecycle_select": ("r", True, "app.erp_endpoint_lifecycle"),
    "erp_endpoints_managed_lifecycle_update": ("w", True, "app.erp_endpoint_lifecycle"),
    "erp_endpoints_managed_live_select": ("r", True, "app.erp_managed_live_heartbeat"),
    "erp_endpoints_managed_live_update": ("w", True, "app.erp_managed_live_heartbeat"),
    "erp_endpoints_managed_live_confirm": ("w", True, "app.erp_managed_live_confirm"),
    "erp_endpoints_managed_live_confirm_select": ("r", True, "app.erp_managed_live_confirm"),
}
_CONSTRAINTS = {
    "erp_endpoints_legacy_creator_chk",
    "erp_endpoints_shared_generation_chk",
    "erp_endpoints_tenant_id_fkey",
    "erp_endpoints_bound_profile_pair_chk",
    "erp_endpoints_live_profile_pair_chk",
    "erp_endpoints_binding_generation_chk",
}


def _require(ok, contract):
    if not ok:
        raise RuntimeError(f"ERP serving schema contract mismatch: {contract}")


def _check_functions(cur):
    for signature, app_execute in _FUNCTIONS.items():
        qualified = "public." + signature
        cur.execute(
            "SELECT p.prosecdef, p.proconfig, "
            "has_function_privilege('public', p.oid, 'EXECUTE') AS public_execute, "
            "CASE WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pearnly_app') "
            "THEN has_function_privilege('pearnly_app', p.oid, 'EXECUTE') "
            "ELSE false END AS app_execute FROM pg_proc p WHERE p.oid = to_regprocedure(%s)",
            (qualified,),
        )
        row = cur.fetchone()
        _require(
            row
            and row["prosecdef"]
            and row["proconfig"] == ["search_path=pg_catalog"]
            and not row["public_execute"]
            and (not app_execute or row["app_execute"]),
            qualified,
        )


def _check_triggers(cur):
    cur.execute(
        "SELECT t.tgname, c.relname, p.proname, t.tgtype, t.tgenabled, "
        "t.tgqual IS NULL AS unconditional, "
        "ARRAY(SELECT a.attname::text FROM unnest(t.tgattr) WITH ORDINALITY k(attnum, pos) "
        "JOIN pg_attribute a ON a.attrelid=t.tgrelid AND a.attnum=k.attnum ORDER BY k.pos) "
        "AS columns FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "JOIN pg_proc p ON p.oid=t.tgfoid "
        "WHERE t.tgrelid IN ('public.erp_endpoints'::regclass, 'public.users'::regclass) "
        "AND NOT t.tgisinternal"
    )
    rows = {row["tgname"]: row for row in cur.fetchall()}
    for name, (table, function, trigger_type, columns) in _TRIGGERS.items():
        row = rows.get(name)
        _require(
            row
            and row["relname"] == table
            and row["proname"] == function
            and row["tgtype"] == trigger_type
            and row["tgenabled"] == "O"
            and row["unconditional"]
            and row["columns"] == columns,
            name,
        )


def _check_policies(cur):
    cur.execute(
        "SELECT p.polname, p.polcmd, p.polpermissive, "
        "pg_get_expr(p.polqual,p.polrelid) AS using_expr, "
        "pg_get_expr(p.polwithcheck,p.polrelid) AS check_expr "
        "FROM pg_policy p WHERE p.polrelid='public.erp_endpoints'::regclass"
    )
    rows = {row["polname"]: row for row in cur.fetchall()}
    for name, (command, permissive, gate) in _POLICIES.items():
        row = rows.get(name)
        _require(
            row
            and row["polcmd"] == command
            and row["polpermissive"] == permissive
            and gate in (row["using_expr"] or "")
            and (command not in {"w", "*"} or gate in (row["check_expr"] or "")),
            name,
        )


def _check_structure(cur):
    cur.execute("SELECT relrowsecurity FROM pg_class WHERE oid='public.erp_endpoints'::regclass")
    row = cur.fetchone()
    _require(row and row["relrowsecurity"], "endpoint RLS")
    cur.execute(
        "SELECT conname FROM pg_constraint WHERE conrelid='public.erp_endpoints'::regclass "
        "AND convalidated AND conname = ANY(%s)",
        (sorted(_CONSTRAINTS),),
    )
    _require({row["conname"] for row in cur.fetchall()} == _CONSTRAINTS, "endpoint constraints")
    cur.execute(
        "SELECT indisunique AND indisvalid AND indisready AND indislive AS ready "
        "FROM pg_index WHERE indexrelid = "
        "to_regclass('public.uq_operation_logs_erp_endpoint_lifecycle_operation')"
    )
    row = cur.fetchone()
    _require(row and row["ready"], "lifecycle operation index")


def _set_ready(ready):
    managed._MANAGED_FOUNDATION_READY = ready
    enrollment._ENROLLMENT_RLS_READY = ready
    lifecycle._LIFECYCLE_SCHEMA_READY = ready
    live._READY = ready


def initialize_serving_schema() -> None:
    """Populate process-local flags only after all installed guards pass readback."""
    _set_ready(False)
    with db.get_cursor(commit=True) as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        for statement in _CATALOG_CHECKS:
            cur.execute(statement)
        _check_structure(cur)
        _check_functions(cur)
        _check_triggers(cur)
        _check_policies(cur)
    _set_ready(True)
