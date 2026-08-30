"""Disposable PostgreSQL proof for managed live-profile guardrails."""

from __future__ import annotations

import uuid
import unittest
import hashlib
import os
from contextlib import contextmanager
from unittest import mock
from types import SimpleNamespace

from psycopg2.extras import RealDictCursor

from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp.shared_express_live_ddl import LIVE_DDL
from services.erp import shared_express_lifecycle_schema as lifecycle
from services.erp.shared_express_managed_schema import SHARED_EXPRESS_MANAGED_RLS_DDL
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


def _localize(statement: str, schema: str) -> str:
    out = statement
    for table in (
        "erp_endpoints",
        "erp_push_logs",
        "operation_logs",
        "workspace_clients",
        "tenants",
        "users",
        "memberships",
        "roles",
    ):
        out = out.replace(f"public.{table}", f'"{schema}".{table}')
    for function in (
        "guard_erp_endpoint_lifecycle_columns",
        "erp_managed_endpoint_has_activity",
        "erp_managed_live_authenticate",
        "guard_erp_endpoint_managed_live_columns",
        "guard_erp_endpoint_managed_profile_confirm",
    ):
        out = out.replace(f"public.{function}", f'"{schema}".{function}')
    out = out.replace("'public.erp_endpoints'::regclass", f"'\"{schema}\".erp_endpoints'::regclass")
    return out


class ManagedLivePgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema = f"smoke_live_{uuid.uuid4().hex[:12]}"
        cls.before = snapshot_public_routines(cls.cur)
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
        cls.cur.execute("""
            CREATE TABLE tenants (id uuid primary key, status text not null default 'active');
            CREATE TABLE users (id uuid primary key, tenant_id uuid, is_active boolean not null default true);
            CREATE TABLE roles (id uuid primary key, name text not null);
            CREATE TABLE memberships (id uuid primary key, user_id uuid, tenant_id uuid, role_id uuid, status text not null);
            CREATE TABLE workspace_clients (id bigint primary key, tenant_id uuid not null, is_active boolean not null default true, erp_endpoint_id uuid);
            CREATE TABLE erp_push_logs (id uuid primary key, user_id uuid, endpoint_id uuid, status text, next_retry_at timestamptz, lease_owner text, lease_expires_at timestamptz, tenant_id uuid);
            CREATE TABLE operation_logs (id bigserial primary key, tenant_id uuid, actor_user_id uuid, actor_username text, actor_is_super boolean not null default false, action text, target_type text, target_id text, target_name text, details jsonb, ip inet, ua text);
            CREATE TABLE erp_endpoints (
              id uuid primary key, user_id uuid, name text not null, adapter text not null,
              config jsonb not null default '{}', is_default boolean not null default false,
              auto_push boolean not null default false, enabled boolean not null default true,
              last_used_at timestamptz, last_status text, success_count integer not null default 0,
              failure_count integer not null default 0, created_at timestamptz not null default now(),
              updated_at timestamptz not null default now(), tenant_id uuid, workspace_client_id bigint,
              shared_scope boolean not null default false, bound_account_set text, bound_profile_key text,
              live_account_set text, live_profile_key text, agent_last_seen_at timestamptz,
              agent_version text, binding_generation bigint not null default 0,
              revoked_at timestamptz, revoked_by uuid,
              constraint binding_generation_chk check (binding_generation >= 0),
              constraint bound_pair_chk check ((bound_account_set is null) = (bound_profile_key is null)),
              constraint live_pair_chk check ((live_account_set is null) = (live_profile_key is null))
            );
            """)
        ensure_rls_app_role(cls.cur)
        cls.cur.execute(f'GRANT USAGE ON SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}')
        cls.cur.execute(
            f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}'
        )
        cls.cur.execute(
            f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}'
        )
        for statement in (
            lifecycle.SHARED_EXPRESS_LIFECYCLE_DDL + SHARED_EXPRESS_MANAGED_RLS_DDL + LIVE_DDL
        ):
            cls.cur.execute(_localize(statement, cls.schema))
        cls.cur.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints ENABLE ROW LEVEL SECURITY')
        cls.cur.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, "smoke_live_")
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.conn.commit()
            assert_public_routines_unchanged(cls.cur, cls.before)
        finally:
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        self.conn.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "TRUNCATE erp_endpoints, workspace_clients, memberships, roles, users, tenants CASCADE"
        )
        self.cur.execute("INSERT INTO tenants VALUES (%s, 'active')", (TENANT,))
        self.cur.execute("INSERT INTO users VALUES (%s,%s,TRUE)", (OWNER, TENANT))
        self.cur.execute("INSERT INTO roles VALUES (%s,'owner')", (ROLE,))
        self.cur.execute(
            "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
            (str(uuid.uuid4()), OWNER, TENANT, ROLE),
        )
        self.cur.execute(
            "INSERT INTO workspace_clients VALUES (%s,%s,TRUE,NULL)", (WORKSPACE, TENANT)
        )
        token_hash = hashlib.sha256(f"exp_{ENDPOINT}_secret".encode("utf-8")).hexdigest()
        self.cur.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter,config,enabled,shared_scope,tenant_id,workspace_client_id,binding_generation) "
            "VALUES (%s,%s,'managed','express',%s::jsonb,TRUE,TRUE,%s,%s,1)",
            (ENDPOINT, OWNER, '{"agent_token_hash":"%s"}' % token_hash, TENANT, WORKSPACE),
        )
        self.cur.execute("ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY")
        self.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
        self.conn.commit()

    def tearDown(self):
        self.conn.rollback()

    def _heartbeat_gate(self, generation=1):
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        for key, value in {
            "app.current_tenant_id": TENANT,
            "app.current_user_id": OWNER,
            "app.current_workspace_id": str(WORKSPACE),
            "app.erp_managed_live_heartbeat": "on",
            "app.erp_managed_live_tenant_id": TENANT,
            "app.erp_managed_live_actor_id": OWNER,
            "app.erp_managed_live_endpoint_id": ENDPOINT,
            "app.erp_managed_live_generation": str(generation),
        }.items():
            self.cur.execute("SELECT set_config(%s,%s,true)", (key, value))

    def test_heartbeat_typed_write_and_direct_write_rejection(self):
        self._heartbeat_gate()
        self.cur.execute(
            "UPDATE erp_endpoints SET live_account_set='main', live_profile_key='v1:x', agent_last_seen_at=NOW(), agent_version='1.1' WHERE id=%s",
            (ENDPOINT,),
        )
        self.cur.execute(
            "SELECT live_account_set, live_profile_key FROM erp_endpoints WHERE id=%s", (ENDPOINT,)
        )
        self.assertEqual(self.cur.fetchone()["live_account_set"], "main")
        self.conn.commit()
        self.cur.execute("SET LOCAL ROLE %s" % RLS_APP_ROLE)
        for key, value in {"app.current_tenant_id": TENANT, "app.current_user_id": OWNER}.items():
            self.cur.execute("SELECT set_config(%s,%s,true)", (key, value))
        self.cur.execute(
            "UPDATE erp_endpoints SET live_account_set='evil' WHERE id=%s", (ENDPOINT,)
        )
        self.assertEqual(self.cur.rowcount, 0)
        self.conn.rollback()

    def test_combined_lifecycle_and_live_update_is_rejected_by_0112(self):
        self._heartbeat_gate()
        with self.assertRaises(Exception):
            self.cur.execute(
                "UPDATE erp_endpoints SET enabled=FALSE, live_account_set='mixed' WHERE id=%s",
                (ENDPOINT,),
            )
        self.conn.rollback()

    def test_profile_confirm_gate_advances_generation_and_pair(self):
        self._heartbeat_gate()
        self.cur.execute(
            "UPDATE erp_endpoints SET live_account_set='main', live_profile_key='v1:x', agent_last_seen_at=NOW() WHERE id=%s",
            (ENDPOINT,),
        )
        self.cur.execute("SELECT set_config(%s,%s,true)", ("app.erp_managed_live_heartbeat", ""))
        self.cur.execute("SELECT set_config(%s,%s,true)", ("app.erp_managed_live_confirm", "on"))
        self.cur.execute(
            "SELECT set_config(%s,%s,true)", ("app.erp_managed_live_expected_generation", "1")
        )
        self.cur.execute(
            "SELECT set_config(%s,%s,true)", ("app.erp_managed_live_tenant_id", TENANT)
        )
        self.cur.execute("SELECT set_config(%s,%s,true)", ("app.erp_managed_live_actor_id", OWNER))
        self.cur.execute(
            "SELECT set_config(%s,%s,true)", ("app.erp_managed_live_endpoint_id", ENDPOINT)
        )
        self.cur.execute("SELECT set_config(%s,%s,true)", ("app.current_user_id", OWNER))
        self.cur.execute("SELECT set_config(%s,%s,true)", ("app.current_tenant_id", TENANT))
        self.cur.execute("SELECT id FROM erp_endpoints WHERE id=%s", (ENDPOINT,))
        self.assertIsNotNone(self.cur.fetchone())
        self.cur.execute(
            "UPDATE erp_endpoints SET bound_account_set=live_account_set, bound_profile_key=live_profile_key, binding_generation=2 WHERE id=%s AND binding_generation=1",
            (ENDPOINT,),
        )
        self.cur.execute(
            "SELECT binding_generation,bound_account_set FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        row = self.cur.fetchone()
        self.assertEqual(row["binding_generation"], 2)
        self.assertEqual(row["bound_account_set"], "main")

    def test_service_heartbeat_uses_real_transaction_and_typed_writer(self):
        from services.erp.shared_express_live import record_managed_heartbeat

        @contextmanager
        def real_cursor(commit=False):
            connection = __import__("psycopg2").connect(LOCAL_DSN, connect_timeout=3)
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            schema = self.schema

            class LocalizedCursor:
                def __getattr__(self, name):
                    return getattr(cursor, name)

                def execute(self, query, params=None):
                    query = query.replace(
                        "public.erp_managed_live_authenticate",
                        f'"{schema}".erp_managed_live_authenticate',
                    )
                    return cursor.execute(query, params)

            try:
                cursor.execute(f'SET search_path TO "{self.schema}", public')
                yield LocalizedCursor()
                if commit:
                    connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
                connection.close()

        token = f"exp_{ENDPOINT}_secret"
        with (
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            result = record_managed_heartbeat(
                token,
                account_set="main",
                account_dir=r"C:\Pearnly\Main",
                agent_version="1.1.64",
            )
        self.assertEqual(result["profile_status"], "unbound")
        self.assertFalse(result["profile_ready"])
        with (
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            invalid = record_managed_heartbeat(
                token, account_set=None, account_dir="bad", agent_version="1.1.64"
            )
        self.assertEqual(invalid["profile_status"], "needs_attention")
        self.cur.execute(
            "SELECT live_account_set, live_profile_key, agent_last_seen_at, agent_version FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        cleared = self.cur.fetchone()
        self.assertIsNone(cleared["live_account_set"])
        self.assertIsNotNone(cleared["agent_last_seen_at"])
        self.assertEqual(cleared["agent_version"], "1.1.64")
        with (
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            record_managed_heartbeat(
                token, account_set="main", account_dir=r"C:\Pearnly\Main", agent_version="1.1.64"
            )
        with (
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            offline = record_managed_heartbeat(
                token, account_set=None, account_dir=None, agent_version="1.1.64", offline=True
            )
        self.assertEqual(
            (offline["connected"], offline["profile_status"], offline["generation"]),
            (False, "offline", 1),
        )

    def test_service_confirm_real_cas_and_audit(self):
        from services.erp import shared_express_live as live

        @contextmanager
        def real_cursor(commit=False, **context):
            connection = __import__("psycopg2").connect(LOCAL_DSN, connect_timeout=3)
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            schema = self.schema

            class LocalizedCursor:
                def __getattr__(self, name):
                    return getattr(cursor, name)

                def execute(self, query, params=None):
                    for function in (
                        "erp_managed_live_authenticate",
                        "erp_managed_endpoint_has_activity",
                    ):
                        query = query.replace(f"public.{function}", f'"{schema}".{function}')
                    return cursor.execute(query, params)

            try:
                cursor.execute(f'SET search_path TO "{schema}", public')
                cursor.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
                if context.get("tenant_id"):
                    cursor.execute("SET LOCAL app.current_tenant_id = %s", (context["tenant_id"],))
                if context.get("workspace_client_id") is not None:
                    cursor.execute(
                        "SET LOCAL app.current_workspace_id = %s",
                        (str(context["workspace_client_id"]),),
                    )
                if context.get("user_id"):
                    cursor.execute("SET LOCAL app.current_user_id = %s", (context["user_id"],))
                yield LocalizedCursor()
                if commit:
                    connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
                connection.close()

        token = f"exp_{ENDPOINT}_secret"
        owner = {"id": OWNER, "tenant_id": TENANT, "username": "owner"}
        authz = SimpleNamespace(membership_id="membership", role_key="owner", has=lambda code: True)

        def owner_gate(cur, **_kwargs):
            for key, value in {
                "app.erp_managed_express_owner": "on",
                "app.erp_managed_express_tenant_id": TENANT,
                "app.erp_managed_express_workspace_id": str(WORKSPACE),
                "app.erp_managed_express_actor_id": OWNER,
            }.items():
                cur.execute("SELECT set_config(%s,%s,true)", (key, value))
            return True

        with (
            mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch(
                "services.erp.shared_express_live.db.get_cursor_rls", side_effect=real_cursor
            ),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
            mock.patch(
                "services.erp.shared_express_live.enable_managed_express_owner_access",
                side_effect=owner_gate,
            ),
            mock.patch("services.erp.shared_express_live.resolve", return_value=authz),
        ):
            live.record_managed_heartbeat(
                token, account_set="main", account_dir=r"C:\Pearnly\Main", agent_version="1.1.64"
            )
            result = live.confirm_managed_live_profile(
                owner, ENDPOINT, WORKSPACE, 1, True, None, None
            )
        self.assertEqual(result["generation"], 2)
        self.cur.execute(
            "SELECT bound_account_set, binding_generation FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        row = self.cur.fetchone()
        self.assertEqual((row["bound_account_set"], row["binding_generation"]), ("main", 2))
        self.cur.execute("SELECT action FROM operation_logs WHERE target_id=%s", (ENDPOINT,))
        self.assertEqual(self.cur.fetchone()["action"], "erp.endpoint.bind")

        with self.assertRaises(live.ManagedLiveError) as stale:
            with (
                mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
                mock.patch(
                    "services.erp.shared_express_live.db.get_cursor_rls", side_effect=real_cursor
                ),
                mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
                mock.patch(
                    "services.erp.shared_express_live.enable_managed_express_owner_access",
                    side_effect=owner_gate,
                ),
                mock.patch("services.erp.shared_express_live.resolve", return_value=authz),
            ):
                live.confirm_managed_live_profile(owner, ENDPOINT, WORKSPACE, 1, True, None, None)
        self.assertEqual(stale.exception.code, "erp.endpoint_stale_generation")
        with (
            mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            live.record_managed_heartbeat(
                token, account_set="main", account_dir=r"C:\Pearnly\Main", agent_version="1.1.64"
            )
        self.cur.execute(
            "INSERT INTO erp_push_logs (id,user_id,endpoint_id,status,tenant_id) VALUES (%s,%s,%s,'pending',%s)",
            (str(uuid.uuid4()), OWNER, ENDPOINT, TENANT),
        )
        self.conn.commit()
        with self.assertRaises(live.ManagedLiveError) as busy:
            with (
                mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
                mock.patch(
                    "services.erp.shared_express_live.db.get_cursor_rls", side_effect=real_cursor
                ),
                mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
                mock.patch(
                    "services.erp.shared_express_live.enable_managed_express_owner_access",
                    side_effect=owner_gate,
                ),
                mock.patch("services.erp.shared_express_live.resolve", return_value=authz),
            ):
                live.confirm_managed_live_profile(owner, ENDPOINT, WORKSPACE, 2, True, None, None)
        self.assertEqual(busy.exception.code, "erp.endpoint_busy")
        self.cur.execute("DELETE FROM erp_push_logs WHERE endpoint_id=%s", (ENDPOINT,))
        self.conn.commit()
        self._heartbeat_gate(generation=2)
        self.cur.execute(
            "UPDATE erp_endpoints SET agent_last_seen_at=NOW()+INTERVAL '10 seconds' WHERE id=%s",
            (ENDPOINT,),
        )
        self.conn.commit()
        with self.assertRaises(live.ManagedLiveError) as future:
            with (
                mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
                mock.patch(
                    "services.erp.shared_express_live.db.get_cursor_rls", side_effect=real_cursor
                ),
                mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
                mock.patch(
                    "services.erp.shared_express_live.enable_managed_express_owner_access",
                    side_effect=owner_gate,
                ),
                mock.patch("services.erp.shared_express_live.resolve", return_value=authz),
            ):
                live.confirm_managed_live_profile(owner, ENDPOINT, WORKSPACE, 2, True, None, None)
        self.assertEqual(future.exception.code, "erp.profile_stale")
        with (
            mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
            mock.patch("services.erp.shared_express_live.db.get_cursor", side_effect=real_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            live.record_managed_heartbeat(
                token, account_set="main", account_dir=r"C:\Pearnly\Main", agent_version="1.1.64"
            )
        self.cur.execute(
            "ALTER TABLE operation_logs ADD CONSTRAINT smoke_audit_failure CHECK (FALSE) NOT VALID"
        )
        self.conn.commit()
        with self.assertRaises(Exception):
            with (
                mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
                mock.patch(
                    "services.erp.shared_express_live.db.get_cursor_rls", side_effect=real_cursor
                ),
                mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
                mock.patch(
                    "services.erp.shared_express_live.enable_managed_express_owner_access",
                    side_effect=owner_gate,
                ),
                mock.patch("services.erp.shared_express_live.resolve", return_value=authz),
            ):
                live.confirm_managed_live_profile(owner, ENDPOINT, WORKSPACE, 2, True, None, None)
        self.cur.execute("ALTER TABLE operation_logs DROP CONSTRAINT smoke_audit_failure")
        self.cur.execute(
            "SELECT binding_generation, bound_account_set FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        rolled_back = self.cur.fetchone()
        self.assertEqual(
            (rolled_back["binding_generation"], rolled_back["bound_account_set"]), (2, "main")
        )
        self.conn.commit()


if __name__ == "__main__":
    unittest.main()
