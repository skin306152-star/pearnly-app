# -*- coding: utf-8 -*-
"""Cowork 注册事务所身份与失败回滚的真 PostgreSQL 冒烟。"""

from __future__ import annotations

import contextlib
import unittest
import uuid
from unittest import mock

from services.auth.signup_core import _ensure_tenant_for_new_user
from services.firm import schema as firm_schema
from services.firm import store as firm_store
from services.modules import store as module_store
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
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS owner_user_id uuid;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS monthly_quota integer NOT NULL DEFAULT 0;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS used_this_month integer NOT NULL DEFAULT 0;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS member_count integer NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text NOT NULL,
    password_hash text NOT NULL
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id uuid;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role text;
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
"""


class CoworkSignupPgSmokeTests(unittest.TestCase):
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
        with cursor() as cur:
            cur.execute(BASE_DDL)
        cls.db_patch = mock.patch("core.db.get_cursor", cursor)
        cls.db_patch.start()
        firm_schema.ensure_firm_schema()

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        cls.db_patch.stop()
        cls.conn.close()

    def setUp(self):
        self.user_id = str(uuid.uuid4())
        self.name = f"cowork-signup-{self.user_id[:8]}"
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, 'test-only')",
                (self.user_id, f"{self.user_id[:8]}@example.test"),
            )

    def tearDown(self):
        with self.cursor() as cur:
            cur.execute("SELECT tenant_id::text FROM users WHERE id = %s", (self.user_id,))
            row = cur.fetchone()
            tenant_id = row["tenant_id"] if row else None
            if tenant_id:
                cur.execute("DELETE FROM tenant_modules WHERE tenant_id = %s", (tenant_id,))
                cur.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))

    def provision(self, entry: str):
        with (
            mock.patch("services.authz.resolver.create_membership", return_value=True),
            mock.patch("services.auth.entrance_store.grant_entrance_safe"),
            self.cursor() as cur,
        ):
            return _ensure_tenant_for_new_user(
                cur,
                self.user_id,
                "credits",
                company_name=self.name,
                username=f"{self.user_id[:8]}@example.test",
                entry=entry,
            )

    def test_cowork_creates_firm_profile_and_firm_preset_atomically(self):
        tenant_id = self.provision("cowork")
        with self.cursor() as cur:
            cur.execute(
                "SELECT tenant_type_v2 FROM tenants WHERE id = %s",
                (tenant_id,),
            )
            self.assertEqual(cur.fetchone()["tenant_type_v2"], "f_firm")
            profile = firm_store.get_profile(cur, tenant_id=tenant_id)
            self.assertIsNotNone(profile)
            self.assertTrue(profile["firm_code"].startswith("PF"))
            self.assertEqual(module_store.get_business_type(cur, tenant_id=tenant_id), "firm")
            self.assertFalse(module_store.needs_onboarding(cur, tenant_id=tenant_id))

    def test_main_registration_remains_unclassified_without_firm_profile(self):
        tenant_id = self.provision("main")
        with self.cursor() as cur:
            cur.execute(
                "SELECT tenant_type_v2 FROM tenants WHERE id = %s",
                (tenant_id,),
            )
            self.assertIsNone(cur.fetchone()["tenant_type_v2"])
            self.assertIsNone(firm_store.get_profile(cur, tenant_id=tenant_id))
            self.assertTrue(module_store.needs_onboarding(cur, tenant_id=tenant_id))

    def test_firm_profile_failure_rolls_back_tenant_and_user_link(self):
        with (
            mock.patch.object(firm_store, "create_profile", side_effect=RuntimeError("boom")),
            mock.patch("services.authz.resolver.create_membership", return_value=True),
            mock.patch("services.auth.entrance_store.grant_entrance_safe"),
        ):
            with self.assertRaises(RuntimeError):
                with self.cursor() as cur:
                    _ensure_tenant_for_new_user(
                        cur,
                        self.user_id,
                        "credits",
                        company_name=self.name,
                        entry="cowork",
                    )

        with self.cursor() as cur:
            cur.execute("SELECT tenant_id FROM users WHERE id = %s", (self.user_id,))
            self.assertIsNone(cur.fetchone()["tenant_id"])
            cur.execute("SELECT count(*) AS n FROM tenants WHERE name = %s", (self.name,))
            self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
