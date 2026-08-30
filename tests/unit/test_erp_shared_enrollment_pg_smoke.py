"""Real PostgreSQL proof for the managed Express enrollment boundary."""

from __future__ import annotations

import contextlib
import queue
import threading
import uuid
import unittest
from unittest import mock

from core import db
from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp import shared_express_enrollment as enrollment_service
from services.erp import shared_express_enrollment_schema as enrollment_schema
from services.erp import shared_express_managed_schema as managed_schema
from services.erp.shared_express_enrollment import enroll_legacy_express_endpoint
from services.erp.push_retry import _lock_log_endpoint
from services.erp.legacy_generation import lock_endpoint_binding
from services.workspace.endpoint_binding import bind_workspace_endpoint
from tests.unit._pg_smoke import (
    LOCAL_DSN,
    assert_public_routines_unchanged,
    connect_or_skip,
    require_disposable_db,
    schema_function,
    schema_function_name,
    snapshot_public_routines,
)

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
OWNER = "11111111-1111-1111-1111-111111111111"
EMPLOYEE = "22222222-2222-2222-2222-222222222222"
ADMIN = "33333333-3333-3333-3333-333333333333"
CUSTOM = "44444444-4444-4444-4444-444444444444"
OWNER_ROLE = "aaaaaaaa-0000-0000-0000-000000000001"
ADMIN_ROLE = "aaaaaaaa-0000-0000-0000-000000000002"
CUSTOM_ROLE = "aaaaaaaa-0000-0000-0000-000000000003"
ENDPOINT = "aaaaaaaa-1111-1111-1111-111111111111"
WORKSPACE_A = 101
WORKSPACE_B = 202


def _schema_ddl(statement: str, schema: str) -> str:
    """Make runtime DDL target this disposable schema, never public tables."""
    localized = (
        statement.replace("public.erp_endpoints", f'"{schema}".erp_endpoints')
        .replace("public.erp_push_logs", f'"{schema}".erp_push_logs')
        .replace("public.users", f'"{schema}".users')
    )
    for name in (
        "preserve_managed_erp_endpoints_on_user_delete",
        "prevent_managed_erp_endpoint_creator_change",
        "purge_managed_erp_endpoints_for_users",
        "erp_endpoint_has_legacy_activity",
        "guard_erp_endpoint_enrollment_columns",
    ):
        localized = localized.replace(f"public.{name}", f'"{schema}".{name}')
    return localized


class EnrollmentPromotionPgSmokeTests(unittest.TestCase):
    conn = None
    cur = None
    schema = None
    _previous_managed_ready = None
    _previous_enrollment_ready = None
    _schema_prefix = "smoke_enroll_"

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        import psycopg2

        cls.cur = cls.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cls.schema = cls._schema_prefix + uuid.uuid4().hex[:12]
        cls._previous_managed_ready = managed_schema._MANAGED_FOUNDATION_READY
        cls._previous_enrollment_ready = enrollment_schema._ENROLLMENT_RLS_READY
        c = cls.cur
        cls._public_routines_before = snapshot_public_routines(c)
        c.execute(f'CREATE SCHEMA "{cls.schema}"')
        c.execute(f'SET search_path TO "{cls.schema}", public')
        c.execute("""
            CREATE TABLE tenants (id UUID PRIMARY KEY);
            CREATE TABLE users (
                id UUID PRIMARY KEY, tenant_id UUID NOT NULL REFERENCES tenants(id), role TEXT,
                invited_by UUID, is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            CREATE TABLE roles (
                id UUID PRIMARY KEY, key TEXT NOT NULL, name TEXT NOT NULL,
                permissions JSONB NOT NULL DEFAULT '{}'::jsonb, tenant_id UUID,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            CREATE TABLE memberships (
                id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
                tenant_id UUID NOT NULL REFERENCES tenants(id), role_id UUID NOT NULL REFERENCES roles(id),
                status TEXT NOT NULL, scope_mode TEXT NOT NULL DEFAULT 'all', granted_by UUID,
                granted_at TIMESTAMPTZ
            );
            CREATE TABLE workspace_clients (
                id BIGINT PRIMARY KEY, tenant_id UUID NOT NULL REFERENCES tenants(id),
                is_active BOOLEAN NOT NULL DEFAULT TRUE, erp_endpoint_id UUID,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE erp_endpoints (
                id UUID PRIMARY KEY, user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE, workspace_client_id BIGINT,
                name TEXT NOT NULL, adapter TEXT NOT NULL, config JSONB NOT NULL DEFAULT '{}'::jsonb,
                is_default BOOLEAN NOT NULL DEFAULT FALSE, auto_push BOOLEAN NOT NULL DEFAULT FALSE,
                enabled BOOLEAN NOT NULL DEFAULT TRUE, last_used_at TIMESTAMPTZ, last_status TEXT,
                success_count INTEGER NOT NULL DEFAULT 0, failure_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                shared_scope BOOLEAN NOT NULL DEFAULT FALSE, bound_account_set TEXT, bound_profile_key TEXT,
                live_account_set TEXT, live_profile_key TEXT, agent_last_seen_at TIMESTAMPTZ,
                agent_version TEXT, binding_generation BIGINT NOT NULL DEFAULT 0
            );
            CREATE TABLE erp_push_logs (
                id UUID PRIMARY KEY, user_id UUID NOT NULL, tenant_id UUID, workspace_client_id BIGINT,
                endpoint_id UUID, status TEXT NOT NULL DEFAULT 'succeeded', next_retry_at TIMESTAMPTZ,
                lease_owner TEXT, lease_expires_at TIMESTAMPTZ
            );
            CREATE TABLE operation_logs (
                id BIGSERIAL PRIMARY KEY, tenant_id UUID, actor_user_id UUID, actor_username TEXT,
                actor_is_super BOOLEAN, action TEXT, target_type TEXT, target_id TEXT, target_name TEXT,
                details JSONB, ip TEXT, ua TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
        for statement in managed_schema.SHARED_EXPRESS_MANAGED_DDL:
            c.execute(_schema_ddl(statement, cls.schema))
        for statement in enrollment_schema.SHARED_EXPRESS_ENROLLMENT_RLS_DDL:
            c.execute(_schema_ddl(statement, cls.schema))
        c.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        assert_public_routines_unchanged(c, cls._public_routines_before)
        cls.conn.commit()
        managed_schema._MANAGED_FOUNDATION_READY = True
        enrollment_schema._ENROLLMENT_RLS_READY = True

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            managed_schema._MANAGED_FOUNDATION_READY = cls._previous_managed_ready
            enrollment_schema._ENROLLMENT_RLS_READY = cls._previous_enrollment_ready
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, cls._schema_prefix)
            cls.cur.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')
            cls.conn.commit()
            assert_public_routines_unchanged(cls.cur, cls._public_routines_before)
        finally:
            cls.cur.close()
            cls.conn.close()

    def _reset_rows(self):
        c = self.cur
        self.conn.rollback()
        c.execute(f'SET search_path TO "{self.schema}", public')
        require_disposable_db(c, self.schema, self._schema_prefix)
        c.execute("RESET ROLE")
        c.execute(f'ALTER TABLE "{self.schema}".erp_endpoints DISABLE ROW LEVEL SECURITY')
        c.execute(
            "TRUNCATE erp_push_logs, operation_logs, erp_endpoints, memberships, roles, "
            "users, workspace_clients, tenants CASCADE"
        )
        c.execute("INSERT INTO tenants VALUES (%s), (%s)", (TENANT_A, TENANT_B))
        c.execute(
            "INSERT INTO users (id,tenant_id,role,is_active) VALUES "
            "(%s,%s,'owner',TRUE),(%s,%s,'member',TRUE),(%s,%s,'member',TRUE),(%s,%s,'member',TRUE)",
            (OWNER, TENANT_A, EMPLOYEE, TENANT_A, ADMIN, TENANT_A, CUSTOM, TENANT_A),
        )
        c.execute(
            "INSERT INTO roles (id,key,name,permissions,tenant_id) VALUES "
            "(%s,'owner','owner','{\"all\":true}',NULL),(%s,'admin','admin','[]',NULL),"
            "(%s,'custom:staff','custom:staff','[]',%s)",
            (OWNER_ROLE, ADMIN_ROLE, CUSTOM_ROLE, TENANT_A),
        )
        c.execute(
            "INSERT INTO memberships (id,user_id,tenant_id,role_id,status) VALUES "
            "(%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active')",
            (
                str(uuid.uuid4()),
                OWNER,
                TENANT_A,
                OWNER_ROLE,
                str(uuid.uuid4()),
                EMPLOYEE,
                TENANT_A,
                ADMIN_ROLE,
                str(uuid.uuid4()),
                ADMIN,
                TENANT_A,
                ADMIN_ROLE,
                str(uuid.uuid4()),
                CUSTOM,
                TENANT_A,
                CUSTOM_ROLE,
            ),
        )
        c.execute(
            "INSERT INTO workspace_clients (id,tenant_id,is_active) VALUES (%s,%s,TRUE),(%s,%s,TRUE),(%s,%s,TRUE)",
            (WORKSPACE_A, TENANT_A, WORKSPACE_B, TENANT_A, 303, TENANT_B),
        )
        c.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter,config,is_default,auto_push,enabled) "
            'VALUES (%s,%s,\'Legacy Express\',\'express\',\'{"agent_token":"secret-token","account_dir":"secret-dir"}\',TRUE,TRUE,TRUE)',
            (ENDPOINT, OWNER),
        )
        c.execute(f'ALTER TABLE "{self.schema}".erp_endpoints ENABLE ROW LEVEL SECURITY')
        c.execute(f'ALTER TABLE "{self.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        self.conn.commit()

    def setUp(self):
        self._reset_rows()

    @contextlib.contextmanager
    def _service_cursor(self, actor=OWNER, tenant=TENANT_A):
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        self.cur.execute(
            "SELECT set_config('app.current_tenant_id',%s,true), set_config('app.current_user_id',%s,true)",
            (tenant, actor),
        )
        try:
            yield self.cur
        except Exception:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()

    def _enroll(self, *, actor=OWNER, tenant=TENANT_A, workspace=WORKSPACE_A):
        user = {
            "id": actor,
            "tenant_id": tenant,
            "role": "owner" if actor == OWNER else "member",
            "username": "smoke",
        }
        with mock.patch.object(
            enrollment_service,
            "endpoint_has_legacy_activity",
            side_effect=self._namespaced_activity,
        ):
            with mock.patch.object(
                db, "get_cursor_rls", side_effect=lambda **_: self._service_cursor(actor, tenant)
            ):
                return enroll_legacy_express_endpoint(
                    user=user,
                    endpoint_id=ENDPOINT,
                    workspace_client_id=workspace,
                    request_ip="127.0.0.1",
                    request_ua="pg-smoke",
                )

    def _namespaced_activity(self, cur, endpoint_id):
        cur.execute(
            f"SELECT {schema_function_name(self.schema, 'erp_endpoint_has_legacy_activity')}(%s) AS busy",
            (str(endpoint_id),),
        )
        return bool(cur.fetchone()["busy"])

    def _set_context(self, actor=OWNER, tenant=TENANT_A, workspace=WORKSPACE_A):
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        self.cur.execute(
            "SELECT set_config('app.current_user_id',%s,true), set_config('app.current_tenant_id',%s,true), "
            "set_config('app.current_workspace_id',%s,true)",
            (actor, tenant, str(workspace)),
        )

    def test_valid_promotion_endpoint_workspace_audit_and_idempotent_retry(self):
        result = self._enroll()
        self.assertTrue(result["changed"])
        self.cur.execute(
            "SELECT binding_generation,tenant_id,workspace_client_id,shared_scope FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        self.assertEqual(tuple(self.cur.fetchone().values()), (1, TENANT_A, WORKSPACE_A, True))
        self.cur.execute("SELECT details::text FROM operation_logs WHERE target_id=%s", (ENDPOINT,))
        audit = self.cur.fetchone()["details"]
        self.assertNotIn("secret-token", audit)
        self.assertNotIn("secret-dir", audit)
        self.assertEqual(self.cur.rowcount, 1)
        second = self._enroll()
        self.assertFalse(second["changed"])
        self.cur.execute("SELECT count(*) AS n FROM operation_logs WHERE target_id=%s", (ENDPOINT,))
        self.assertEqual(self.cur.fetchone()["n"], 1)
        self.cur.execute(
            "SELECT erp_endpoint_id FROM workspace_clients WHERE id=%s", (WORKSPACE_A,)
        )
        self.assertEqual(str(self.cur.fetchone()["erp_endpoint_id"]), ENDPOINT)

    def test_same_sql_sensitive_column_changes_are_rejected_by_trigger(self):
        import psycopg2

        for column, value in (
            ("config", "'{\"stolen\":true}'::jsonb"),
            ("adapter", "'mrerp'"),
            ("user_id", "NULL"),
        ):
            self._reset_rows()
            self._set_context()
            with self.assertRaises(psycopg2.Error):
                self.cur.execute(
                    f"UPDATE erp_endpoints SET {column}={value}, binding_generation=1, shared_scope=TRUE, "
                    "tenant_id=%s, workspace_client_id=%s WHERE id=%s",
                    (TENANT_A, WORKSPACE_A, ENDPOINT),
                )
            self.conn.rollback()
            self.cur.execute("RESET ROLE")
            self.cur.execute(
                "SELECT binding_generation,config,user_id,adapter FROM erp_endpoints WHERE id=%s",
                (ENDPOINT,),
            )
            row = self.cur.fetchone()
            self.assertEqual(row["binding_generation"], 0)
            self.assertEqual(row["adapter"], "express")

    def test_wrong_tenant_workspace_employee_admin_custom_and_spoofed_gate_are_denied(self):
        for actor, tenant, workspace in (
            (OWNER, TENANT_B, WORKSPACE_A),
            (OWNER, TENANT_A, 999),
            (EMPLOYEE, TENANT_A, WORKSPACE_A),
            (ADMIN, TENANT_A, WORKSPACE_A),
            (CUSTOM, TENANT_A, WORKSPACE_A),
        ):
            self._reset_rows()
            self._set_context(actor, tenant, workspace)
            try:
                self.cur.execute(
                    "UPDATE erp_endpoints SET binding_generation=1,shared_scope=TRUE,tenant_id=%s,workspace_client_id=%s WHERE id=%s",
                    (TENANT_A, WORKSPACE_A, ENDPOINT),
                )
                self.assertEqual(self.cur.rowcount, 0)
            except Exception as exc:
                self.assertEqual(getattr(exc, "pgcode", None), "42501")
            self.conn.rollback()
        self._enroll()
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        self.cur.execute(
            "SELECT set_config('app.current_user_id',%s,true),set_config('app.current_tenant_id',%s,true),"
            "set_config('app.current_workspace_id',%s,true),set_config('app.erp_managed_express_owner','on',true),"
            "set_config('app.erp_managed_express_tenant_id',%s,true),set_config('app.erp_managed_express_workspace_id','999',true),"
            "set_config('app.erp_managed_express_actor_id',%s,true)",
            (OWNER, TENANT_A, str(WORKSPACE_A), TENANT_A, OWNER),
        )
        self.cur.execute("UPDATE erp_endpoints SET enabled=FALSE WHERE id=%s", (ENDPOINT,))
        self.assertEqual(self.cur.rowcount, 0)
        self.conn.rollback()

    def test_guc_commit_reset_and_audit_failure_roll_back_every_write(self):
        self._enroll()
        self.cur.execute(
            "SELECT current_setting('app.erp_managed_express_owner',true) AS gate, current_setting('app.current_workspace_id',true) AS ws"
        )
        row = self.cur.fetchone()
        self.assertIn(row["gate"], (None, ""))
        self.assertIn(row["ws"], (None, ""))
        self._reset_rows()
        with mock.patch(
            "services.erp.shared_express_enrollment.insert_operation_log_tx",
            side_effect=RuntimeError("audit down"),
        ):
            with self.assertRaises(RuntimeError):
                self._enroll()
        self.cur.execute(
            "SELECT binding_generation,shared_scope FROM erp_endpoints WHERE id=%s", (ENDPOINT,)
        )
        self.assertEqual(tuple(self.cur.fetchone().values()), (0, False))
        self.cur.execute("SELECT count(*) AS n FROM operation_logs")
        self.assertEqual(self.cur.fetchone()["n"], 0)

    def test_existing_multi_workspace_reference_is_a_zero_write_conflict(self):
        self.cur.execute(
            "UPDATE workspace_clients SET erp_endpoint_id=%s WHERE id IN (%s,%s)",
            (ENDPOINT, WORKSPACE_A, WORKSPACE_B),
        )
        self.conn.commit()
        with self.assertRaises(Exception) as raised:
            self._enroll()
        self.assertEqual(getattr(raised.exception, "status_code", None), 409)
        self.cur.execute(
            "SELECT binding_generation,tenant_id,workspace_client_id,shared_scope FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        self.assertEqual(tuple(self.cur.fetchone().values()), (0, None, None, False))
        self.cur.execute("SELECT id,erp_endpoint_id FROM workspace_clients ORDER BY id")
        refs = {row["id"]: row["erp_endpoint_id"] for row in self.cur.fetchall()}
        self.assertEqual(str(refs[WORKSPACE_A]), ENDPOINT)
        self.assertEqual(str(refs[WORKSPACE_B]), ENDPOINT)

    def test_activity_helper_scans_all_actors_and_expired_leases(self):
        self._set_context()
        self.cur.execute(
            "INSERT INTO erp_push_logs (id,user_id,endpoint_id,status,lease_owner,lease_expires_at) "
            "VALUES (%s,%s,%s,'success','employee-agent',NOW() - INTERVAL '1 hour')",
            (str(uuid.uuid4()), EMPLOYEE, ENDPOINT),
        )
        self.cur.execute(
            f"SELECT {schema_function_name(self.schema, 'erp_endpoint_has_legacy_activity')}(%s) AS busy",
            (ENDPOINT,),
        )
        self.assertTrue(self.cur.fetchone()["busy"])
        self.cur.execute("DELETE FROM erp_push_logs")
        self.cur.execute(
            "INSERT INTO erp_push_logs (id,user_id,endpoint_id,status) VALUES (%s,%s,%s,'success')",
            (str(uuid.uuid4()), EMPLOYEE, ENDPOINT),
        )
        self.cur.execute(
            f"SELECT {schema_function_name(self.schema, 'erp_endpoint_has_legacy_activity')}(%s) AS busy",
            (ENDPOINT,),
        )
        self.assertFalse(self.cur.fetchone()["busy"])

    def test_activity_helper_does_not_reveal_foreign_endpoint(self):
        self._set_context(actor=EMPLOYEE)
        self.cur.execute(
            "INSERT INTO erp_push_logs (id,user_id,endpoint_id,status) VALUES (%s,%s,%s,'pending')",
            (str(uuid.uuid4()), EMPLOYEE, ENDPOINT),
        )
        self.cur.execute(
            f"SELECT {schema_function_name(self.schema, 'erp_endpoint_has_legacy_activity')}(%s) AS busy",
            (ENDPOINT,),
        )
        self.assertFalse(self.cur.fetchone()["busy"])
        self.cur.execute(
            "SELECT set_config('app.current_user_id',%s,true), "
            f"{schema_function_name(self.schema, 'erp_endpoint_has_legacy_activity')}(%s) AS busy",
            (OWNER, ENDPOINT),
        )
        self.assertTrue(self.cur.fetchone()["busy"])

    def test_activity_helper_grant_is_safe_with_and_without_app_role(self):
        self.cur.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=%s) AS present, "
            "has_function_privilege(%s, %s, 'EXECUTE') AS allowed",
            (
                RLS_APP_ROLE,
                RLS_APP_ROLE,
                schema_function(self.schema, "erp_endpoint_has_legacy_activity", "uuid"),
            ),
        )
        role = self.cur.fetchone()
        self.assertTrue(role["present"])
        self.assertTrue(role["allowed"])

        absent_role = "pg_smoke_missing_" + uuid.uuid4().hex
        self.cur.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=%s) AS present",
            (absent_role,),
        )
        self.assertFalse(self.cur.fetchone()["present"])
        grant_ddl = next(
            statement
            for statement in enrollment_schema._LEGACY_ACTIVITY_FUNCTION_GRANT_DDL
            if "DO $pearnly$" in statement
        )
        self.cur.execute(_schema_ddl(grant_ddl.replace(RLS_APP_ROLE, absent_role), self.schema))
        self.conn.rollback()

    def test_enroll_uses_helper_busy_for_other_actor_and_expired_lease(self):
        self.cur.execute(
            "INSERT INTO erp_push_logs (id,user_id,endpoint_id,status,lease_owner,lease_expires_at) "
            "VALUES (%s,%s,%s,'success','stale-agent',NOW() - INTERVAL '1 second')",
            (str(uuid.uuid4()), EMPLOYEE, ENDPOINT),
        )
        self.conn.commit()
        with self.assertRaises(Exception) as raised:
            self._enroll()
        self.assertEqual(getattr(raised.exception, "status_code", None), 409)
        self.assertEqual(getattr(raised.exception, "detail", None), "erp.endpoint_busy")
        self.cur.execute(
            "SELECT binding_generation, shared_scope FROM erp_endpoints WHERE id=%s", (ENDPOINT,)
        )
        self.assertEqual(tuple(self.cur.fetchone().values()), (0, False))

    def test_activity_helper_catalog_contract_and_trigger_rejects_when(self):
        self.cur.execute(
            "SELECT p.prosecdef, p.proconfig, has_function_privilege(%s, "
            "%s, 'EXECUTE'), p.proacl::text "
            "FROM pg_proc p WHERE p.oid=%s::regprocedure",
            (
                RLS_APP_ROLE,
                schema_function(self.schema, "erp_endpoint_has_legacy_activity", "uuid"),
                schema_function(self.schema, "erp_endpoint_has_legacy_activity", "uuid"),
            ),
        )
        function = self.cur.fetchone()
        self.assertTrue(function["prosecdef"])
        self.assertEqual(function["proconfig"], ["search_path=pg_catalog"])
        self.assertTrue(function["has_function_privilege"])
        self.assertNotIn("{=X", function["proacl"] or "")
        self.assertNotIn(",=X", function["proacl"] or "")

        self.cur.execute(
            "SELECT tgenabled, tgtype, tgattr::text, tgqual IS NULL AS no_when, "
            "tgfoid=%s::regprocedure AS target "
            "FROM pg_trigger WHERE tgrelid=%s::regclass "
            "AND tgname='erp_endpoints_enrollment_columns_guard'",
            (
                schema_function(self.schema, "guard_erp_endpoint_enrollment_columns"),
                f'"{self.schema}".erp_endpoints',
            ),
        )
        trigger = self.cur.fetchone()
        self.assertEqual((trigger["tgenabled"], trigger["tgtype"]), ("O", 19))
        self.assertEqual(trigger["tgattr"], "")
        self.assertTrue(trigger["no_when"])
        self.assertTrue(trigger["target"])

        self.cur.execute("SAVEPOINT bad_enrollment_trigger")
        self.cur.execute(
            f'DROP TRIGGER "erp_endpoints_enrollment_columns_guard" ON "{self.schema}".erp_endpoints'
        )
        self.cur.execute(
            f'CREATE TRIGGER "erp_endpoints_enrollment_columns_guard" '
            f'BEFORE UPDATE ON "{self.schema}".erp_endpoints FOR EACH ROW '
            f"WHEN (FALSE) EXECUTE FUNCTION {schema_function(self.schema, 'guard_erp_endpoint_enrollment_columns')}"
        )
        with self.assertRaises(Exception):
            self.cur.execute(
                enrollment_schema._PROMOTION_GUARD_TRIGGER_DDL.replace(
                    "'erp_endpoints'::regclass", f"'\"{self.schema}\".erp_endpoints'::regclass"
                ).replace("public.erp_endpoints", f'"{self.schema}".erp_endpoints')
            )
        self.cur.execute("ROLLBACK TO SAVEPOINT bad_enrollment_trigger")

    def test_real_enroll_and_bind_helpers_serialize_on_endpoint(self):
        """The production helpers, not a SQL facsimile, have one winner."""
        barrier = threading.Barrier(2)
        outcomes = queue.Queue()
        local = threading.local()

        @contextlib.contextmanager
        def cursor_for_thread(*, tenant_id=None, user_id=None, **_kwargs):
            import psycopg2

            conn = local.conn
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
                cur.execute(
                    "SELECT set_config('app.current_user_id',%s,true), "
                    "set_config('app.current_tenant_id',%s,true)",
                    (str(user_id), str(tenant_id)),
                )
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

        def worker(kind):
            import psycopg2

            local.conn = psycopg2.connect(LOCAL_DSN, connect_timeout=3)
            try:
                local.conn.cursor().execute(f'SET search_path TO "{self.schema}", public')
                barrier.wait(timeout=2)
                if kind == "enroll":
                    result = enroll_legacy_express_endpoint(
                        user={
                            "id": OWNER,
                            "tenant_id": TENANT_A,
                            "role": "owner",
                            "username": "smoke",
                        },
                        endpoint_id=ENDPOINT,
                        workspace_client_id=WORKSPACE_A,
                        request_ip=None,
                        request_ua="race",
                    )
                    outcomes.put((kind, "success" if result["changed"] else "idempotent"))
                else:
                    outcomes.put(
                        (
                            kind,
                            (
                                "success"
                                if bind_workspace_endpoint(WORKSPACE_B, ENDPOINT, OWNER, TENANT_A)
                                else "conflict"
                            ),
                        )
                    )
            except Exception as exc:
                if getattr(exc, "status_code", None) == 409:
                    outcomes.put((kind, "conflict"))
                else:
                    outcomes.put((kind, f"error:{type(exc).__name__}:{exc}"))
            finally:
                local.conn.close()

        with (
            mock.patch.object(
                enrollment_service,
                "endpoint_has_legacy_activity",
                side_effect=self._namespaced_activity,
            ),
            mock.patch.object(db, "get_cursor_rls", side_effect=cursor_for_thread),
        ):
            threads = [
                threading.Thread(target=worker, args=("enroll",)),
                threading.Thread(target=worker, args=("bind",)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive(), "real enroll/bind race timed out")
        result = dict(outcomes.get(timeout=1) for _ in range(2))
        self.assertIn(
            (result["enroll"], result["bind"]),
            {("success", "conflict"), ("conflict", "success")},
        )

    def test_retry_helper_waits_on_binding_advisory_before_endpoint_share(self):
        """A retry cannot pass the endpoint lock while enrollment owns its advisory lock."""
        import psycopg2

        self.cur.execute(
            "INSERT INTO erp_push_logs (id,user_id,endpoint_id,status) VALUES (%s,%s,%s,'failed') RETURNING id",
            (str(uuid.uuid4()), OWNER, ENDPOINT),
        )
        log_id = str(self.cur.fetchone()["id"])
        self.conn.commit()
        first = psycopg2.connect(LOCAL_DSN, connect_timeout=3)
        second = psycopg2.connect(LOCAL_DSN, connect_timeout=3)
        first_cur = first.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        first_cur.execute(f'SET search_path TO "{self.schema}", public')
        lock_endpoint_binding(first_cur, ENDPOINT)
        result = queue.Queue()

        def retry_reader():
            cur = second.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cur.execute(f'SET search_path TO "{self.schema}", public')
                cur.execute("SET statement_timeout = '3000ms'")
                result.put(_lock_log_endpoint(cur, log_id))
                second.commit()
            except Exception as exc:
                second.rollback()
                result.put(exc)
            finally:
                cur.close()

        thread = threading.Thread(target=retry_reader)
        thread.start()
        thread.join(timeout=0.2)
        self.assertTrue(thread.is_alive(), "retry bypassed the endpoint advisory lock")
        first.commit()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "retry advisory lock wait timed out")
        outcome = result.get(timeout=1)
        self.assertEqual(outcome, (True, ENDPOINT))
        first_cur.close()
        first.close()
        second.close()


if __name__ == "__main__":
    unittest.main()
