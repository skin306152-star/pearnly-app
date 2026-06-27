# -*- coding: utf-8 -*-
"""B8 RLS · 真 supplier_categories + buyer_to_client_memory 表端到端隔离(REFACTOR-B8)。

真 ensure_*(建表 + enroll apply_tenant_or_user_rls)+ 真 store 函数,在真 postgres 上验:
两表都是 tenant_or_user(tenant_id 可空 + user_id 兜底),租户 A 学的供应商分类/买方映射,租户 B
一概读不到、塞不进(WITH CHECK)。tenant_id IS NULL 的孤立用户行经 user_id 兜底分支隔离。
CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_suppliers_buyer_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"
FAKE = "00000000-0000-0000-0000-0000000000ff"


class SuppliersBuyerRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.clients import store, buyer_resolve

        cls.db, cls.s, cls.b = db, store, buyer_resolve
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS supplier_categories, buyer_to_client_memory CASCADE")

        store.ensure_supplier_categories_table()  # 建表 + enroll tenant_or_user
        buyer_resolve.ensure_buyer_to_client_table()  # 建表 + enroll tenant_or_user

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for t in ("supplier_categories", "buyer_to_client_memory"):
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {t} TO pearnly_app")
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS supplier_categories, buyer_to_client_memory CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE supplier_categories, buyer_to_client_memory RESTART IDENTITY")

    def test_supplier_categories_tenant_scoped(self):
        # 真 store 函数:同 seller 名,A/B 各记各的分类
        self.assertTrue(self.s.upsert_supplier_category("7-11", "food", UA, tenant_id=A))
        self.assertTrue(self.s.upsert_supplier_category("7-11", "fuel", UB, tenant_id=B))
        self.assertEqual(self.s.get_category_for_seller("7-11", UA, tenant_id=A), "food")
        self.assertEqual(self.s.get_category_for_seller("7-11", UB, tenant_id=B), "fuel")
        self.assertEqual(self.s.count_supplier_mappings(UA, tenant_id=A), 1)
        # 陌生租户读不到 A 的记忆
        self.assertIsNone(self.s.get_category_for_seller("7-11", UA, tenant_id=FAKE))
        self.assertEqual(self.s.count_supplier_mappings(UA, tenant_id=FAKE), 0)

    def test_supplier_categories_user_only_branch(self):
        # tenant_id IS NULL 的孤立用户行走 user_id 兜底分支
        self.assertTrue(self.s.upsert_supplier_category("Cafe", "drink", UA, tenant_id=None))
        self.assertEqual(self.s.get_category_for_seller("Cafe", UA, tenant_id=None), "drink")
        # 另一用户(无 tenant)读不到
        self.assertIsNone(self.s.get_category_for_seller("Cafe", UB, tenant_id=None))

    def test_buyer_memory_tenant_scoped(self):
        self.assertTrue(
            self.b.learn_buyer_to_client("BuyerX", "1234567890123", 100, UA, tenant_id=A)
        )
        self.assertTrue(
            self.b.learn_buyer_to_client("BuyerY", "9876543210987", 200, UB, tenant_id=B)
        )
        # 角色上下文下裸查 → policy 只放行自己租户
        with self.db.get_cursor_rls(tenant_id=A, user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM buyer_to_client_memory")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(tenant_id=FAKE, user_id=FAKE) as cur:
            cur.execute("SELECT count(*) n FROM buyer_to_client_memory")
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        # A 的上下文里塞 tenant_id=B 的行 → WITH CHECK 拦
        with self.db.get_cursor_rls(tenant_id=A, user_id=UA, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO supplier_categories (tenant_id, user_id, seller_name, category) "
                    "VALUES (%s, %s, 'x', 'y')",
                    (B, UA),
                )


if __name__ == "__main__":
    unittest.main()
