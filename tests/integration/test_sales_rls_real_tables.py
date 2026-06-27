# -*- coding: utf-8 -*-
"""B8 RLS · sales 域孤儿表真表端到端隔离(REFACTOR-B8)。

真 ensure_sales_rls()(enroll apply_tenant_rls)在真 postgres 上验:sales 文档/明细/送达/设置 +
连号计数器都是按 tenant 隔离,租户 A 的行租户 B 一概读不到、塞不进(WITH CHECK)。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_sales_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

TA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

# enroll 与 store 解耦,这里用最小真实列建表(覆盖隔离列 tenant_id)。
_DDL = {
    "sales_documents": (
        "id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, "
        "doc_type text NOT NULL DEFAULT 'invoice', status text NOT NULL DEFAULT 'draft', "
        "created_by uuid"
    ),
    "sales_document_lines": (
        "id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, "
        "document_id uuid NOT NULL, line_no int NOT NULL DEFAULT 1, description text NOT NULL DEFAULT ''"
    ),
    "sales_document_sends": (
        "id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, "
        "document_id uuid NOT NULL, channel text NOT NULL DEFAULT 'email', created_by uuid"
    ),
    "sales_settings": "tenant_id uuid PRIMARY KEY, seller_name text NOT NULL DEFAULT ''",
    "document_number_sequences": (
        "tenant_id uuid NOT NULL, doc_type text NOT NULL, prefix text NOT NULL, "
        "period text NOT NULL, next_number bigint NOT NULL DEFAULT 1, "
        "PRIMARY KEY (tenant_id, doc_type, prefix, period)"
    ),
    "products": (
        "id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL, "
        "code text, name text NOT NULL DEFAULT ''"
    ),
}


class SalesRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.sales import schema

        cls.db, cls.schema = db, schema
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            for table, cols in _DDL.items():
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                cur.execute(f"CREATE TABLE {table} ({cols})")

        schema.ensure_sales_rls()  # enroll apply_tenant_rls × 5

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _DDL:
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO pearnly_app")
                cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                for table in _DDL:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _DDL:
                cur.execute(f"TRUNCATE {table}")

    def _seed_tenant(self, tenant):
        with self.db.get_cursor_rls(tenant, commit=True) as cur:
            cur.execute(
                "INSERT INTO sales_documents (tenant_id) VALUES (%s) RETURNING id",
                (tenant,),
            )
            doc_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO sales_document_lines (tenant_id, document_id) VALUES (%s, %s)",
                (tenant, doc_id),
            )
            cur.execute(
                "INSERT INTO sales_document_sends (tenant_id, document_id) VALUES (%s, %s)",
                (tenant, doc_id),
            )
            cur.execute("INSERT INTO sales_settings (tenant_id) VALUES (%s)", (tenant,))
            cur.execute(
                "INSERT INTO document_number_sequences (tenant_id, doc_type, prefix, period) "
                "VALUES (%s, 'invoice', 'IV', '2506')",
                (tenant,),
            )
            cur.execute("INSERT INTO products (tenant_id, name) VALUES (%s, 'P')", (tenant,))

    def test_tenant_sees_only_own_rows(self):
        self._seed_tenant(TA)
        self._seed_tenant(TB)
        for table in _DDL:
            with self.db.get_cursor_rls(TA) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见自己 1 行")
            with self.db.get_cursor_rls("00000000-0000-0000-0000-0000000000ff") as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生租户应见 0 行")

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(TA, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute("INSERT INTO sales_settings (tenant_id) VALUES (%s)", (TB,))

    def test_bypass_sees_all(self):
        self._seed_tenant(TA)
        self._seed_tenant(TB)
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM sales_documents")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
