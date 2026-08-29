# -*- coding: utf-8 -*-
"""Real PostgreSQL serialization proofs for custom-role invitation and assignment."""

from __future__ import annotations

import concurrent.futures
import contextlib
import json
import threading
import unittest
import uuid
from unittest import mock

from services.authz import roles_store
from services.authz.registry import ROLE_PERMISSIONS
from services.team import invitations
from tests.unit._pg_smoke import connect, connect_or_skip

SCHEMA = "_pearnly_pg_smoke_b2a_role_concurrency"
SENTINEL = "_pearnly_disposable_test_db"

DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY,
    name text NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    email text,
    plan text,
    is_active boolean NOT NULL DEFAULT true,
    is_super_admin boolean NOT NULL DEFAULT false,
    tenant_id uuid,
    role text,
    invited_by uuid,
    company_name text
);
CREATE TABLE IF NOT EXISTS roles (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    permissions jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_system boolean NOT NULL DEFAULT false,
    tenant_id uuid,
    key text,
    display_name text,
    is_active boolean NOT NULL DEFAULT true,
    version integer NOT NULL DEFAULT 0,
    created_by uuid
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_system_key
    ON roles(key) WHERE tenant_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_tenant_key
    ON roles(tenant_id, key) WHERE tenant_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS memberships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role_id uuid NOT NULL REFERENCES roles(id),
    status text NOT NULL DEFAULT 'active',
    scope_mode text NOT NULL DEFAULT 'all',
    granted_by uuid,
    granted_at timestamptz
);
CREATE TABLE IF NOT EXISTS invitations (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    email text,
    line_target text,
    role_key text NOT NULL,
    scope_mode text NOT NULL DEFAULT 'all',
    workspace_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    token_hash text NOT NULL UNIQUE,
    invited_by uuid NOT NULL,
    expires_at timestamptz NOT NULL,
    accepted_at timestamptz,
    accepted_user_id uuid,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE memberships ALTER COLUMN id SET DEFAULT gen_random_uuid();
"""


class _HookedCursor:
    def __init__(self, raw, hook):
        self._raw = raw
        self._hook = hook

    def execute(self, sql, params=None):
        compact = " ".join(sql.split())
        self._hook("before", compact)
        result = self._raw.execute(sql, params)
        self._hook("after", compact)
        return result

    def __getattr__(self, name):
        return getattr(self._raw, name)


class TeamRoleConcurrencyPgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        probe = connect_or_skip()
        probe.close()
        from psycopg2.extras import RealDictCursor

        cls.cursor_factory = RealDictCursor
        with cls._connect(autocommit=True) as conn:
            with conn.cursor(cursor_factory=cls.cursor_factory) as cur:
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = %s) AS found",
                    (SCHEMA,),
                )
                exists = bool(cur.fetchone()["found"])
                if not exists:
                    cur.execute(f'CREATE SCHEMA "{SCHEMA}"')
                    cur.execute(f'CREATE TABLE "{SCHEMA}"."{SENTINEL}" (note text NOT NULL)')
                    cur.execute(
                        f'INSERT INTO "{SCHEMA}"."{SENTINEL}" VALUES (%s)',
                        ("owned by test_team_role_concurrency_pg_smoke",),
                    )
                cls._require_disposable_schema(cur)
                cur.execute(f'SET search_path TO "{SCHEMA}"')
                cur.execute(DDL)

    @classmethod
    def _connect(cls, autocommit=False):
        conn = connect()
        conn.autocommit = autocommit
        return conn

    @classmethod
    def _require_disposable_schema(cls, cur):
        cur.execute("SELECT to_regclass(%s) AS marker", (f'{SCHEMA}."{SENTINEL}"',))
        if cur.fetchone()["marker"] is None:
            raise RuntimeError(f"refusing destructive cleanup without {SCHEMA}.{SENTINEL}")

    def setUp(self):
        self.tenant_id = str(uuid.uuid4())
        self.owner_id = str(uuid.uuid4())
        self.owner_role_id = str(uuid.uuid4())
        self.viewer_role_id = str(uuid.uuid4())
        self.custom_role_id = str(uuid.uuid4())
        self.operation = threading.local()
        self.hook = lambda _phase, _sql: None
        self.service_pids = []
        self.pid_lock = threading.Lock()
        with self._connect(autocommit=True) as conn:
            with conn.cursor(cursor_factory=self.cursor_factory) as cur:
                self._require_disposable_schema(cur)
                cur.execute(f'SET search_path TO "{SCHEMA}"')
                cur.execute("DELETE FROM invitations")
                cur.execute("DELETE FROM memberships")
                cur.execute("DELETE FROM users")
                cur.execute("DELETE FROM roles")
                cur.execute("DELETE FROM tenants")
                cur.execute(
                    "INSERT INTO tenants (id, name) VALUES (%s, 'Tenant A')", (self.tenant_id,)
                )
                cur.execute(
                    "INSERT INTO roles (id,name,key,permissions,is_system,tenant_id) "
                    "VALUES (%s,'owner','owner',%s::jsonb,TRUE,NULL),"
                    "(%s,'viewer','viewer',%s::jsonb,TRUE,NULL),"
                    "(%s,%s,'custom:buyer',%s::jsonb,FALSE,%s)",
                    (
                        self.owner_role_id,
                        json.dumps({"all": True}),
                        self.viewer_role_id,
                        json.dumps(sorted(ROLE_PERMISSIONS["viewer"])),
                        self.custom_role_id,
                        f"custom:{self.tenant_id}:buyer",
                        json.dumps(["purchase.doc.create"]),
                        self.tenant_id,
                    ),
                )
                cur.execute(
                    "INSERT INTO users "
                    "(id,username,password_hash,tenant_id,role,invited_by) "
                    "VALUES (%s,'owner@test','hash',%s,'owner',NULL)",
                    (self.owner_id, self.tenant_id),
                )
                cur.execute(
                    "INSERT INTO memberships "
                    "(id,user_id,tenant_id,role_id,status,scope_mode) "
                    "VALUES (%s,%s,%s,%s,'active','all')",
                    (str(uuid.uuid4()), self.owner_id, self.tenant_id, self.owner_role_id),
                )

    @contextlib.contextmanager
    def _service_cursor(self, commit=False, **_kwargs):
        conn = self._connect()
        raw = conn.cursor(cursor_factory=self.cursor_factory)
        try:
            raw.execute(f'SET search_path TO "{SCHEMA}"')
            raw.execute("SET LOCAL lock_timeout = '3s'")
            raw.execute("SET LOCAL statement_timeout = '6s'")
            raw.execute("SELECT pg_backend_pid() AS pid")
            with self.pid_lock:
                self.service_pids.append(int(raw.fetchone()["pid"]))
            yield _HookedCursor(raw, self.hook)
            conn.commit() if commit else conn.rollback()
        except Exception:
            conn.rollback()
            raise
        finally:
            raw.close()
            conn.close()

    def _run_as(self, operation, callback):
        self.operation.name = operation
        return callback()

    def _race_after_role_share(self, first_operation, first_callback, second_callback):
        role_locked = threading.Event()
        second_attempted = threading.Event()
        release = threading.Event()

        def hook(phase, sql):
            operation = getattr(self.operation, "name", None)
            shared_role = (
                "FROM roles WHERE tenant_id = %s AND key = %s" in sql and "FOR SHARE" in sql
            )
            deleting_role = "FROM roles r" in sql and "FOR UPDATE" in sql
            if operation == first_operation and phase == "after" and shared_role:
                role_locked.set()
                if not release.wait(timeout=3):
                    raise TimeoutError("concurrency peer did not reach the role lock")
            if operation == "delete" and phase == "before" and deleting_role:
                second_attempted.set()

        self.hook = hook
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(self._run_as, first_operation, first_callback)
                self.assertTrue(role_locked.wait(timeout=2), "first operation never locked role")
                second = pool.submit(self._run_as, "delete", second_callback)
                self.assertTrue(
                    second_attempted.wait(timeout=2), "delete never attempted role lock"
                )
                release.set()
                return first.result(timeout=6), second.result(timeout=6)
        finally:
            release.set()

    def _delete_custom_role(self):
        return roles_store.delete_custom_role(tenant_id=self.tenant_id, role_id=self.custom_role_id)

    def test_accept_custom_invite_and_role_delete_serialize_without_fk_failure(self):
        token = "pg-smoke-accept-delete"
        invitation_id = str(uuid.uuid4())
        with self._connect(autocommit=True) as conn:
            with conn.cursor(cursor_factory=self.cursor_factory) as cur:
                cur.execute(f'SET search_path TO "{SCHEMA}"')
                cur.execute(
                    "INSERT INTO invitations "
                    "(id,tenant_id,role_key,scope_mode,workspace_ids,token_hash,invited_by,expires_at) "
                    "VALUES (%s,%s,'custom:buyer','all','[]'::jsonb,%s,%s,NOW()+INTERVAL '1 day')",
                    (invitation_id, self.tenant_id, invitations.hash_token(token), self.owner_id),
                )

        with (
            mock.patch.object(invitations.db, "get_cursor", side_effect=self._service_cursor),
            mock.patch.object(
                invitations, "erp_shared_express_endpoint_enabled_for", return_value=True
            ),
            mock.patch.object(invitations.bcrypt, "gensalt", return_value=b"salt"),
            mock.patch.object(invitations.bcrypt, "hashpw", return_value=b"hashed"),
        ):
            accepted, deleted = self._race_after_role_share(
                "accept",
                lambda: invitations.accept(token, username="new-user", password="Zz12345678"),
                self._delete_custom_role,
            )

        self.assertTrue(accepted["ok"])
        self.assertEqual(deleted, {"error": "team.role_in_use", "member_count": 1})
        self.assertGreaterEqual(len(set(self.service_pids)), 2)

    def test_assign_custom_role_and_role_delete_serialize_without_fk_failure(self):
        target_id = str(uuid.uuid4())
        with self._connect(autocommit=True) as conn:
            with conn.cursor(cursor_factory=self.cursor_factory) as cur:
                cur.execute(f'SET search_path TO "{SCHEMA}"')
                cur.execute(
                    "INSERT INTO users "
                    "(id,username,password_hash,tenant_id,role,invited_by) "
                    "VALUES (%s,'staff@test','hash',%s,'member',%s)",
                    (target_id, self.tenant_id, self.owner_id),
                )
                cur.execute(
                    "INSERT INTO memberships "
                    "(id,user_id,tenant_id,role_id,status,scope_mode) "
                    "VALUES (%s,%s,%s,%s,'active','all')",
                    (str(uuid.uuid4()), target_id, self.tenant_id, self.viewer_role_id),
                )

        with mock.patch.object(invitations.db, "get_cursor", side_effect=self._service_cursor):
            assigned, deleted = self._race_after_role_share(
                "assign",
                lambda: roles_store.assign_role(
                    tenant_id=self.tenant_id,
                    actor_id=self.owner_id,
                    target_user_id=target_id,
                    role_key="custom:buyer",
                ),
                self._delete_custom_role,
            )

        self.assertTrue(assigned["ok"])
        self.assertEqual(assigned["role_from"], "viewer")
        self.assertEqual(deleted, {"error": "team.role_in_use", "member_count": 1})
        self.assertGreaterEqual(len(set(self.service_pids)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
