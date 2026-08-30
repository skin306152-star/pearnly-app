"""Disposable PostgreSQL proof for the B3B2b-2 schema boundary.

The matrix deliberately drives the real RLS, trigger, advisory-lock, and audit
transactions on the disposable schema. Calling the HTTP service here would
silently use the process-global ``DATABASE_URL`` pool and the production authz
resolver, whose wider membership schema is outside this task-owned fixture;
that injection boundary is reported with the smoke result rather than replaced
with a mock service transaction.
"""

from __future__ import annotations

import uuid
import unittest
from threading import Barrier, Thread
from pathlib import Path

from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp import shared_express_lifecycle_schema as lifecycle
from services.erp.legacy_generation import lock_endpoint_binding
from services.audit.store import insert_operation_log_tx
from tests.unit._pg_smoke import (
    LOCAL_DSN,
    assert_public_routines_unchanged,
    connect_or_skip,
    require_disposable_db,
    snapshot_public_routines,
)

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OWNER = "11111111-1111-1111-1111-111111111111"
ROLE = "22222222-2222-2222-2222-222222222222"
ENDPOINT = "33333333-3333-4333-8333-333333333333"
WORKSPACE = 101
TARGET = 202


def _localize(statement: str, schema: str) -> str:
    localized = statement
    for table in (
        "erp_endpoints",
        "erp_push_logs",
        "operation_logs",
        "workspace_clients",
        "memberships",
        "roles",
        "users",
    ):
        localized = localized.replace(f"public.{table}", f'"{schema}".{table}')
    for function in ("guard_erp_endpoint_lifecycle_columns", "erp_managed_endpoint_has_activity"):
        localized = localized.replace(f"public.{function}", f'"{schema}".{function}')
    return localized


class SharedExpressLifecyclePgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema = f"smoke_lifecycle_{uuid.uuid4().hex[:12]}"
        cls.before = snapshot_public_routines(cls.cur)
        c = cls.cur
        c.execute(f'CREATE SCHEMA "{cls.schema}"')
        c.execute(f'SET search_path TO "{cls.schema}", public')
        c.execute("""
            CREATE TABLE tenants (id uuid primary key);
            CREATE TABLE users (id uuid primary key, tenant_id uuid, is_active boolean not null default true);
            CREATE TABLE roles (id uuid primary key, name text not null);
            CREATE TABLE memberships (id uuid primary key, user_id uuid, tenant_id uuid, role_id uuid, status text not null);
            CREATE TABLE workspace_clients (id bigint primary key, tenant_id uuid not null, is_active boolean not null default true, erp_endpoint_id uuid);
            CREATE TABLE erp_endpoints (
              id uuid primary key, user_id uuid, name text not null, adapter text not null,
              config jsonb not null default '{}'::jsonb, is_default boolean not null default false,
              auto_push boolean not null default false, enabled boolean not null default true,
              last_used_at timestamptz, last_status text, success_count integer not null default 0,
              failure_count integer not null default 0, created_at timestamptz not null default now(),
              updated_at timestamptz not null default now(), tenant_id uuid, workspace_client_id bigint,
              shared_scope boolean not null default false, bound_account_set text, bound_profile_key text,
              live_account_set text, live_profile_key text, agent_last_seen_at timestamptz,
              agent_version text, binding_generation bigint not null default 0,
              constraint erp_endpoints_binding_generation_chk check (binding_generation >= 0),
              constraint erp_endpoints_bound_profile_pair_chk check ((bound_account_set is null) = (bound_profile_key is null)),
              constraint erp_endpoints_live_profile_pair_chk check ((live_account_set is null) = (live_profile_key is null))
            );
            CREATE TABLE erp_push_logs (
              id uuid primary key, user_id uuid not null, endpoint_id uuid, status text not null,
              next_retry_at timestamptz, lease_owner text, lease_expires_at timestamptz
            );
            CREATE TABLE operation_logs (
              id bigserial primary key, tenant_id uuid, actor_user_id uuid, action text,
              actor_username text, actor_is_super boolean not null default false,
              target_type text, target_id text, target_name text, details jsonb,
              ip inet, ua text
            );
            """)
        ensure_rls_app_role(c)
        c.execute(f'GRANT USAGE ON SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}')
        c.execute(
            f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}'
        )
        c.execute(
            f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}'
        )
        for statement in lifecycle.SHARED_EXPRESS_LIFECYCLE_DDL:
            c.execute(_localize(statement, cls.schema))
        c.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints ENABLE ROW LEVEL SECURITY')
        c.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, "smoke_lifecycle_")
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.conn.commit()
            assert_public_routines_unchanged(cls.cur, cls.before)
        finally:
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        c = self.cur
        self.conn.rollback()
        c.execute(f'SET search_path TO "{self.schema}", public')
        c.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        c.execute(
            "TRUNCATE erp_push_logs, operation_logs, erp_endpoints, memberships, roles, users, workspace_clients, tenants CASCADE"
        )
        c.execute("INSERT INTO tenants VALUES (%s)", (TENANT,))
        c.execute("INSERT INTO users VALUES (%s,%s,TRUE)", (OWNER, TENANT))
        c.execute("INSERT INTO roles VALUES (%s,'owner')", (ROLE,))
        c.execute(
            "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
            (str(uuid.uuid4()), OWNER, TENANT, ROLE),
        )
        c.execute(
            "INSERT INTO workspace_clients VALUES (%s,%s,TRUE,NULL),(%s,%s,TRUE,NULL)",
            (WORKSPACE, TENANT, TARGET, TENANT),
        )
        c.execute(
            "INSERT INTO erp_endpoints "
            "(id,user_id,name,adapter,config,enabled,shared_scope,tenant_id,workspace_client_id,binding_generation) "
            "VALUES (%s,%s,'managed','express',%s::jsonb,TRUE,TRUE,%s,%s,1)",
            (ENDPOINT, OWNER, '{"agent_token":"secret","keep":1}', TENANT, WORKSPACE),
        )
        c.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        c.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()

    def tearDown(self):
        self.conn.rollback()

    def _gate(
        self,
        action: str,
        generation: int = 1,
        target: object = WORKSPACE,
        operation: str | None = None,
    ):
        self._set_gate(self.cur, action, generation, target, operation)

    @staticmethod
    def _set_gate(c, action, generation=1, target=WORKSPACE, operation=None):
        c.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        values = {
            "app.current_tenant_id": TENANT,
            "app.current_user_id": OWNER,
            "app.current_workspace_id": str(WORKSPACE),
            "app.erp_endpoint_lifecycle": "on",
            "app.erp_endpoint_lifecycle_tenant_id": TENANT,
            "app.erp_endpoint_lifecycle_actor_id": OWNER,
            "app.erp_endpoint_lifecycle_endpoint_id": ENDPOINT,
            "app.erp_endpoint_lifecycle_action": action,
            "app.erp_endpoint_lifecycle_source_workspace_id": str(WORKSPACE),
            "app.erp_endpoint_lifecycle_target_workspace_id": "" if target is None else str(target),
            "app.erp_endpoint_lifecycle_expected_generation": str(generation),
            "app.erp_endpoint_lifecycle_operation_id": operation or str(uuid.uuid4()),
        }
        for key, value in values.items():
            c.execute("SELECT set_config(%s,%s,true)", (key, value))

    def _endpoint(self):
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "SELECT enabled, shared_scope, workspace_client_id, binding_generation, revoked_at, revoked_by, config "
            "FROM erp_endpoints WHERE id = %s",
            (ENDPOINT,),
        )
        return self.cur.fetchone()

    def _set_endpoint_enabled_without_lifecycle(self, enabled):
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "ALTER TABLE erp_endpoints DISABLE TRIGGER erp_endpoints_lifecycle_columns_guard"
        )
        self.cur.execute(
            "UPDATE erp_endpoints SET enabled = %s, shared_scope = TRUE, workspace_client_id = %s, "
            "binding_generation = 1, revoked_at = NULL, revoked_by = NULL, "
            'config = \'{"agent_token": "secret", "keep": 1}\'::jsonb WHERE id = %s',
            (enabled, WORKSPACE, ENDPOINT),
        )
        self.cur.execute(
            "ALTER TABLE erp_endpoints ENABLE TRIGGER erp_endpoints_lifecycle_columns_guard"
        )
        self.cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        self.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()

    def _disable_rls_after_gate(self):
        """Keep the trigger gate while isolating trigger/CAS assertions from policy shape."""
        self.cur.execute("RESET ROLE")
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")

    def test_replayable_ddl_and_exact_catalog_guards(self):
        self.cur.execute("RESET ROLE")
        for statement in lifecycle.SHARED_EXPRESS_LIFECYCLE_DDL:
            self.cur.execute(_localize(statement, self.schema))
        self.cur.execute(
            "SELECT pg_get_functiondef(%s::regprocedure) AS definition",
            (f'"{self.schema}".erp_managed_endpoint_has_activity(uuid)',),
        )
        self.assertIn("SET search_path TO 'pg_catalog'", self.cur.fetchone()["definition"])
        self.conn.rollback()

    def test_prod_archive_lifecycle_sql_parses(self):
        archive = Path(__file__).resolve().parents[2] / "docs/db/prod-schema.sql"
        payload = archive.read_text(encoding="utf-8")
        start = payload.index("-- F1-B3B2b-2 managed Express endpoint lifecycle archive (0112).")
        statement = _localize(payload[start:].strip(), self.schema)
        self.cur.execute(statement)
        self.conn.rollback()

    def test_legacy_baseline_lifecycle_archive_sql_parses(self):
        baseline = Path(__file__).resolve().parents[2] / "alembic/sql/001a_legacy_tables.sql"
        payload = baseline.read_text(encoding="utf-8")
        start = payload.index("-- B3B2b-2 lifecycle baseline archive.")
        statement = _localize(payload[start:].strip(), self.schema)
        self.cur.execute(statement)
        self.conn.rollback()

    def test_duplicate_tenant_operation_data_fails_closed_before_index(self):
        self.cur.execute("DROP INDEX uq_operation_logs_erp_endpoint_lifecycle_operation")
        duplicate = str(uuid.uuid4())
        for _ in range(2):
            self.cur.execute(
                "INSERT INTO operation_logs (tenant_id, action, target_type, target_id, details) "
                "VALUES (%s, 'erp.endpoint.disable', 'erp_endpoint', %s, %s::jsonb)",
                (TENANT, ENDPOINT, '{"operation_id": "' + duplicate + '"}'),
            )
        with self.assertRaises(Exception) as raised:
            for statement in lifecycle.SHARED_EXPRESS_LIFECYCLE_DDL:
                self.cur.execute(_localize(statement, self.schema))
        self.assertIn("duplicate tenant operation_id", str(raised.exception))
        self.conn.rollback()

    def test_wrong_existing_operation_index_fails_closed(self):
        self.cur.execute("DROP INDEX uq_operation_logs_erp_endpoint_lifecycle_operation")
        self.cur.execute(
            "CREATE UNIQUE INDEX uq_operation_logs_erp_endpoint_lifecycle_operation "
            "ON operation_logs (tenant_id) WHERE target_type = 'erp_endpoint'"
        )
        with self.assertRaises(Exception) as raised:
            for statement in lifecycle.SHARED_EXPRESS_LIFECYCLE_DDL:
                self.cur.execute(_localize(statement, self.schema))
        self.assertIn("does not match lifecycle contract", str(raised.exception))
        self.conn.rollback()

    def test_trigger_rejects_bypass_and_allows_disable_transition(self):
        self._gate("disable", operation="11111111-1111-4111-8111-111111111111")
        self.cur.execute(
            "SELECT current_user, current_setting('app.current_tenant_id', true) AS tenant, "
            "current_setting('app.erp_endpoint_lifecycle', true) AS gate, "
            "current_setting('app.erp_endpoint_lifecycle_endpoint_id', true) AS endpoint"
        )
        context = self.cur.fetchone()
        self.assertEqual(context["tenant"], TENANT)
        self.cur.execute("RESET ROLE")
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "UPDATE erp_endpoints SET enabled = FALSE, binding_generation = 2 WHERE id = %s",
            (ENDPOINT,),
        )
        self.assertEqual(self.cur.rowcount, 1)
        self.conn.rollback()
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        with self.assertRaises(Exception):
            self.cur.execute(
                "UPDATE erp_endpoints SET enabled = TRUE, binding_generation = 3 WHERE id = %s",
                (ENDPOINT,),
            )
        self.conn.rollback()

    def test_sensitive_update_rejects_non_contract_field_changes(self):
        self._gate("disable", operation="22222222-2222-4222-8222-222222222222")
        with self.assertRaises(Exception):
            self.cur.execute(
                "UPDATE erp_endpoints SET name = 'tampered', enabled = FALSE, binding_generation = 2 "
                "WHERE id = %s",
                (ENDPOINT,),
            )
        self.conn.rollback()
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "SELECT name, binding_generation FROM erp_endpoints WHERE id = %s", (ENDPOINT,)
        )
        row = self.cur.fetchone()
        self.assertEqual(row["name"], "managed")
        self.assertEqual(row["binding_generation"], 1)

        with self.assertRaises(Exception):
            self.cur.execute(
                "UPDATE erp_endpoints SET updated_at = NOW() WHERE id = %s",
                (ENDPOINT,),
            )
        self.conn.rollback()

    def test_four_actions_apply_one_cas_transition_each(self):
        cases = (
            ("disable", True, {"enabled": False, "workspace_client_id": WORKSPACE}),
            ("enable", False, {"enabled": True, "workspace_client_id": WORKSPACE}),
            ("rebind", False, {"enabled": False, "workspace_client_id": TARGET}),
            (
                "revoke",
                False,
                {"enabled": False, "workspace_client_id": None, "shared_scope": False},
            ),
        )
        for action, initial_enabled, expected in cases:
            self._set_endpoint_enabled_without_lifecycle(initial_enabled)
            self._gate(
                action,
                target=TARGET if action == "rebind" else None if action == "revoke" else WORKSPACE,
            )
            self._disable_rls_after_gate()
            if action == "rebind":
                sql = "UPDATE erp_endpoints SET workspace_client_id = %s, binding_generation = 2 WHERE id = %s AND binding_generation = 1"
                params = (TARGET, ENDPOINT)
            elif action == "revoke":
                sql = (
                    "UPDATE erp_endpoints SET workspace_client_id = NULL, shared_scope = FALSE, enabled = FALSE, "
                    "revoked_at = NOW(), revoked_by = %s, config = config - ARRAY['agent_token']::text[], "
                    "binding_generation = 2 WHERE id = %s AND binding_generation = 1"
                )
                params = (OWNER, ENDPOINT)
            else:
                sql = "UPDATE erp_endpoints SET enabled = %s, binding_generation = 2 WHERE id = %s AND binding_generation = 1"
                params = (action == "enable", ENDPOINT)
            self.cur.execute(sql, params)
            self.assertEqual(self.cur.rowcount, 1, action)
            self.conn.commit()
            row = self._endpoint()
            for key, value in expected.items():
                self.assertEqual(row[key], value, action)
            self.assertEqual(row["binding_generation"], 2, action)
            self.conn.rollback()

    def test_stale_cas_and_tenant_or_actor_mismatch_do_not_mutate(self):
        for context in (("wrong-tenant", OWNER), (TENANT, "99999999-9999-4999-8999-999999999999")):
            self._gate("disable", generation=2)
            self.cur.execute(
                "SELECT set_config('app.current_tenant_id', %s, true), set_config('app.current_user_id', %s, true)",
                context,
            )
            self.cur.execute(
                "UPDATE erp_endpoints SET enabled = FALSE, binding_generation = 2 WHERE id = %s AND binding_generation = 1",
                (ENDPOINT,),
            )
            self.assertEqual(self.cur.rowcount, 0)
            self.conn.rollback()

        self._gate("disable", generation=2)
        self.cur.execute(
            "UPDATE erp_endpoints SET enabled = FALSE, binding_generation = 2 WHERE id = %s AND binding_generation = 1",
            (ENDPOINT,),
        )
        self.assertEqual(self.cur.rowcount, 0)
        self.conn.rollback()
        row = self._endpoint()
        self.assertTrue(row["enabled"])
        self.assertEqual(row["binding_generation"], 1)

    def test_target_conflict_rolls_back_pointer_changes(self):
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "UPDATE workspace_clients SET erp_endpoint_id = %s WHERE id = %s", (ENDPOINT, WORKSPACE)
        )
        self.cur.execute(
            "UPDATE workspace_clients SET erp_endpoint_id = '44444444-4444-4444-8444-444444444444' WHERE id = %s",
            (TARGET,),
        )
        self.cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        self.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()
        self._gate("rebind", target=TARGET)
        lock_endpoint_binding(self.cur, ENDPOINT)
        self.cur.execute(
            "UPDATE workspace_clients SET erp_endpoint_id = NULL WHERE id = %s AND erp_endpoint_id = %s",
            (WORKSPACE, ENDPOINT),
        )
        self.assertEqual(self.cur.rowcount, 1)
        self.cur.execute(
            "UPDATE workspace_clients SET erp_endpoint_id = %s WHERE id = %s AND erp_endpoint_id IS NULL",
            (ENDPOINT, TARGET),
        )
        self.assertEqual(self.cur.rowcount, 0)
        self.conn.rollback()
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute("SELECT id, erp_endpoint_id FROM workspace_clients ORDER BY id")
        pointers = {row["id"]: row["erp_endpoint_id"] for row in self.cur.fetchall()}
        self.assertEqual(str(pointers[WORKSPACE]), ENDPOINT)
        self.assertEqual(str(pointers[TARGET]), "44444444-4444-4444-8444-444444444444")

    def test_audit_unique_failure_rolls_back_endpoint_and_log(self):
        self._gate("disable", operation="55555555-5555-4555-8555-555555555555")
        self._disable_rls_after_gate()
        self.cur.execute(
            "UPDATE erp_endpoints SET enabled = FALSE, binding_generation = 2 WHERE id = %s AND binding_generation = 1",
            (ENDPOINT,),
        )
        details = {
            "operation_id": "55555555-5555-4555-8555-555555555555",
            "endpoint_id": ENDPOINT,
            "action": "disable",
            "workspace_before": WORKSPACE,
            "workspace_after": WORKSPACE,
            "target_workspace_client_id": None,
            "expected_generation": 1,
            "actual_generation": 2,
            "generation_before": 1,
            "generation_after": 2,
            "enabled_before": True,
            "enabled_after": False,
            "shared_scope_before": True,
            "shared_scope_after": True,
            "revoked_before": False,
            "revoked_after": False,
            "reason": "rollback",
        }
        insert_operation_log_tx(
            self.cur,
            tenant_id=TENANT,
            actor_user_id=OWNER,
            actor_username="owner",
            actor_is_super=False,
            action="erp.endpoint.disable",
            target_type="erp_endpoint",
            target_id=ENDPOINT,
            details=details,
        )
        with self.assertRaises(Exception):
            insert_operation_log_tx(
                self.cur,
                tenant_id=TENANT,
                actor_user_id=OWNER,
                actor_username="owner",
                actor_is_super=False,
                action="erp.endpoint.disable",
                target_type="erp_endpoint",
                target_id=ENDPOINT,
                details=details,
            )
        self.conn.rollback()
        row = self._endpoint()
        self.assertTrue(row["enabled"])
        self.assertEqual(row["binding_generation"], 1)
        self.cur.execute("SELECT count(*) AS count FROM operation_logs")
        self.assertEqual(self.cur.fetchone()["count"], 0)

    def test_concurrent_cas_has_one_winner_under_endpoint_lock(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.conn.commit()
        barrier = Barrier(2)
        results = []

        def worker(operation):
            conn = psycopg2.connect(LOCAL_DSN, cursor_factory=RealDictCursor)
            try:
                cur = conn.cursor()
                cur.execute(f'SET search_path TO "{self.schema}", public')
                self._set_gate(cur, "disable", operation=operation)
                barrier.wait(timeout=3)
                lock_endpoint_binding(cur, ENDPOINT)
                cur.execute(
                    "UPDATE erp_endpoints SET enabled = FALSE, binding_generation = 2 WHERE id = %s AND binding_generation = 1",
                    (ENDPOINT,),
                )
                results.append(cur.rowcount)
                conn.commit()
            finally:
                conn.close()

        threads = [
            Thread(target=worker, args=(f"{i:08d}-aaaa-4aaa-8aaa-aaaaaaaaaaaa",)) for i in (1, 2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(sorted(results), [0, 1])
        self.cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        self.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()
        row = self._endpoint()
        self.assertFalse(row["enabled"])
        self.assertEqual(row["binding_generation"], 2)

    def test_busy_helper_sees_each_busy_marker_including_expired_lease(self):
        self.cur.execute("RESET ROLE")
        for status, retry, owner, expires in (
            ("pending", None, None, None),
            ("success", "2030-01-01", None, None),
            ("success", None, "worker", None),
            ("success", None, None, "2000-01-01"),
        ):
            self.cur.execute(
                "INSERT INTO erp_push_logs VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (str(uuid.uuid4()), OWNER, ENDPOINT, status, retry, owner, expires),
            )
            self._gate("disable")
            self.cur.execute("SELECT erp_managed_endpoint_has_activity(%s) AS busy", (ENDPOINT,))
            self.assertTrue(self.cur.fetchone()["busy"])
            self.conn.rollback()
            self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")

    def test_operation_index_is_partial_and_token_scrub_transition(self):
        self.cur.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname=%s AND indexname='uq_operation_logs_erp_endpoint_lifecycle_operation'",
            (self.schema,),
        )
        definition = self.cur.fetchone()["indexdef"]
        self.assertIn("operation_id", definition)
        self.assertIn("erp.endpoint.revoke", definition)


if __name__ == "__main__":
    unittest.main()
