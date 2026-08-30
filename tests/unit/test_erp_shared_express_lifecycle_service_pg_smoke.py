"""Real-connection service transaction proof for the managed Express CAS lane.

The service's global pool is replaced only with a task-owned connection
contextmanager. Its SQL, endpoint advisory lock, RLS policy, trigger, busy
helper, CAS update, and audit insert all execute against disposable PostgreSQL;
``resolve`` is the sole narrow authz seam because the fixture has no full
production permission graph.
"""

from __future__ import annotations

import uuid
import json
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp import shared_express_lifecycle as service
from services.erp import shared_express_lifecycle_schema as schema
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
SECOND_OWNER = "55555555-5555-4555-8555-555555555555"
WORKSPACE = 101
TARGET = 202


def _localize(statement: str, schema_name: str) -> str:
    for name in (
        "erp_endpoints",
        "erp_push_logs",
        "operation_logs",
        "workspace_clients",
        "memberships",
        "roles",
        "users",
    ):
        statement = statement.replace(f"public.{name}", f'"{schema_name}".{name}')
    for name in ("guard_erp_endpoint_lifecycle_columns", "erp_managed_endpoint_has_activity"):
        statement = statement.replace(f"public.{name}", f'"{schema_name}".{name}')
    return statement


class ServiceLifecyclePgSmoke:
    @classmethod
    def setup(cls):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        cls.conn = connect_or_skip()
        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema_name = f"smoke_service_lifecycle_{uuid.uuid4().hex[:12]}"
        cls.before = snapshot_public_routines(cls.cur)
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema_name}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema_name}", public')
        cls.cur.execute("""
            CREATE TABLE tenants (id uuid primary key);
            CREATE TABLE users (id uuid primary key, tenant_id uuid, is_active boolean not null default true);
            CREATE TABLE roles (id uuid primary key, name text not null);
            CREATE TABLE memberships (id uuid primary key, user_id uuid, tenant_id uuid, role_id uuid, status text not null);
            CREATE TABLE workspace_clients (id bigint primary key, tenant_id uuid not null, is_active boolean not null default true, erp_endpoint_id uuid, updated_at timestamptz not null default now());
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
            CREATE TABLE erp_push_logs (id uuid primary key, user_id uuid not null, endpoint_id uuid, status text not null, next_retry_at timestamptz, lease_owner text, lease_expires_at timestamptz);
            CREATE TABLE operation_logs (
              id bigserial primary key, tenant_id uuid, actor_user_id uuid, actor_username text,
              actor_is_super boolean not null default false, action text, target_type text,
              target_id text, target_name text, details jsonb, ip inet, ua text
            );
            """)
        ensure_rls_app_role(cls.cur)
        cls.cur.execute(f'GRANT USAGE ON SCHEMA "{cls.schema_name}" TO {RLS_APP_ROLE}')
        cls.cur.execute(
            f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "{cls.schema_name}" TO {RLS_APP_ROLE}'
        )
        cls.cur.execute(
            f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "{cls.schema_name}" TO {RLS_APP_ROLE}'
        )
        for statement in schema.SHARED_EXPRESS_LIFECYCLE_DDL:
            cls.cur.execute(_localize(statement, cls.schema_name))
        cls.cur.execute(
            "SELECT to_regprocedure('public.erp_managed_endpoint_has_activity(uuid)') AS routine"
        )
        if cls.cur.fetchone()["routine"] is not None:
            raise RuntimeError(
                "public managed activity helper already exists; refusing to replace it"
            )
        cls.cur.execute(f"""CREATE FUNCTION public.erp_managed_endpoint_has_activity(uuid)
                RETURNS boolean LANGUAGE sql
                AS $$ SELECT "{cls.schema_name}".erp_managed_endpoint_has_activity($1) $$""")
        cls.cur.execute(
            "GRANT EXECUTE ON FUNCTION public.erp_managed_endpoint_has_activity(uuid) TO "
            + RLS_APP_ROLE
        )
        cls.cur.execute(f'ALTER TABLE "{cls.schema_name}".erp_endpoints ENABLE ROW LEVEL SECURITY')
        cls.cur.execute(f'ALTER TABLE "{cls.schema_name}".erp_endpoints FORCE ROW LEVEL SECURITY')
        cls.conn.commit()
        schema._LIFECYCLE_SCHEMA_READY = True

    @classmethod
    def teardown(cls):
        cls.conn.rollback()
        cls.cur.execute(f'SET search_path TO "{cls.schema_name}", public')
        require_disposable_db(cls.cur, cls.schema_name, "smoke_service_lifecycle_")
        cls.cur.execute(f'DROP SCHEMA "{cls.schema_name}" CASCADE')
        cls.cur.execute("DROP FUNCTION public.erp_managed_endpoint_has_activity(uuid)")
        cls.conn.commit()
        assert_public_routines_unchanged(cls.cur, cls.before)
        cls.cur.close()
        cls.conn.close()

    def reset(self):
        self.cur = self.__class__.cur
        self.conn = self.__class__.conn
        self.conn.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema_name}", public')
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "TRUNCATE erp_push_logs, operation_logs, erp_endpoints, memberships, roles, users, workspace_clients, tenants CASCADE"
        )
        self.cur.execute("INSERT INTO tenants VALUES (%s)", (TENANT,))
        self.cur.execute("INSERT INTO users VALUES (%s,%s,TRUE)", (OWNER, TENANT))
        self.cur.execute("INSERT INTO users VALUES (%s,%s,TRUE)", (SECOND_OWNER, TENANT))
        self.cur.execute("INSERT INTO roles VALUES (%s,'owner')", (ROLE,))
        self.cur.execute(
            "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
            (str(uuid.uuid4()), OWNER, TENANT, ROLE),
        )
        self.cur.execute(
            "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
            (str(uuid.uuid4()), SECOND_OWNER, TENANT, ROLE),
        )
        self.cur.execute(
            "INSERT INTO workspace_clients (id,tenant_id,is_active,erp_endpoint_id) VALUES (%s,%s,TRUE,%s),(%s,%s,TRUE,NULL)",
            (WORKSPACE, TENANT, ENDPOINT, TARGET, TENANT),
        )
        self.cur.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter,config,enabled,shared_scope,tenant_id,workspace_client_id,binding_generation) VALUES (%s,%s,'managed','express',%s::jsonb,TRUE,TRUE,%s,%s,1)",
            (ENDPOINT, OWNER, '{"agent_token":"secret","keep":1}', TENANT, WORKSPACE),
        )
        self.cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        self.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()

    def prepare(self, enabled: bool):
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute(
            "ALTER TABLE erp_endpoints DISABLE TRIGGER erp_endpoints_lifecycle_columns_guard"
        )
        self.cur.execute(
            "UPDATE erp_endpoints SET enabled=%s, shared_scope=TRUE, workspace_client_id=%s, binding_generation=1, revoked_at=NULL, revoked_by=NULL, config=%s::jsonb WHERE id=%s",
            (enabled, WORKSPACE, '{"agent_token":"secret","keep":1}', ENDPOINT),
        )
        self.cur.execute(
            "ALTER TABLE erp_endpoints ENABLE TRIGGER erp_endpoints_lifecycle_columns_guard"
        )
        self.cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        self.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()

    def _endpoint(self):
        self.cur.execute("ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY")
        self.cur.execute("SELECT * FROM erp_endpoints WHERE id=%s", (ENDPOINT,))
        return self.cur.fetchone()

    @contextmanager
    def service_cursor(
        self, tenant_id=None, user_id=None, workspace_client_id=None, commit=False, **_kwargs
    ):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(LOCAL_DSN)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f'SET search_path TO "{self.schema_name}", public')
        cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        for key, value in (
            ("app.current_tenant_id", tenant_id),
            ("app.current_user_id", user_id),
            ("app.current_workspace_id", workspace_client_id),
        ):
            if value is not None:
                cur.execute("SELECT set_config(%s,%s,true)", (key, str(value)))
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def call(self, action, *, enabled, target=None, reason="test", confirm=False):
        self.reset()
        self.prepare(enabled)
        user = {"id": OWNER, "tenant_id": TENANT, "username": "owner"}
        with (
            patch.object(service.db, "get_cursor_rls", self.service_cursor),
            patch.object(
                service,
                "resolve",
                return_value=SimpleNamespace(
                    membership_id="m", role_key="owner", has=lambda _: True
                ),
            ),
            patch.object(service, "lifecycle_schema_ready", return_value=True),
        ):
            return service.change_shared_express_endpoint(
                user=user,
                endpoint_id=ENDPOINT,
                action=action,
                operation_id=str(uuid.uuid4()),
                expected_generation=1,
                source_workspace_id=WORKSPACE,
                target_workspace_id=target,
                reason=reason,
                confirm=confirm,
            )


class ServiceLifecyclePgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pg_service = ServiceLifecyclePgSmoke()
        cls.pg_service.setup()

    @classmethod
    def tearDownClass(cls):
        cls.pg_service.teardown()

    def test_service_four_actions_use_real_transactions(self):
        pg_service = self.pg_service
        for action, enabled, target, confirm in (
            ("disable", True, None, False),
            ("enable", False, None, False),
            ("rebind", False, TARGET, False),
            ("revoke", False, None, True),
        ):
            response = pg_service.call(action, enabled=enabled, target=target, confirm=confirm)
            self.assertTrue(response["ok"])
            self.assertEqual(response["generation"], 2)
            row = pg_service._endpoint()
            self.assertEqual(row["binding_generation"], 2)
            if action == "revoke":
                self.assertIsNone(row["workspace_client_id"])
                self.assertFalse(row["shared_scope"])

    def test_service_audit_failure_rolls_back_endpoint_workspace_and_log(self):
        pg_service = self.pg_service
        pg_service.reset()
        pg_service.prepare(False)
        pg_service.cur.execute(
            "CREATE OR REPLACE FUNCTION fail_service_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.details->>'reason' = 'force_failure' THEN RAISE EXCEPTION 'audit failure'; END IF; RETURN NEW; END $$"
        )
        pg_service.cur.execute(
            "CREATE TRIGGER fail_service_audit BEFORE INSERT ON operation_logs FOR EACH ROW EXECUTE FUNCTION fail_service_audit()"
        )
        pg_service.conn.commit()
        with self.assertRaisesRegex(Exception, "audit failure"):
            pg_service.call("rebind", enabled=False, target=TARGET, reason="force_failure")
        pg_service.cur.execute("DROP TRIGGER fail_service_audit ON operation_logs")
        pg_service.cur.execute("DROP FUNCTION fail_service_audit()")
        row = pg_service._endpoint()
        self.assertEqual(row["binding_generation"], 1)
        self.assertEqual(row["workspace_client_id"], WORKSPACE)
        pg_service.cur.execute(
            "SELECT erp_endpoint_id FROM workspace_clients WHERE id=%s", (WORKSPACE,)
        )
        self.assertEqual(str(pg_service.cur.fetchone()["erp_endpoint_id"]), ENDPOINT)
        pg_service.cur.execute("SELECT count(*) AS count FROM operation_logs")
        self.assertEqual(pg_service.cur.fetchone()["count"], 0)

    def test_service_busy_and_wrong_tenant_do_not_partially_write(self):
        pg_service = self.pg_service
        pg_service.reset()
        pg_service.prepare(True)
        pg_service.cur.execute(
            "INSERT INTO erp_push_logs VALUES (%s,%s,%s,'pending',NULL,NULL,NULL)",
            (str(uuid.uuid4()), OWNER, ENDPOINT),
        )
        pg_service.conn.commit()
        user = {"id": OWNER, "tenant_id": TENANT, "username": "owner"}
        with (
            patch.object(service.db, "get_cursor_rls", pg_service.service_cursor),
            patch.object(
                service,
                "resolve",
                return_value=SimpleNamespace(
                    membership_id="m", role_key="owner", has=lambda _: True
                ),
            ),
            patch.object(service, "lifecycle_schema_ready", return_value=True),
        ):
            with self.assertRaises(service.HTTPException) as exc:
                service.change_shared_express_endpoint(
                    user=user,
                    endpoint_id=ENDPOINT,
                    action="disable",
                    operation_id=str(uuid.uuid4()),
                    expected_generation=1,
                    source_workspace_id=WORKSPACE,
                )
        self.assertEqual(exc.exception.detail, "erp.endpoint_busy")
        row = pg_service._endpoint()
        self.assertTrue(row["enabled"])
        self.assertEqual(row["binding_generation"], 1)

        pg_service.reset()
        user = {
            "id": OWNER,
            "tenant_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "username": "owner",
        }
        with (
            patch.object(service.db, "get_cursor_rls", pg_service.service_cursor),
            patch.object(
                service,
                "resolve",
                return_value=SimpleNamespace(
                    membership_id="m", role_key="owner", has=lambda _: True
                ),
            ),
            patch.object(service, "lifecycle_schema_ready", return_value=True),
        ):
            with self.assertRaises(service.HTTPException) as exc:
                service.change_shared_express_endpoint(
                    user=user,
                    endpoint_id=ENDPOINT,
                    action="disable",
                    operation_id=str(uuid.uuid4()),
                    expected_generation=1,
                    source_workspace_id=WORKSPACE,
                )
        self.assertEqual(exc.exception.detail, "authz.not_found")
        row = pg_service._endpoint()
        self.assertTrue(row["enabled"])
        self.assertEqual(row["binding_generation"], 1)

    def test_service_target_conflict_does_not_partially_write(self):
        pg_service = self.pg_service
        pg_service.reset()
        pg_service.prepare(False)
        pg_service.cur.execute(
            "UPDATE workspace_clients SET erp_endpoint_id=%s WHERE id=%s",
            ("44444444-4444-4444-8444-444444444444", TARGET),
        )
        pg_service.conn.commit()
        user = {"id": OWNER, "tenant_id": TENANT, "username": "owner"}
        with (
            patch.object(service.db, "get_cursor_rls", pg_service.service_cursor),
            patch.object(
                service,
                "resolve",
                return_value=SimpleNamespace(
                    membership_id="m", role_key="owner", has=lambda _: True
                ),
            ),
            patch.object(service, "lifecycle_schema_ready", return_value=True),
        ):
            with self.assertRaises(service.HTTPException) as exc:
                service.change_shared_express_endpoint(
                    user=user,
                    endpoint_id=ENDPOINT,
                    action="rebind",
                    operation_id=str(uuid.uuid4()),
                    expected_generation=1,
                    source_workspace_id=WORKSPACE,
                    target_workspace_id=TARGET,
                )
        self.assertEqual(exc.exception.detail, "erp.workspace_endpoint_conflict")
        row = pg_service._endpoint()
        self.assertEqual(row["workspace_client_id"], WORKSPACE)
        self.assertEqual(row["binding_generation"], 1)
        pg_service.cur.execute(
            "SELECT erp_endpoint_id FROM workspace_clients WHERE id=%s", (WORKSPACE,)
        )
        self.assertEqual(str(pg_service.cur.fetchone()["erp_endpoint_id"]), ENDPOINT)

    def test_operation_replay_same_uuid_is_tenant_global(self):
        pg_service = self.pg_service
        pg_service.reset()
        operation_id = str(uuid.uuid4())
        details = {
            "operation_id": operation_id,
            "endpoint_id": ENDPOINT,
            "action": "disable",
            "workspace_before": WORKSPACE,
            "workspace_after": WORKSPACE,
            "target_workspace_client_id": None,
            "expected_generation": 1,
            "generation_after": 2,
            "enabled_after": False,
            "shared_scope_after": True,
            "revoked_after": False,
            "reason": "tenant-global replay",
        }
        pg_service.cur.execute(
            "INSERT INTO operation_logs (tenant_id, actor_user_id, action, target_type, target_id, details) "
            "VALUES (%s,%s,'erp.endpoint.disable','erp_endpoint',%s,%s::jsonb)",
            (TENANT, OWNER, ENDPOINT, json.dumps(details)),
        )
        pg_service.conn.commit()

        response = service._operation_replay(
            pg_service.cur,
            tenant_id=TENANT,
            actor_id=OWNER,
            operation_id=operation_id,
            endpoint_id=ENDPOINT,
            action="disable",
            source_workspace_id=WORKSPACE,
            target_workspace_id=None,
            expected_generation=1,
            reason="tenant-global replay",
        )
        self.assertEqual(response["operation_id"], operation_id)

        with self.assertRaisesRegex(service.LifecycleError, "operation_id_conflict"):
            service._operation_replay(
                pg_service.cur,
                tenant_id=TENANT,
                actor_id=SECOND_OWNER,
                operation_id=operation_id,
                endpoint_id="44444444-4444-4444-8444-444444444444",
                action="disable",
                source_workspace_id=WORKSPACE,
                target_workspace_id=None,
                expected_generation=1,
                reason="tenant-global replay",
            )

    def test_concurrent_service_cas_has_one_winner(self):
        pg_service = self.pg_service
        import threading

        pg_service.reset()
        barrier = threading.Barrier(2)
        outcomes = []
        operation_id = str(uuid.uuid4())

        def worker(actor):
            user = {"id": actor, "tenant_id": TENANT, "username": "owner"}
            barrier.wait(timeout=3)
            try:
                response = service.change_shared_express_endpoint(
                    user=user,
                    endpoint_id=ENDPOINT,
                    action="disable",
                    operation_id=operation_id,
                    expected_generation=1,
                    source_workspace_id=WORKSPACE,
                )
                outcomes.append(response["generation"])
            except service.HTTPException as exc:
                outcomes.append(exc.detail)
            except Exception as exc:  # keep real database failures deterministic
                outcomes.append(f"unexpected:{type(exc).__name__}:{exc}")

        with (
            patch.object(service.db, "get_cursor_rls", pg_service.service_cursor),
            patch.object(
                service,
                "resolve",
                return_value=SimpleNamespace(
                    membership_id="m", role_key="owner", has=lambda _: True
                ),
            ),
            patch.object(service, "lifecycle_schema_ready", return_value=True),
        ):
            threads = [
                threading.Thread(target=worker, args=(actor,)) for actor in (OWNER, SECOND_OWNER)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(set(outcomes), {2, "erp.operation_id_conflict"})
        row = pg_service._endpoint()
        self.assertFalse(row["enabled"])
        self.assertEqual(row["binding_generation"], 2)
