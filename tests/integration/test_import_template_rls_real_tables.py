# -*- coding: utf-8 -*-
"""B8 RLS wave4 · import_template_mappings 真表隔离(REFACTOR-B8)。

tenant_id NOT NULL(无 user_id 列)→ 纯 tenant 隔离(apply_tenant_rls)。4 个 CRUD 全传
tenant_id 且 WHERE tenant_id。在真 postgres 验:租户 A 存的模板,租户 B 经真 DAL 读不到;
WITH CHECK 拦跨租户写。

CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_import_template_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FAKE = "00000000-0000-0000-0000-0000000000ff"


class ImportTemplateRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.importer import template_store as ts

        cls.db, cls.rls, cls.ts = db, rls, ts
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS import_template_mappings CASCADE")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
            cur.execute(ts._DDL_TABLE)
            cur.execute(ts._DDL_INDEX)
            rls.apply_tenant_rls(cur, "import_template_mappings")
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON import_template_mappings TO pearnly_app"
            )
            cur.execute("ALTER TABLE import_template_mappings FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS import_template_mappings CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE import_template_mappings")

    def test_real_dal_cross_tenant_blocked(self):
        self.assertTrue(self.ts.save_mapping(A, "statement", "sigA", {"date": 0, "balance": 4}))
        self.assertTrue(self.ts.save_mapping(B, "statement", "sigB", {"date": 1}))
        # 真 DAL 各自只见自己的
        self.assertEqual(self.ts.find_mapping(A, "statement", "sigA"), {"date": 0, "balance": 4})
        self.assertIsNone(self.ts.find_mapping(A, "statement", "sigB"))  # B 的签名 A 看不到
        self.assertEqual(len(self.ts.list_mappings(A)), 1)
        self.assertEqual(len(self.ts.list_mappings(FAKE)), 0)

    def test_delete_scoped_to_tenant(self):
        self.assertTrue(self.ts.save_mapping(A, "gl", "sg", {"x": 0}))
        rows = self.ts.list_mappings(A, "gl")
        self.assertEqual(len(rows), 1)
        mid = rows[0]["id"]
        # 假租户删不动(RLS 看不到该行)
        self.assertFalse(self.ts.delete_mapping(FAKE, mid))
        self.assertTrue(self.ts.delete_mapping(A, mid))

    def test_with_check_blocks_cross_tenant_write(self):
        import psycopg2

        with self.assertRaises(psycopg2.errors.Error):
            with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
                cur.execute(
                    "INSERT INTO import_template_mappings"
                    "(tenant_id, document_type, header_signature, mapping_json) "
                    "VALUES (%s,'statement','s','{}'::jsonb)",
                    (B,),
                )


if __name__ == "__main__":
    unittest.main()
