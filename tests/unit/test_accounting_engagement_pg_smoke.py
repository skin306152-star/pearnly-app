# -*- coding: utf-8 -*-
"""关系唯一性、双确认与参与方 RLS 的真 PostgreSQL 冒烟。"""

from __future__ import annotations

import contextlib
import unittest
import uuid
from unittest import mock

from core.rls import ensure_rls_app_role
from services.accounting_engagement import lifecycle, schema
from services.accounting_engagement.errors import WORKSPACE_MISMATCH, EngagementError
from services.firm import schema as firm_schema
from tests.unit._pg_smoke import connect, connect_or_skip

BASE_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    display_name text,
    tenant_type text NOT NULL DEFAULT 'shared_api',
    status text NOT NULL DEFAULT 'active',
    tenant_type_v2 text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS tenant_modules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    module_key text NOT NULL,
    enabled boolean NOT NULL DEFAULT false,
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, module_key)
);
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text
);
CREATE TABLE IF NOT EXISTS workspace_clients (
    id bigserial PRIMARY KEY,
    tenant_id uuid,
    user_id uuid NOT NULL,
    name text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
"""


class AccountingEngagementPgSmokeTests(unittest.TestCase):
    conn = None

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        @contextlib.contextmanager
        def cursor(*_args, **_kwargs):
            cur = cls.conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cur
                cls.conn.commit()
            except Exception:
                cls.conn.rollback()
                raise
            finally:
                cur.close()

        cls.cursor = cursor
        cls.ids = {
            name: str(uuid.uuid4())
            for name in ("firm", "firm_peer", "merchant", "outsider", "user", "admin")
        }
        with cursor() as cur:
            cur.execute(BASE_DDL)
        cls.patch = mock.patch("core.db.get_cursor", cursor)
        cls.patch.start()
        firm_schema.ensure_firm_schema()
        with cursor() as cur:
            for name in ("firm", "firm_peer", "merchant", "outsider"):
                layer = "f_firm" if name.startswith("firm") else "s_micro"
                cur.execute(
                    "INSERT INTO tenants (id, name, display_name, tenant_type_v2) "
                    "VALUES (%s, %s, %s, %s)",
                    (cls.ids[name], f"eng-{name}", f"Eng {name}", layer),
                )
            cur.execute(
                "INSERT INTO users (id, username, password_hash) "
                "VALUES (%s, 'eng-user', 'test-only'), (%s, 'eng-admin', 'test-only')",
                (cls.ids["user"], cls.ids["admin"]),
            )
        firm_schema.ensure_firm_schema()
        schema.ensure_accounting_engagement_schema()
        schema.ensure_accounting_engagement_schema()
        with cursor() as cur:
            for name in ("firm", "merchant", "outsider"):
                cur.execute(
                    "INSERT INTO workspace_clients (tenant_id, user_id, name) "
                    "VALUES (%s, %s, %s) RETURNING id",
                    (cls.ids[name], cls.ids["user"], f"ws-{name}"),
                )
                cls.ids[f"ws_{name}"] = cur.fetchone()["id"]
            ensure_rls_app_role(cur)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            with cls.cursor() as cur:
                cur.execute(
                    "DELETE FROM accounting_engagements "
                    "WHERE firm_tenant_id = ANY(%s::uuid[]) OR merchant_tenant_id = ANY(%s::uuid[])",
                    (
                        [cls.ids["firm"], cls.ids["firm_peer"]],
                        [cls.ids["merchant"], cls.ids["outsider"]],
                    ),
                )
                cur.execute(
                    "DELETE FROM workspace_clients WHERE id = ANY(%s::bigint[])",
                    ([cls.ids["ws_firm"], cls.ids["ws_merchant"], cls.ids["ws_outsider"]],),
                )
                cur.execute(
                    "DELETE FROM users WHERE id = ANY(%s::uuid[])",
                    ([cls.ids["user"], cls.ids["admin"]],),
                )
                cur.execute(
                    "DELETE FROM tenants WHERE id = ANY(%s::uuid[])",
                    (
                        [
                            cls.ids["firm"],
                            cls.ids["firm_peer"],
                            cls.ids["merchant"],
                            cls.ids["outsider"],
                        ],
                    ),
                )
        finally:
            cls.patch.stop()
            cls.conn.close()

    def setUp(self):
        with self.cursor() as cur:
            cur.execute(
                "DELETE FROM accounting_engagements " "WHERE merchant_tenant_id = ANY(%s::uuid[])",
                ([self.ids["merchant"], self.ids["outsider"]],),
            )

    def test_invite_confirmation_and_same_firm_retry_are_idempotent(self):
        with self.cursor() as cur:
            invited = lifecycle.invite(
                cur,
                firm_tenant_id=self.ids["firm"],
                merchant_tenant_id=self.ids["merchant"],
                admin_user_id=self.ids["admin"],
            )
            repeated = lifecycle.invite(
                cur,
                firm_tenant_id=self.ids["firm"],
                merchant_tenant_id=self.ids["merchant"],
                admin_user_id=self.ids["admin"],
            )
            self.assertEqual(repeated["id"], invited["id"])
            merchant = lifecycle.accept_merchant(
                cur,
                engagement_id=invited["id"],
                merchant_tenant_id=self.ids["merchant"],
                workspace_client_id=self.ids["ws_merchant"],
            )
            active = lifecycle.accept_firm(
                cur,
                engagement_id=invited["id"],
                firm_tenant_id=self.ids["firm"],
                workspace_client_id=self.ids["ws_firm"],
            )
        self.assertEqual(merchant["status"], "pending_firm")
        self.assertEqual(active["status"], "active")
        self.assertIsNotNone(active["active_from"])

    def test_wrong_tenant_workspace_is_rejected(self):
        with self.cursor() as cur:
            invited = lifecycle.invite(
                cur,
                firm_tenant_id=self.ids["firm_peer"],
                merchant_tenant_id=self.ids["outsider"],
                admin_user_id=self.ids["admin"],
            )
            with self.assertRaises(EngagementError) as error:
                lifecycle.accept_merchant(
                    cur,
                    engagement_id=invited["id"],
                    merchant_tenant_id=self.ids["outsider"],
                    workspace_client_id=self.ids["ws_merchant"],
                )
        self.assertEqual(error.exception.code, WORKSPACE_MISMATCH)

    def test_firm_and_merchant_can_read_but_outsider_cannot(self):
        from psycopg2.extras import RealDictCursor

        with self.cursor() as cur:
            invited = lifecycle.invite(
                cur,
                firm_tenant_id=self.ids["firm"],
                merchant_tenant_id=self.ids["merchant"],
                admin_user_id=self.ids["admin"],
            )
            lifecycle.accept_merchant(
                cur,
                engagement_id=invited["id"],
                merchant_tenant_id=self.ids["merchant"],
                workspace_client_id=self.ids["ws_merchant"],
            )
            lifecycle.accept_firm(
                cur,
                engagement_id=invited["id"],
                firm_tenant_id=self.ids["firm"],
                workspace_client_id=self.ids["ws_firm"],
            )

        for tenant_name, expected in (("firm", 1), ("merchant", 1), ("outsider", 0)):
            conn = connect()
            try:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SET LOCAL ROLE pearnly_app")
                cur.execute("SET LOCAL app.current_tenant_id = %s", (self.ids[tenant_name],))
                cur.execute(
                    "SELECT count(*) AS n FROM accounting_engagements "
                    "WHERE merchant_tenant_id = %s",
                    (self.ids["merchant"],),
                )
                self.assertEqual(cur.fetchone()["n"], expected)
            finally:
                conn.rollback()
                conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
