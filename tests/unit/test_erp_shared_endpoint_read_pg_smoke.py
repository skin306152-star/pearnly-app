# -*- coding: utf-8 -*-
"""F1-B3A shared endpoint query against disposable PostgreSQL RLS state."""

from __future__ import annotations

import unittest
import uuid
from unittest import mock

from core import rls
from services.erp import shared_express_schema, shared_express_store
from tests.unit._pg_smoke import connect_or_skip

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
OWNER = "11111111-1111-1111-1111-111111111111"
EMPLOYEE = "22222222-2222-2222-2222-222222222222"
WORKSPACE_A = 101
WORKSPACE_B = 202


class SharedEndpointReadPgSmokeTests(unittest.TestCase):
    conn = None
    cur = None

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        try:
            rls.ensure_rls_app_role(cls.cur)
            cls.conn.commit()
            cls.cur.execute("SET search_path TO pg_temp, public")
            cls.cur.execute("""
                CREATE TEMP TABLE erp_endpoints (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    name TEXT NOT NULL,
                    adapter TEXT NOT NULL,
                    config JSONB NOT NULL DEFAULT '{}'::jsonb,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    auto_push BOOLEAN NOT NULL DEFAULT FALSE,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    last_used_at TIMESTAMPTZ,
                    last_status TEXT,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """)
            cls.cur.execute(
                "CREATE TEMP TABLE erp_push_logs ("
                "id UUID PRIMARY KEY, user_id UUID NOT NULL, tenant_id UUID, endpoint_id UUID)"
            )
            rls.apply_user_rls(cls.cur, "erp_endpoints", "erp_push_logs")
            shared_express_schema.apply_shared_express_foundation(cls.cur)
            cls.cur.execute("SELECT current_schema() AS schema")
            cls.schema = cls.cur.fetchone()["schema"]
            cls.cur.execute(f'GRANT USAGE ON SCHEMA "{cls.schema}" TO {rls.RLS_APP_ROLE}')
            cls.cur.execute(
                f'GRANT SELECT ON ALL TABLES IN SCHEMA "{cls.schema}" TO {rls.RLS_APP_ROLE}'
            )
            cls.cur.execute("ALTER TABLE erp_endpoints FORCE ROW LEVEL SECURITY")
            cls.conn.commit()
        except Exception:
            cls.conn.rollback()
            cls.cur.close()
            cls.conn.close()
            cls.cur = None
            cls.conn = None
            raise

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        cls.conn.rollback()
        cls.cur.close()
        cls.conn.close()

    def _insert(self, label, user_id, tenant_id, workspace, adapter, enabled, shared):
        endpoint_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, label))
        self.cur.execute(
            """
            INSERT INTO erp_endpoints
                (id,user_id,tenant_id,workspace_client_id,name,adapter,enabled,shared_scope)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                endpoint_id,
                user_id,
                tenant_id,
                workspace,
                label,
                adapter,
                enabled,
                shared,
            ),
        )
        return endpoint_id

    def test_query_merges_actor_legacy_with_only_current_active_shared_express(self):
        actor_legacy = self._insert("actor-legacy", EMPLOYEE, None, None, "mrerp", False, False)
        shared_current = self._insert(
            "shared-current", OWNER, TENANT_A, WORKSPACE_A, "express", True, True
        )
        self._insert("private-current", OWNER, TENANT_A, WORKSPACE_A, "express", True, False)
        self._insert("disabled-current", OWNER, TENANT_A, WORKSPACE_A, "express", False, True)
        self._insert("mrerp-current", OWNER, TENANT_A, WORKSPACE_A, "mrerp", True, True)
        self._insert("shared-other-workspace", OWNER, TENANT_A, WORKSPACE_B, "express", True, True)
        self._insert("shared-other-tenant", OWNER, TENANT_B, WORKSPACE_A, "express", True, True)
        self.conn.commit()

        self.cur.execute(f"SET LOCAL ROLE {rls.RLS_APP_ROLE}")
        self.cur.execute("SET LOCAL app.current_user_id = %s", (EMPLOYEE,))
        self.cur.execute("SET LOCAL app.current_tenant_id = %s", (TENANT_A,))
        self.cur.execute("SET LOCAL app.current_workspace_id = %s", (str(WORKSPACE_A),))
        with mock.patch.object(
            shared_express_schema,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ):
            self.assertTrue(
                shared_express_schema.enable_shared_express_select(self.cur, TENANT_A, WORKSPACE_A)
            )
        rows = shared_express_store.fetch_visible_endpoint_rows(
            self.cur,
            actor_id=EMPLOYEE,
            tenant_id=TENANT_A,
            workspace_client_id=WORKSPACE_A,
        )
        self.assertEqual({str(row["id"]) for row in rows}, {actor_legacy, shared_current})

        self.cur.execute("SET LOCAL app.current_workspace_id = %s", (str(WORKSPACE_B),))
        rows = shared_express_store.fetch_visible_endpoint_rows(
            self.cur,
            actor_id=EMPLOYEE,
            tenant_id=TENANT_A,
            workspace_client_id=WORKSPACE_A,
        )
        self.assertEqual({str(row["id"]) for row in rows}, {actor_legacy})
        self.conn.rollback()


if __name__ == "__main__":
    unittest.main()
