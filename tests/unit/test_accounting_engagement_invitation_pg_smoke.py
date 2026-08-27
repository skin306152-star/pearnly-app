# -*- coding: utf-8 -*-
"""Earn 邀请、ERP 授权与 pending 关系同事务的真 PostgreSQL 冒烟。"""

from __future__ import annotations

import contextlib
import unittest
import uuid
from unittest import mock

from services.accounting_engagement import invitations, schema
from services.accounting_engagement.errors import PRIMARY_EXISTS, EngagementError
from services.firm import schema as firm_schema
from services.firm import store as firm_store
from tests.unit._pg_smoke import connect_or_skip

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
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS display_name text;
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text NOT NULL,
    password_hash text NOT NULL
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_normalized text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id uuid;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin boolean NOT NULL DEFAULT false;
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
CREATE TABLE IF NOT EXISTS workspace_clients (
    id bigserial PRIMARY KEY,
    tenant_id uuid,
    user_id uuid NOT NULL,
    name text NOT NULL,
    is_active boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS platform_setting_allowlist (
    setting_key text NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (setting_key, user_id)
);
CREATE TABLE IF NOT EXISTS tenant_entrances (
    id bigserial PRIMARY KEY,
    tenant_id uuid NOT NULL,
    entrance text NOT NULL,
    granted_at timestamptz NOT NULL DEFAULT now(),
    granted_by text,
    UNIQUE (tenant_id, entrance)
);
"""


class AccountingEngagementInvitationPgSmokeTests(unittest.TestCase):
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
            name: str(uuid.uuid4()) for name in ("firm_a", "firm_b", "merchant", "user", "admin")
        }
        with cursor() as cur:
            cur.execute(BASE_DDL)
            cur.execute(
                "INSERT INTO tenants (id, name, tenant_type_v2) VALUES "
                "(%s, 'invite-firm-a', 'f_firm'), (%s, 'invite-firm-b', 'f_firm'), "
                "(%s, 'invite-merchant', NULL)",
                (cls.ids["firm_a"], cls.ids["firm_b"], cls.ids["merchant"]),
            )
            cur.execute(
                "INSERT INTO users (id, username, password_hash, tenant_id) "
                "VALUES (%s, %s, 'test-only', %s), (%s, %s, 'test-only', NULL)",
                (
                    cls.ids["user"],
                    f"invite-{cls.ids['user'][:8]}",
                    cls.ids["merchant"],
                    cls.ids["admin"],
                    f"admin-{cls.ids['admin'][:8]}",
                ),
            )
        cls.db_patch = mock.patch("core.db.get_cursor", cursor)
        cls.db_patch.start()
        firm_schema.ensure_firm_schema()
        with cursor() as cur:
            firm_store.create_profile(
                cur, tenant_id=cls.ids["firm_a"], display_name="Invite Firm A"
            )
            firm_store.create_profile(
                cur, tenant_id=cls.ids["firm_b"], display_name="Invite Firm B"
            )
        schema.ensure_accounting_engagement_schema()

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            with cls.cursor() as cur:
                cur.execute(
                    "DELETE FROM platform_setting_allowlist WHERE user_id = %s",
                    (cls.ids["merchant"],),
                )
                cur.execute(
                    "DELETE FROM tenant_entrances WHERE tenant_id = %s",
                    (cls.ids["merchant"],),
                )
                cur.execute(
                    "DELETE FROM accounting_engagements WHERE merchant_tenant_id = %s",
                    (cls.ids["merchant"],),
                )
                cur.execute(
                    "DELETE FROM users WHERE id = ANY(%s::uuid[])",
                    ([cls.ids["user"], cls.ids["admin"]],),
                )
                cur.execute(
                    "DELETE FROM tenants WHERE id = ANY(%s::uuid[])",
                    ([cls.ids["firm_a"], cls.ids["firm_b"], cls.ids["merchant"]],),
                )
        finally:
            cls.db_patch.stop()
            cls.conn.close()

    def setUp(self):
        with self.cursor() as cur:
            cur.execute(
                "DELETE FROM platform_setting_allowlist WHERE user_id = %s",
                (self.ids["merchant"],),
            )
            cur.execute(
                "DELETE FROM tenant_entrances WHERE tenant_id = %s",
                (self.ids["merchant"],),
            )
            cur.execute(
                "DELETE FROM accounting_engagements WHERE merchant_tenant_id = %s",
                (self.ids["merchant"],),
            )

    def identity(self):
        username = f"invite-{self.ids['user'][:8]}"
        return {
            "lookup_key": username,
            "username": username,
            "email": None,
            "email_norm": None,
        }

    def test_invite_persists_relation_allowlist_and_entry_together(self):
        with self.cursor() as cur:
            result = invitations.invite_merchant(
                cur,
                identity=self.identity(),
                firm_tenant_id=self.ids["firm_a"],
                admin_user_id=self.ids["admin"],
            )
            cur.execute(
                "SELECT status FROM accounting_engagements WHERE id = %s",
                (result["engagement"]["id"],),
            )
            self.assertEqual(cur.fetchone()["status"], "pending_merchant")
            cur.execute(
                "SELECT count(*) AS n FROM platform_setting_allowlist "
                "WHERE setting_key = 'erp_portal' AND user_id = %s",
                (self.ids["merchant"],),
            )
            self.assertEqual(cur.fetchone()["n"], 1)
            cur.execute(
                "SELECT count(*) AS n FROM platform_setting_allowlist "
                "WHERE setting_key = 'erp_cowork_engagements' AND user_id = %s",
                (self.ids["merchant"],),
            )
            self.assertEqual(cur.fetchone()["n"], 1)
            cur.execute(
                "SELECT count(*) AS n FROM tenant_entrances "
                "WHERE tenant_id = %s AND entrance = 'erp'",
                (self.ids["merchant"],),
            )
            self.assertEqual(cur.fetchone()["n"], 1)

    def test_conflicting_firm_does_not_leave_new_access_rows(self):
        with self.cursor() as cur:
            invitations.lifecycle.invite(
                cur,
                firm_tenant_id=self.ids["firm_a"],
                merchant_tenant_id=self.ids["merchant"],
                admin_user_id=self.ids["admin"],
            )

        with self.assertRaises(EngagementError) as error:
            with self.cursor() as cur:
                invitations.invite_merchant(
                    cur,
                    identity=self.identity(),
                    firm_tenant_id=self.ids["firm_b"],
                    admin_user_id=self.ids["admin"],
                )
        self.assertEqual(error.exception.code, PRIMARY_EXISTS)

        with self.cursor() as cur:
            cur.execute(
                "SELECT count(*) AS n FROM platform_setting_allowlist WHERE user_id = %s",
                (self.ids["merchant"],),
            )
            self.assertEqual(cur.fetchone()["n"], 0)
            cur.execute(
                "SELECT count(*) AS n FROM tenant_entrances WHERE tenant_id = %s",
                (self.ids["merchant"],),
            )
            self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
