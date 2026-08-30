# -*- coding: utf-8 -*-
"""F1-B3B2a 真 PostgreSQL 冒烟：ownership、RLS、删除保护与启动竞态。"""

from __future__ import annotations

import threading
import unittest
import uuid
from unittest import mock

from core import rls
from services.erp import shared_express_managed_schema as managed
from services.erp import shared_express_schema
from tests.unit._pg_smoke import connect, connect_or_skip

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
OWNER = "11111111-1111-1111-1111-111111111111"
CREATOR = "22222222-2222-2222-2222-222222222222"
EMPLOYEE = "33333333-3333-3333-3333-333333333333"
WORKSPACE_A = 101
WORKSPACE_B = 202
LEGACY = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0001"
MANAGED = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0002"
DISPOSABLE_MARKER = "__b3b2a_disposable_pg_smoke"


def require_disposable_db(cur, schema: str) -> None:
    if schema.startswith("pg_temp_"):
        return
    cur.execute("SELECT to_regclass(%s) AS marker", (f'"{schema}"."{DISPOSABLE_MARKER}"',))
    row = cur.fetchone()
    marker = row.get("marker") if hasattr(row, "get") else row[0] if row else None
    if marker is None:
        raise RuntimeError(f"refusing destructive cleanup without {schema}.{DISPOSABLE_MARKER}")


def _create_tables(cur, prefix: str = "") -> None:
    def table(name: str) -> str:
        return f"{prefix}{name}"

    cur.execute(f"CREATE TABLE {table('tenants')} (id UUID PRIMARY KEY, name TEXT NOT NULL)")
    cur.execute(
        f"CREATE TABLE {table('users')} ("
        "id UUID PRIMARY KEY, tenant_id UUID, is_active BOOLEAN NOT NULL DEFAULT TRUE)"
    )
    cur.execute(
        f"CREATE TABLE {table('workspace_clients')} ("
        "id BIGINT PRIMARY KEY, tenant_id UUID NOT NULL, is_active BOOLEAN NOT NULL DEFAULT TRUE)"
    )
    cur.execute(f"CREATE TABLE {table('roles')} (id UUID PRIMARY KEY, name TEXT NOT NULL)")
    cur.execute(
        f"CREATE TABLE {table('memberships')} ("
        "id UUID PRIMARY KEY, user_id UUID NOT NULL, tenant_id UUID NOT NULL, "
        "role_id UUID NOT NULL, status TEXT NOT NULL)"
    )
    cur.execute(
        f"CREATE TABLE {table('erp_endpoints')} ("
        "id UUID PRIMARY KEY, user_id UUID, name TEXT NOT NULL, adapter TEXT NOT NULL, "
        "enabled BOOLEAN NOT NULL DEFAULT TRUE, shared_scope BOOLEAN NOT NULL DEFAULT FALSE, "
        "tenant_id UUID, workspace_client_id BIGINT, binding_generation BIGINT NOT NULL DEFAULT 0, "
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    cur.execute(
        f"ALTER TABLE {table('erp_endpoints')} "
        "ADD CONSTRAINT erp_endpoints_user_id_fkey "
        f"FOREIGN KEY (user_id) REFERENCES {table('users')}(id) ON DELETE CASCADE"
    )
    cur.execute(
        f"ALTER TABLE {table('erp_endpoints')} "
        "ADD CONSTRAINT erp_endpoints_tenant_id_fkey "
        f"FOREIGN KEY (tenant_id) REFERENCES {table('tenants')}(id) ON DELETE CASCADE"
    )
    cur.execute(
        f"CREATE UNIQUE INDEX uq_erp_endpoints_user_express ON {table('erp_endpoints')} "
        "(user_id) WHERE adapter = 'express' AND binding_generation = 0"
    )


# fmt: off
def _localized_ddl(schema: str) -> tuple[str, ...]:
    return tuple(statement.replace("public.users", f'"{schema}".users').replace("public.erp_endpoints", f'"{schema}".erp_endpoints') for statement in managed.SHARED_EXPRESS_MANAGED_DDL)
# fmt: on


def _run_race_thread(schema: str, errors: list[str], action):
    conn = None
    try:
        from psycopg2.extras import RealDictCursor

        conn = connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f'SET search_path TO "{schema}", public')
        cur.execute("SET LOCAL lock_timeout = '5s'")
        action(cur)
        conn.commit()
    except Exception as exc:
        errors.append(repr(exc))
        conn and conn.rollback()
    finally:
        conn and conn.close()


class SharedExpressManagedPgSmokeTests(unittest.TestCase):
    conn = None
    cur = None

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls._previous_ready = managed._MANAGED_FOUNDATION_READY
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        try:
            rls.ensure_rls_app_role(cls.cur)
            cls.cur.execute("SET search_path TO pg_temp, public")
            cls.cur.execute("SELECT current_schema() AS schema")
            cls.schema = cls.cur.fetchone()["schema"]
            _create_tables(cls.cur)
            require_disposable_db(cls.cur, cls.schema)
            for name in (
                "tenants",
                "users",
                "workspace_clients",
                "roles",
                "memberships",
                "erp_endpoints",
            ):
                cls.cur.execute(
                    f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{cls.schema}".{name} TO {rls.RLS_APP_ROLE}'
                )
            for statement in _localized_ddl(cls.schema):
                cls.cur.execute(statement)
            cls.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
            cls.conn.commit()
            managed._MANAGED_FOUNDATION_READY = True
        except Exception:
            cls.conn.rollback()
            cls.cur.close()
            cls.conn.close()
            cls.cur = None
            cls.conn = None
            raise

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            managed._MANAGED_FOUNDATION_READY = cls._previous_ready
            cls.conn.rollback()
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        self.cur.execute(
            "INSERT INTO tenants (id,name) VALUES (%s,'A'),(%s,'B')",
            (TENANT_A, TENANT_B),
        )
        self.cur.execute(
            "INSERT INTO users (id,tenant_id) VALUES (%s,%s),(%s,%s),(%s,%s)",
            (OWNER, TENANT_A, CREATOR, TENANT_A, EMPLOYEE, TENANT_A),
        )
        owner_role = "44444444-4444-4444-4444-444444444444"
        self.cur.execute("INSERT INTO roles (id,name) VALUES (%s,'owner')", (owner_role,))
        self.cur.execute(
            "INSERT INTO memberships (id,user_id,tenant_id,role_id,status) "
            "VALUES (%s,%s,%s,%s,'active')",
            (str(uuid.uuid4()), OWNER, TENANT_A, owner_role),
        )
        self.cur.execute(
            "INSERT INTO workspace_clients (id,tenant_id) VALUES (%s,%s),(%s,%s)",
            (WORKSPACE_A, TENANT_A, WORKSPACE_B, TENANT_B),
        )
        self.cur.execute(
            "INSERT INTO erp_endpoints "
            "(id,user_id,name,adapter,tenant_id,workspace_client_id,binding_generation,shared_scope) "
            "VALUES (%s,%s,'legacy','express',NULL,NULL,0,FALSE),"
            "(%s,%s,'managed','express',%s,%s,1,TRUE)",
            (LEGACY, CREATOR, MANAGED, CREATOR, TENANT_A, WORKSPACE_A),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.rollback()
        self.cur.execute("SET search_path TO pg_temp, public")
        require_disposable_db(self.cur, self.schema)
        self.cur.execute(
            "TRUNCATE memberships, roles, workspace_clients, erp_endpoints, users, tenants CASCADE"
        )
        self.conn.commit()

    def _context(self, user: str, tenant: str = TENANT_A, workspace: int = WORKSPACE_A):
        self.cur.execute(f"SET LOCAL ROLE {rls.RLS_APP_ROLE}")
        self.cur.execute("SET LOCAL app.current_user_id = %s", (user,))
        self.cur.execute("SET LOCAL app.current_tenant_id = %s", (tenant,))
        self.cur.execute("SET LOCAL app.current_workspace_id = %s", (str(workspace),))

    def test_employee_shared_read_owner_non_creator_update_and_legacy_isolation(self):
        self._context(EMPLOYEE)
        with mock.patch.object(
            shared_express_schema, "erp_shared_express_endpoint_enabled_for", return_value=True
        ):
            self.assertTrue(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        self.cur.execute(
            "SELECT current_setting('app.erp_shared_express_endpoint', true) AS gate, "
            "current_setting('app.erp_shared_express_tenant_id', true) AS tenant, "
            "current_setting('app.erp_shared_express_workspace_id', true) AS workspace"
        )
        gate = self.cur.fetchone()
        self.assertEqual(gate["gate"], "on")
        self.assertEqual(gate["tenant"], TENANT_A)
        self.assertEqual(gate["workspace"], str(WORKSPACE_A))
        self.cur.execute("SELECT id FROM erp_endpoints ORDER BY id")
        self.assertEqual([row["id"] for row in self.cur.fetchall()], [MANAGED])
        self.conn.rollback()

        self._context(OWNER)
        self.assertTrue(
            managed.enable_managed_express_owner_access(
                self.cur,
                tenant_id=TENANT_A,
                workspace_client_id=WORKSPACE_A,
                actor_user_id=OWNER,
            )
        )
        self.cur.execute("SELECT id FROM erp_endpoints")
        self.assertEqual([row["id"] for row in self.cur.fetchall()], [MANAGED])
        self.cur.execute("UPDATE erp_endpoints SET name='owner-updated' WHERE id=%s", (MANAGED,))
        self.assertEqual(self.cur.rowcount, 1)
        self.cur.execute("DELETE FROM erp_endpoints WHERE id=%s", (MANAGED,))
        self.assertEqual(self.cur.rowcount, 0)
        self.conn.rollback()

    def test_managed_delete_is_denied_but_legacy_delete_remains_user_scoped(self):
        self._context(CREATOR)
        self.cur.execute("SET LOCAL app.bypass_rls = 'on'")
        self.cur.execute("SELECT id FROM erp_endpoints ORDER BY id")
        self.assertEqual([row["id"] for row in self.cur.fetchall()], [LEGACY])
        self.cur.execute("DELETE FROM erp_endpoints WHERE id=%s", (MANAGED,))
        self.assertEqual(self.cur.rowcount, 0)
        self.cur.execute("DELETE FROM erp_endpoints WHERE id=%s", (LEGACY,))
        self.assertEqual(self.cur.rowcount, 1)
        self.conn.rollback()

    def test_legacy_partial_unique_rejects_duplicate_but_keeps_managed(self):
        import psycopg2

        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.cur.execute(
                "INSERT INTO erp_endpoints (id,user_id,name,adapter) VALUES (%s,%s,'duplicate','express')",
                (str(uuid.uuid4()), CREATOR),
            )

    def test_managed_creator_is_immutable_and_shared_rows_require_generation(self):
        import psycopg2

        self._context(OWNER)
        self.assertTrue(
            managed.enable_managed_express_owner_access(
                self.cur,
                tenant_id=TENANT_A,
                workspace_client_id=WORKSPACE_A,
                actor_user_id=OWNER,
            )
        )
        with self.assertRaises(psycopg2.Error):
            self.cur.execute("UPDATE erp_endpoints SET user_id=%s WHERE id=%s", (OWNER, MANAGED))
        self.conn.rollback()

        self._context(OWNER)
        self.assertTrue(
            managed.enable_managed_express_owner_access(
                self.cur,
                tenant_id=TENANT_A,
                workspace_client_id=WORKSPACE_A,
                actor_user_id=OWNER,
            )
        )
        self.cur.execute("SET LOCAL app.bypass_rls = 'on'")
        self.cur.execute("SET LOCAL app.erp_managed_creator_delete = 'on'")
        with self.assertRaises(psycopg2.Error):
            self.cur.execute("UPDATE erp_endpoints SET user_id=%s WHERE id=%s", (OWNER, MANAGED))
        self.conn.rollback()

        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.cur.execute(
                "INSERT INTO erp_endpoints "
                "(id,user_id,name,adapter,tenant_id,workspace_client_id,binding_generation,shared_scope) "
                "VALUES (%s,%s,'invalid','express',%s,%s,0,TRUE)",
                (str(uuid.uuid4()), OWNER, TENANT_A, WORKSPACE_A),
            )
        self.conn.rollback()

    def test_creator_delete_preserves_managed_and_cascades_legacy(self):
        self._context(CREATOR)
        self.cur.execute("DELETE FROM users WHERE id=%s", (CREATOR,))
        self.assertEqual(self.cur.rowcount, 1)
        self.cur.execute("RESET ROLE")
        self.cur.execute("SET LOCAL row_security = off")
        self.cur.execute("SELECT user_id FROM erp_endpoints WHERE id=%s", (MANAGED,))
        self.assertEqual(self.cur.fetchone(), {"user_id": None})
        self.cur.execute("SELECT 1 FROM erp_endpoints WHERE id=%s", (LEGACY,))
        self.assertIsNone(self.cur.fetchone())
        self.conn.rollback()

    def test_tenant_delete_cascades_managed_endpoint(self):
        self._context(OWNER)
        self.cur.execute("RESET ROLE; SET LOCAL row_security = off")
        self.cur.execute("SELECT 1 FROM erp_endpoints WHERE id=%s", (MANAGED,))
        self.assertIsNotNone(self.cur.fetchone())
        self.cur.execute("DELETE FROM tenants WHERE id=%s", (TENANT_A,))
        self.assertEqual(self.cur.rowcount, 1)
        self.cur.execute("SELECT 1 FROM erp_endpoints WHERE id=%s", (MANAGED,))
        self.assertIsNone(self.cur.fetchone())
        self.conn.rollback()

    def test_demo_teardown_deletes_endpoint_before_creator(self):
        demo_user = str(uuid.uuid4())
        demo_endpoint = str(uuid.uuid4())
        self.cur.execute("INSERT INTO users (id,tenant_id) VALUES (%s,%s)", (demo_user, TENANT_A))
        self.cur.execute(
            "INSERT INTO erp_endpoints "
            "(id,user_id,name,adapter,tenant_id,workspace_client_id,binding_generation,shared_scope) "
            "VALUES (%s,%s,'demo','express',%s,%s,1,TRUE)",
            (demo_endpoint, demo_user, TENANT_A, WORKSPACE_A),
        )
        self.cur.execute(
            "SELECT public.purge_managed_erp_endpoints_for_users(%s::uuid[]) AS deleted",
            ([demo_user],),
        )
        self.assertEqual(self.cur.fetchone()["deleted"], 1)
        self._context(OWNER)
        self.cur.execute("SET LOCAL app.bypass_rls = 'on'")
        self.cur.execute("DELETE FROM erp_endpoints WHERE id=%s", (demo_endpoint,))
        self.assertEqual(self.cur.rowcount, 0)
        self.cur.execute("DELETE FROM users WHERE id=%s", (demo_user,))
        self.assertEqual(self.cur.rowcount, 1)
        self.cur.execute("SELECT 1 FROM erp_endpoints WHERE user_id=%s", (demo_user,))
        self.assertIsNone(self.cur.fetchone())
        self.conn.rollback()

    def test_trigger_shape_and_drift_are_checked(self):
        self.cur.execute(
            "SELECT procedure_meta.prosecdef, procedure_meta.proconfig "
            "FROM pg_proc procedure_meta "
            "WHERE procedure_meta.oid = "
            "'public.prevent_managed_erp_endpoint_creator_change()'::regprocedure"
        )
        function_meta = self.cur.fetchone()
        self.assertTrue(function_meta["prosecdef"])
        self.assertEqual(function_meta["proconfig"], ["search_path=pg_catalog"])
        self.cur.execute(
            "SELECT pg_get_functiondef("
            "'public.prevent_managed_erp_endpoint_creator_change()'::regprocedure) AS body"
        )
        self.assertIn("pg_trigger_depth() = 1", self.cur.fetchone()["body"])
        self.cur.execute(
            "SELECT lower(pg_get_triggerdef(trigger_meta.oid)) AS definition "
            "FROM pg_trigger trigger_meta "
            "WHERE trigger_meta.tgrelid = 'erp_endpoints'::regclass "
            "AND trigger_meta.tgname = 'erp_endpoints_managed_creator_immutable'"
        )
        definition = self.cur.fetchone()["definition"]
        self.assertIn("before update of user_id", definition)
        self.assertIn("for each row", definition)
        self.assertIn("prevent_managed_erp_endpoint_creator_change", definition)
        self.cur.execute("SAVEPOINT trigger_drift")
        self.cur.execute("DROP TRIGGER erp_endpoints_managed_creator_immutable ON erp_endpoints")
        self.cur.execute(
            "CREATE TRIGGER erp_endpoints_managed_creator_immutable "
            "BEFORE INSERT ON erp_endpoints FOR EACH ROW "
            "EXECUTE FUNCTION public.prevent_managed_erp_endpoint_creator_change()"
        )
        import psycopg2

        with self.assertRaises(psycopg2.Error):
            for statement in _localized_ddl(self.schema):
                self.cur.execute(statement)
        self.cur.execute("ROLLBACK TO SAVEPOINT trigger_drift")
        self.cur.execute("RELEASE SAVEPOINT trigger_drift")
        self.conn.rollback()

    def test_set_local_managed_gate_does_not_leak_after_commit(self):
        self._context(OWNER)
        self.assertTrue(
            managed.enable_managed_express_owner_access(
                self.cur,
                tenant_id=TENANT_A,
                workspace_client_id=WORKSPACE_A,
                actor_user_id=OWNER,
            )
        )
        self.conn.commit()
        self.cur.execute(
            "SELECT current_setting('app.erp_managed_express_owner', true) AS gate, "
            "current_setting('app.erp_managed_express_tenant_id', true) AS tenant"
        )
        row = self.cur.fetchone()
        self.assertEqual(row["gate"], "")
        self.assertEqual(row["tenant"], "")

    def test_two_startup_ensures_are_idempotent_under_race(self):
        schema = f"b3b2a_{uuid.uuid4().hex[:12]}"
        race_conn = connect()
        race_cur = race_conn.cursor()
        try:
            race_cur.execute(f'CREATE SCHEMA "{schema}"')
            race_cur.execute(f'CREATE TABLE "{schema}"."{DISPOSABLE_MARKER}" (note TEXT NOT NULL)')
            race_cur.execute(f'INSERT INTO "{schema}"."{DISPOSABLE_MARKER}" VALUES (\'ok\')')
            race_cur.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO {rls.RLS_APP_ROLE}')
            race_cur.execute(f'SET search_path TO "{schema}", public')
            _create_tables(race_cur)
            race_cur.execute(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON memberships, roles, users, workspace_clients TO {rls.RLS_APP_ROLE}"
            )
            race_cur.execute("INSERT INTO tenants (id,name) VALUES (%s,'race')", (TENANT_A,))
            race_cur.execute("INSERT INTO users (id,tenant_id) VALUES (%s,%s)", (OWNER, TENANT_A))
            race_cur.execute("INSERT INTO roles (id,name) VALUES (%s,'owner')", (OWNER,))
            race_cur.execute(
                f"INSERT INTO memberships VALUES ('{OWNER}','{OWNER}','{TENANT_A}','{OWNER}','active')"
            )
            race_cur.execute(f"INSERT INTO workspace_clients VALUES ({WORKSPACE_A},'{TENANT_A}')")
            race_conn.commit()
            race_cur.execute(
                f"SELECT bool_and(has_table_privilege('{rls.RLS_APP_ROLE}', table_name, 'SELECT') AND has_table_privilege('{rls.RLS_APP_ROLE}', table_name, 'INSERT') AND has_table_privilege('{rls.RLS_APP_ROLE}', table_name, 'UPDATE') AND has_table_privilege('{rls.RLS_APP_ROLE}', table_name, 'DELETE') AND NOT EXISTS (SELECT 1 FROM pg_class c, aclexplode(c.relacl) acl WHERE c.oid = table_name::regclass AND (acl.grantee = 0 OR (acl.grantee = '{rls.RLS_APP_ROLE}'::regrole AND acl.is_grantable)))) AS allowed FROM unnest(ARRAY['\"{schema}\".memberships','\"{schema}\".roles','\"{schema}\".users','\"{schema}\".workspace_clients']) AS table_name"
            )
            self.assertTrue(race_cur.fetchone()[0])
            race_cur.execute(
                "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=%s",
                (rls.RLS_APP_ROLE,),
            )
            self.assertEqual(race_cur.fetchone(), (False, False))
            for _ in range(2):
                for statement in _localized_ddl(schema):
                    race_cur.execute(statement)
                race_conn.commit()
            errors = []
            reached = []
            ensure_barrier = threading.Barrier(2)

            def ensure_action(cur):
                ensure_barrier.wait(timeout=5)
                for statement in _localized_ddl(schema):
                    cur.execute(statement)
                reached.append("ensure")

            threads = [
                threading.Thread(target=_run_race_thread, args=(schema, errors, ensure_action))
                for _ in range(2)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=15)
            self.assertFalse(any(thread.is_alive() for thread in threads) or errors, errors)
            self.assertEqual(reached.count("ensure"), 2)

            authority_barrier = threading.Barrier(2)

            def owner_action(cur):
                authority_barrier.wait(timeout=5)
                cur.execute(f"SET LOCAL ROLE {rls.RLS_APP_ROLE}")
                cur.execute("SET LOCAL app.current_user_id = %s", (OWNER,))
                cur.execute("SET LOCAL app.current_tenant_id = %s", (TENANT_A,))
                cur.execute("SET LOCAL app.current_workspace_id = %s", (str(WORKSPACE_A),))
                if not managed.enable_managed_express_owner_access(
                    cur,
                    tenant_id=TENANT_A,
                    workspace_client_id=WORKSPACE_A,
                    actor_user_id=OWNER,
                ):
                    raise AssertionError("owner authority unexpectedly unavailable")
                reached.append("owner")

            def transfer_action(cur):
                authority_barrier.wait(timeout=5)
                cur.execute(
                    f"SELECT membership.id FROM memberships membership JOIN roles role ON role.id = membership.role_id WHERE membership.user_id = '{OWNER}' AND membership.tenant_id = '{TENANT_A}' FOR UPDATE OF membership, role; SELECT id FROM users WHERE id = '{OWNER}' AND tenant_id = '{TENANT_A}' FOR UPDATE; SELECT id FROM workspace_clients WHERE id = {WORKSPACE_A} AND tenant_id = '{TENANT_A}' FOR UPDATE"
                )
                reached.append("transfer")

            authority_threads = [
                threading.Thread(target=_run_race_thread, args=(schema, errors, owner_action)),
                threading.Thread(target=_run_race_thread, args=(schema, errors, transfer_action)),
            ]
            for thread in authority_threads:
                thread.start()
            for thread in authority_threads:
                thread.join(timeout=15)
            self.assertFalse(any(t.is_alive() for t in authority_threads) or errors, errors)
            self.assertEqual((reached.count("owner"), reached.count("transfer")), (1, 1))
        finally:
            require_disposable_db(race_cur, schema)
            race_cur.execute(f'DROP SCHEMA "{schema}" CASCADE')
            race_conn.commit()
            race_cur.close()
            race_conn.close()
