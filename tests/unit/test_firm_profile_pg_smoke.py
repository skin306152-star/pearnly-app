# -*- coding: utf-8 -*-
"""会计事务所经营层回填、短码与 RLS 的真 PostgreSQL 冒烟。"""

from __future__ import annotations

import contextlib
import json
import unittest
import uuid
from unittest import mock

from core.rls import ensure_rls_app_role
from services.firm import schema
from tests.unit._pg_smoke import connect, connect_or_skip

BASE_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    display_name text,
    tenant_type text NOT NULL DEFAULT 'shared_api',
    status text NOT NULL DEFAULT 'active',
    tenant_type_v2 text DEFAULT 'firm',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS display_name text;
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
ALTER TABLE tenants DROP CONSTRAINT IF EXISTS ck_tenants_tenant_type_v2_allowed;
ALTER TABLE tenants ALTER COLUMN tenant_type_v2 SET DEFAULT 'firm';
"""


class FirmProfilePgSmokeTests(unittest.TestCase):
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
        cls.ids = {name: str(uuid.uuid4()) for name in ("firm", "small", "unknown", "kept", "peer")}
        with cursor() as cur:
            cur.execute(BASE_DDL)
            for name, tenant_id in cls.ids.items():
                initial = "m_business" if name == "kept" else "firm"
                cur.execute(
                    "INSERT INTO tenants (id, name, display_name, tenant_type_v2) "
                    "VALUES (%s, %s, %s, %s)",
                    (tenant_id, f"pg-{name}", f"Display {name}", initial),
                )
            for name, business_type in (
                ("firm", "firm"),
                ("small", "restaurant"),
                ("kept", "firm"),
                ("peer", "firm"),
            ):
                cur.execute(
                    "INSERT INTO tenant_modules (tenant_id, module_key, config) "
                    "VALUES (%s, '__business_type__', %s::jsonb)",
                    (cls.ids[name], json.dumps({"value": business_type})),
                )

        cls.patch = mock.patch("core.db.get_cursor", cursor)
        cls.patch.start()
        schema.ensure_firm_schema()
        with cursor() as cur:
            ensure_rls_app_role(cur)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            with cls.cursor() as cur:
                cur.execute(
                    "DELETE FROM tenant_modules WHERE tenant_id = ANY(%s::uuid[])",
                    (list(cls.ids.values()),),
                )
                cur.execute(
                    "DELETE FROM tenants WHERE id = ANY(%s::uuid[])", (list(cls.ids.values()),)
                )
        finally:
            cls.patch.stop()
            cls.conn.close()

    def tenant_types(self):
        with self.cursor() as cur:
            cur.execute(
                "SELECT id::text, tenant_type_v2 FROM tenants WHERE id = ANY(%s::uuid[])",
                (list(self.ids.values()),),
            )
            return {row["id"]: row["tenant_type_v2"] for row in cur.fetchall()}

    def test_mapping_null_and_legal_value_preservation(self):
        got = self.tenant_types()
        self.assertEqual(got[self.ids["firm"]], "f_firm")
        self.assertEqual(got[self.ids["small"]], "s_micro")
        self.assertIsNone(got[self.ids["unknown"]])
        self.assertEqual(got[self.ids["kept"]], "m_business")
        self.assertEqual(got[self.ids["peer"]], "f_firm")

    def test_default_is_null_and_check_rejects_unknown_non_null_value(self):
        tenant_id = str(uuid.uuid4())
        self.ids["default"] = tenant_id
        with self.cursor() as cur:
            cur.execute("INSERT INTO tenants (id, name) VALUES (%s, 'default-null')", (tenant_id,))
            cur.execute("SELECT tenant_type_v2 FROM tenants WHERE id = %s", (tenant_id,))
            self.assertIsNone(cur.fetchone()["tenant_type_v2"])

        import psycopg2

        with self.assertRaises(psycopg2.errors.CheckViolation):
            with self.cursor() as cur:
                cur.execute(
                    "UPDATE tenants SET tenant_type_v2 = 'merchant' WHERE id = %s", (tenant_id,)
                )

    def test_profile_codes_are_unique_sequence_codes_and_retry_preserves_name(self):
        with self.cursor() as cur:
            cur.execute(
                "SELECT tenant_id::text, firm_code FROM accounting_firm_profiles "
                "WHERE tenant_id = ANY(%s::uuid[]) ORDER BY tenant_id",
                (list(self.ids.values()),),
            )
            rows = [dict(row) for row in cur.fetchall()]
        self.assertEqual({row["tenant_id"] for row in rows}, {self.ids["firm"], self.ids["peer"]})
        codes = [row["firm_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(
            all(code.startswith("PF") and code[2:].isdigit() and len(code) >= 10 for code in codes)
        )

        with self.cursor() as cur:
            cur.execute(
                "UPDATE accounting_firm_profiles SET display_name = 'Custom Name' WHERE tenant_id = %s",
                (self.ids["firm"],),
            )
        schema.ensure_firm_schema()
        with self.cursor() as cur:
            cur.execute(
                "SELECT display_name FROM accounting_firm_profiles WHERE tenant_id = %s",
                (self.ids["firm"],),
            )
            self.assertEqual(cur.fetchone()["display_name"], "Custom Name")

    def test_rls_hides_peer_and_rejects_cross_tenant_insert(self):
        from psycopg2.extras import RealDictCursor

        owner_rows = None
        with self.cursor() as cur:
            cur.execute(
                "SELECT tenant_id::text FROM accounting_firm_profiles "
                "WHERE tenant_id = ANY(%s::uuid[])",
                ([self.ids["firm"], self.ids["peer"]],),
            )
            owner_rows = {row["tenant_id"] for row in cur.fetchall()}
        self.assertEqual(owner_rows, {self.ids["firm"], self.ids["peer"]})

        tenant_conn = connect()
        try:
            cur = tenant_conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SET LOCAL ROLE pearnly_app")
            cur.execute("SET LOCAL app.current_tenant_id = %s", (self.ids["firm"],))
            cur.execute(
                "SELECT tenant_id::text FROM accounting_firm_profiles "
                "WHERE tenant_id = ANY(%s::uuid[])",
                ([self.ids["firm"], self.ids["peer"]],),
            )
            self.assertEqual({row["tenant_id"] for row in cur.fetchall()}, {self.ids["firm"]})
            tenant_conn.rollback()

            cur = tenant_conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SET LOCAL ROLE pearnly_app")
            cur.execute("SET LOCAL app.current_tenant_id = %s", (self.ids["firm"],))
            with self.assertRaises(Exception):
                cur.execute(
                    "INSERT INTO accounting_firm_profiles (tenant_id, display_name) "
                    "VALUES (%s, 'Cross tenant')",
                    (self.ids["unknown"],),
                )
        finally:
            tenant_conn.rollback()
            tenant_conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
