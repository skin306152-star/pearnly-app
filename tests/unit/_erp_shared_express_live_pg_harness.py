"""Shared disposable PostgreSQL harness for managed Express live-profile tests."""

from __future__ import annotations

import hashlib
import os
import unittest
import uuid
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

import psycopg2
from psycopg2.extras import RealDictCursor

from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp import shared_express_lifecycle_schema as lifecycle
from services.erp.shared_express_live import (
    confirm_managed_live_profile,
    record_managed_heartbeat,
)
from services.erp.shared_express_live_ddl import LIVE_DDL
from services.erp.shared_express_managed_schema import SHARED_EXPRESS_MANAGED_RLS_DDL
from tests.unit._pg_smoke import LOCAL_DSN, connect_or_skip, require_disposable_db
from tests.unit.test_erp_shared_express_live_pg_smoke import _localize

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_TENANT = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
OWNER = "11111111-1111-1111-1111-111111111111"
CLERK = "11111111-1111-1111-1111-222222222222"
OWNER_ROLE = "22222222-2222-2222-2222-222222222222"
CLERK_ROLE = "22222222-2222-2222-2222-333333333333"
ENDPOINT = "33333333-3333-4333-8333-333333333333"
WORKSPACE = 101
TARGET_WORKSPACE = 202
FOREIGN_WORKSPACE = 303
TOKEN = f"exp_{ENDPOINT}_secret"


class ManagedLivePgHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema = f"smoke_live_matrix_{uuid.uuid4().hex[:10]}"
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
        cls.cur.execute("""
            CREATE TABLE tenants (id uuid primary key, status text not null);
            CREATE TABLE users (id uuid primary key, tenant_id uuid, is_active boolean not null);
            CREATE TABLE roles (id uuid primary key, name text not null);
            CREATE TABLE memberships (id uuid primary key, user_id uuid, tenant_id uuid, role_id uuid, status text not null);
            CREATE TABLE workspace_clients (id bigint primary key, tenant_id uuid not null, is_active boolean not null, erp_endpoint_id uuid);
            CREATE TABLE erp_push_logs (id uuid primary key, user_id uuid, endpoint_id uuid, status text,
                next_retry_at timestamptz, lease_owner text, lease_expires_at timestamptz, tenant_id uuid);
            CREATE TABLE operation_logs (id bigserial primary key, tenant_id uuid, actor_user_id uuid,
                actor_username text, actor_is_super boolean not null default false, action text,
                target_type text, target_id text, target_name text, details jsonb, ip inet, ua text);
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
        ddl = lifecycle.SHARED_EXPRESS_LIFECYCLE_DDL + SHARED_EXPRESS_MANAGED_RLS_DDL + LIVE_DDL
        for statement in ddl:
            cls.cur.execute(_localize(statement, cls.schema))
        cls.cur.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints ENABLE ROW LEVEL SECURITY')
        cls.cur.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, "smoke_live_matrix_")
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.conn.commit()
        finally:
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        self.conn.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "TRUNCATE operation_logs, erp_push_logs, erp_endpoints, workspace_clients, memberships, roles, users, tenants CASCADE"
        )
        self.cur.execute(
            "INSERT INTO tenants VALUES (%s,'active'),(%s,'active')", (TENANT, OTHER_TENANT)
        )
        self.cur.execute(
            "INSERT INTO users VALUES (%s,%s,TRUE),(%s,%s,TRUE)", (OWNER, TENANT, CLERK, TENANT)
        )
        self.cur.execute(
            "INSERT INTO roles VALUES (%s,'owner'),(%s,'clerk')", (OWNER_ROLE, CLERK_ROLE)
        )
        self.cur.execute(
            "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active')",
            (
                str(uuid.uuid4()),
                OWNER,
                TENANT,
                OWNER_ROLE,
                str(uuid.uuid4()),
                CLERK,
                TENANT,
                CLERK_ROLE,
            ),
        )
        self.cur.execute(
            "INSERT INTO workspace_clients VALUES (%s,%s,TRUE,NULL),(%s,%s,TRUE,NULL),(%s,%s,TRUE,NULL)",
            (WORKSPACE, TENANT, TARGET_WORKSPACE, TENANT, FOREIGN_WORKSPACE, OTHER_TENANT),
        )
        self._insert_endpoint()

    def tearDown(self):
        self.conn.rollback()

    def _insert_endpoint(self, **overrides):
        values = {
            "user_id": OWNER,
            "adapter": "express",
            "enabled": True,
            "shared_scope": True,
            "tenant_id": TENANT,
            "workspace_id": WORKSPACE,
            "generation": 1,
            "bound_set": None,
            "bound_key": None,
            "live_set": None,
            "live_key": None,
            "seen": None,
            "version": None,
            "revoked_at": None,
            "revoked_by": None,
        }
        values.update(overrides)
        self.cur.execute("DELETE FROM erp_endpoints WHERE id=%s", (ENDPOINT,))
        token_hash = hashlib.sha256(TOKEN.encode()).hexdigest()
        self.cur.execute(
            """INSERT INTO erp_endpoints
               (id,user_id,name,adapter,config,enabled,shared_scope,tenant_id,workspace_client_id,
                binding_generation,bound_account_set,bound_profile_key,live_account_set,live_profile_key,
                agent_last_seen_at,agent_version,revoked_at,revoked_by)
               VALUES (%s,%s,'managed',%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                ENDPOINT,
                values["user_id"],
                values["adapter"],
                '{"agent_token_hash":"%s"}' % token_hash,
                values["enabled"],
                values["shared_scope"],
                values["tenant_id"],
                values["workspace_id"],
                values["generation"],
                values["bound_set"],
                values["bound_key"],
                values["live_set"],
                values["live_key"],
                values["seen"],
                values["version"],
                values["revoked_at"],
                values["revoked_by"],
            ),
        )
        self.conn.commit()

    @contextmanager
    def _service_cursor(self, commit=False, **context):
        connection = psycopg2.connect(LOCAL_DSN, connect_timeout=3)
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
            if context:
                cursor.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
                for key, value in (
                    ("app.current_tenant_id", context.get("tenant_id")),
                    ("app.current_workspace_id", context.get("workspace_client_id")),
                    ("app.current_user_id", context.get("user_id")),
                ):
                    if value is not None:
                        cursor.execute("SELECT set_config(%s,%s,true)", (key, str(value)))
            yield LocalizedCursor()
            if commit:
                connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _record(self, body=None, token=TOKEN):
        body = body or {}
        with (
            mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
            mock.patch(
                "services.erp.shared_express_live.db.get_cursor", side_effect=self._service_cursor
            ),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            return record_managed_heartbeat(
                token,
                account_set=body.get("account_set"),
                account_dir=body.get("account_dir"),
                agent_version=body.get("companion_version"),
                offline=body.get("offline") is True,
            )

    @staticmethod
    def _owner_gate(cur, **values):
        for key, value in (
            ("app.erp_managed_express_owner", "on"),
            ("app.erp_managed_express_tenant_id", values["tenant_id"]),
            ("app.erp_managed_express_workspace_id", values["workspace_client_id"]),
            ("app.erp_managed_express_actor_id", values["actor_user_id"]),
        ):
            cur.execute("SELECT set_config(%s,%s,true)", (key, str(value)))
        return True

    def _confirm(self, generation=1, workspace=WORKSPACE, user=None, authz=None):
        user = user or {"id": OWNER, "tenant_id": TENANT, "username": "owner"}
        authz = authz or SimpleNamespace(
            membership_id="membership", role_key="owner", has=lambda code: True
        )
        with (
            mock.patch.dict(os.environ, {"RLS_ROLE": RLS_APP_ROLE}),
            mock.patch(
                "services.erp.shared_express_live.db.get_cursor_rls",
                side_effect=self._service_cursor,
            ),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
            mock.patch(
                "services.erp.shared_express_live.enable_managed_express_owner_access",
                side_effect=self._owner_gate,
            ),
            mock.patch("services.erp.shared_express_live.resolve", return_value=authz),
        ):
            return confirm_managed_live_profile(
                user, ENDPOINT, workspace, generation, True, None, "matrix"
            )
