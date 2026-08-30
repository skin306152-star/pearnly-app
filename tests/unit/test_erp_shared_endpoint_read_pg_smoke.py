"""True PostgreSQL RLS smoke for the F1-B3A shared endpoint read."""

from __future__ import annotations

import uuid
import unittest
from unittest import mock

from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp import shared_express_managed_schema as managed_schema
from services.erp import shared_express_schema, shared_express_store
from tests.unit._pg_smoke import (
    assert_public_routines_unchanged,
    connect_or_skip,
    require_disposable_db,
    snapshot_public_routines,
)

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OWNER = "11111111-1111-1111-1111-111111111111"
EMPLOYEE = "22222222-2222-2222-2222-222222222222"
OWNER_ROLE = "aaaaaaaa-0000-0000-0000-000000000001"
EMPLOYEE_ROLE = "aaaaaaaa-0000-0000-0000-000000000002"
WORKSPACE_A = 101
WORKSPACE_B = 202


def _schema_ddl(statement: str, schema: str) -> str:
    localized = statement.replace("public.erp_endpoints", f'"{schema}".erp_endpoints').replace(
        "public.users", f'"{schema}".users'
    )
    for name in (
        "preserve_managed_erp_endpoints_on_user_delete",
        "prevent_managed_erp_endpoint_creator_change",
        "purge_managed_erp_endpoints_for_users",
    ):
        localized = localized.replace(f"public.{name}", f'"{schema}".{name}')
    return localized


class SharedEndpointReadPgSmokeTests(unittest.TestCase):
    conn = None
    cur = None
    schema = None
    _previous_ready = None
    _schema_prefix = "smoke_shared_read_"

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        import psycopg2

        cls.cur = cls.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cls.schema = cls._schema_prefix + uuid.uuid4().hex[:12]
        cls._previous_ready = managed_schema._MANAGED_FOUNDATION_READY
        c = cls.cur
        cls._public_routines_before = snapshot_public_routines(c)
        c.execute(f'CREATE SCHEMA "{cls.schema}"')
        c.execute(f'SET search_path TO "{cls.schema}", public')
        c.execute("""
            CREATE TABLE tenants (id UUID PRIMARY KEY);
            CREATE TABLE users (id UUID PRIMARY KEY, tenant_id UUID NOT NULL REFERENCES tenants(id), role TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE);
            CREATE TABLE roles (id UUID PRIMARY KEY, key TEXT NOT NULL, name TEXT NOT NULL, permissions JSONB NOT NULL DEFAULT '{}'::jsonb, tenant_id UUID, is_active BOOLEAN NOT NULL DEFAULT TRUE);
            CREATE TABLE memberships (id UUID PRIMARY KEY, user_id UUID REFERENCES users(id), tenant_id UUID REFERENCES tenants(id), role_id UUID REFERENCES roles(id), status TEXT NOT NULL, scope_mode TEXT NOT NULL DEFAULT 'all');
            CREATE TABLE workspace_clients (id BIGINT PRIMARY KEY, tenant_id UUID REFERENCES tenants(id), is_active BOOLEAN NOT NULL DEFAULT TRUE, erp_endpoint_id UUID, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
            CREATE TABLE erp_endpoints (
                id UUID PRIMARY KEY, user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE, workspace_client_id BIGINT,
                name TEXT NOT NULL, adapter TEXT NOT NULL, config JSONB NOT NULL DEFAULT '{}'::jsonb,
                is_default BOOLEAN NOT NULL DEFAULT FALSE, auto_push BOOLEAN NOT NULL DEFAULT FALSE,
                enabled BOOLEAN NOT NULL DEFAULT TRUE, last_used_at TIMESTAMPTZ, last_status TEXT,
                success_count INTEGER NOT NULL DEFAULT 0, failure_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                shared_scope BOOLEAN NOT NULL DEFAULT FALSE, bound_account_set TEXT, bound_profile_key TEXT,
                live_account_set TEXT, live_profile_key TEXT, agent_last_seen_at TIMESTAMPTZ, agent_version TEXT,
                binding_generation BIGINT NOT NULL DEFAULT 0
            );
            """)
        ensure_rls_app_role(c)
        c.execute(f'GRANT USAGE ON SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}')
        c.execute(
            f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}'
        )
        for statement in managed_schema.SHARED_EXPRESS_MANAGED_DDL:
            c.execute(_schema_ddl(statement, cls.schema))
        c.execute(f'ALTER TABLE "{cls.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        assert_public_routines_unchanged(c, cls._public_routines_before)
        cls.conn.commit()
        managed_schema._MANAGED_FOUNDATION_READY = True

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            try:
                managed_schema._MANAGED_FOUNDATION_READY = cls._previous_ready
                cls.conn.rollback()
                cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
                require_disposable_db(cls.cur, cls.schema, cls._schema_prefix)
                cls.cur.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')
                cls.conn.commit()
                assert_public_routines_unchanged(cls.cur, cls._public_routines_before)
            finally:
                cls.cur.close()
                cls.conn.close()

    def setUp(self):
        c = self.cur
        self.conn.rollback()
        c.execute(f'SET search_path TO "{self.schema}", public')
        require_disposable_db(c, self.schema, self._schema_prefix)
        c.execute("RESET ROLE")
        c.execute(f'ALTER TABLE "{self.schema}".erp_endpoints DISABLE ROW LEVEL SECURITY')
        c.execute(
            "TRUNCATE erp_endpoints, memberships, roles, users, workspace_clients, tenants CASCADE"
        )
        c.execute("INSERT INTO tenants VALUES (%s)", (TENANT_A,))
        c.execute(
            "INSERT INTO users (id,tenant_id,role) VALUES (%s,%s,'owner'),(%s,%s,'member')",
            (OWNER, TENANT_A, EMPLOYEE, TENANT_A),
        )
        c.execute(
            "INSERT INTO roles (id,key,name,permissions) VALUES (%s,'owner','owner','{\"all\":true}'),(%s,'member','member','[\"erp.endpoint.view\"]')",
            (OWNER_ROLE, EMPLOYEE_ROLE),
        )
        c.execute(
            "INSERT INTO memberships (id,user_id,tenant_id,role_id,status) VALUES (%s,%s,%s,%s,'active'),(%s,%s,%s,%s,'active')",
            (
                str(uuid.uuid4()),
                OWNER,
                TENANT_A,
                OWNER_ROLE,
                str(uuid.uuid4()),
                EMPLOYEE,
                TENANT_A,
                EMPLOYEE_ROLE,
            ),
        )
        c.execute(
            "INSERT INTO workspace_clients (id,tenant_id,is_active) VALUES (%s,%s,TRUE),(%s,%s,TRUE)",
            (WORKSPACE_A, TENANT_A, WORKSPACE_B, TENANT_A),
        )
        c.execute(
            "INSERT INTO erp_endpoints (id,user_id,name,adapter,config,enabled,shared_scope,binding_generation,tenant_id,workspace_client_id) VALUES "
            "(%s,%s,'legacy','express','{\"agent_token_hash\":\"legacy-secret\"}',TRUE,FALSE,0,NULL,NULL),"
            '(%s,%s,\'managed\',\'express\',\'{"agent_token_hash":"managed-secret","account_set":"Main"}\',TRUE,TRUE,1,%s,%s),'
            "(%s,%s,'mrerp','mrerp','{}',TRUE,FALSE,0,NULL,NULL)",
            (
                str(uuid.uuid4()),
                EMPLOYEE,
                str(uuid.uuid4()),
                OWNER,
                TENANT_A,
                WORKSPACE_A,
                str(uuid.uuid4()),
                OWNER,
            ),
        )
        c.execute(f'ALTER TABLE "{self.schema}".erp_endpoints ENABLE ROW LEVEL SECURITY')
        c.execute(f'ALTER TABLE "{self.schema}".erp_endpoints FORCE ROW LEVEL SECURITY')
        self.conn.commit()

    def _app_context(self, actor=EMPLOYEE, workspace=WORKSPACE_A):
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        self.cur.execute(
            "SELECT set_config('app.current_user_id',%s,true), set_config('app.current_tenant_id',%s,true), set_config('app.current_workspace_id',%s,true)",
            (actor, TENANT_A, str(workspace)),
        )

    def test_managed_generation_one_is_visible_only_in_current_active_workspace_and_legacy_is_gen0(
        self,
    ):
        self._app_context()
        with mock.patch.object(
            shared_express_schema, "erp_shared_express_endpoint_enabled_for", return_value=True
        ):
            self.assertTrue(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        rows = shared_express_store.fetch_visible_endpoint_rows(
            self.cur, actor_id=EMPLOYEE, tenant_id=TENANT_A, workspace_client_id=WORKSPACE_A
        )
        self.assertEqual(len(rows), 2)
        managed = next(row for row in rows if row["name"] == "managed")
        self.cur.execute(
            "SELECT binding_generation FROM erp_endpoints WHERE id=%s", (managed["id"],)
        )
        self.assertEqual(self.cur.fetchone()["binding_generation"], 1)
        safe = shared_express_store.safe_endpoint_dto(
            managed, __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        )
        self.assertNotIn("config", safe)
        self.assertNotIn("managed-secret", str(safe))
        self.cur.execute("SET LOCAL app.erp_shared_express_workspace_id = '202'")
        rows = shared_express_store.fetch_visible_endpoint_rows(
            self.cur, actor_id=EMPLOYEE, tenant_id=TENANT_A, workspace_client_id=WORKSPACE_A
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "legacy")
        self.conn.rollback()


if __name__ == "__main__":
    unittest.main()
