# -*- coding: utf-8 -*-
"""B8 RLS wave3 3b · 真 workspace_clients + seller_workspace_routes 表端到端隔离(REFACTOR-B8)。

真 ensure_workspace_tables()/ensure_seller_route_table()(建表 + enroll tenant_or_user)+ 真
store/seller_routing 函数,在真 postgres 上验:租户 A 的账套主体/卖方路由,租户 B 读不到、改不到、
分拣不到;tax_id 查重也跨租户隔离。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_workspace_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"

_OCR_STUB = (
    "CREATE TABLE ocr_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), "
    "user_id UUID, tenant_id UUID, total_amount NUMERIC, created_at TIMESTAMPTZ DEFAULT now())"
)


class WorkspaceRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.workspace import store, seller_routing

        cls.db, cls.s, cls.r = db, store, seller_routing
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(
                "DROP TABLE IF EXISTS workspace_clients, seller_workspace_routes, ocr_history CASCADE"
            )
            cur.execute(_OCR_STUB)

        store.ensure_workspace_tables()  # 建 workspace_clients + ALTER ocr_history + enroll
        seller_routing.ensure_seller_route_table()  # 建 seller_workspace_routes + enroll

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            # alembic 才加的开票列(不在 ensure 的 CREATE)· 补上以测 create_workspace_client
            cur.execute(
                "ALTER TABLE workspace_clients "
                "ADD COLUMN IF NOT EXISTS address TEXT, ADD COLUMN IF NOT EXISTS branch TEXT, "
                "ADD COLUMN IF NOT EXISTS phone TEXT, "
                "ADD COLUMN IF NOT EXISTS vat_registered BOOLEAN DEFAULT TRUE"
            )
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON "
                "workspace_clients,seller_workspace_routes,ocr_history TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            for t in ("workspace_clients", "seller_workspace_routes"):
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS workspace_clients, seller_workspace_routes, "
                    "ocr_history CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE workspace_clients, seller_workspace_routes RESTART IDENTITY")

    def _seed(self):
        wa = self.s.create_workspace_client(UA, A, "WS-A", tax_id="111")
        wb = self.s.create_workspace_client(UB, B, "WS-B", tax_id="222")
        self.assertIsNotNone(wa)
        self.assertIsNotNone(wb)
        return wa, wb

    def test_list_get_cross_tenant_blocked(self):
        wa, _ = self._seed()
        self.assertEqual(
            [w["name"] for w in self.s.list_workspace_clients(UA, tenant_id=A)], ["WS-A"]
        )
        self.assertEqual(
            [w["name"] for w in self.s.list_workspace_clients(UB, tenant_id=B)], ["WS-B"]
        )
        self.assertIsNone(self.s.get_workspace_client(wa, UB, tenant_id=B))
        self.assertIsNotNone(self.s.get_workspace_client(wa, UA, tenant_id=A))

    def test_update_archive_bind_cross_tenant_blocked(self):
        wa, _ = self._seed()
        self.assertFalse(self.s.update_workspace_client(wa, UB, tenant_id=B, name="hack"))
        self.assertTrue(self.s.update_workspace_client(wa, UA, tenant_id=A, name="ok"))
        self.assertFalse(self.s.bind_workspace_endpoint(wa, "ep", UB, tenant_id=B))
        self.assertTrue(self.s.bind_workspace_endpoint(wa, "ep", UA, tenant_id=A))
        self.assertFalse(self.s.archive_workspace_client(wa, UB, tenant_id=B))
        self.assertTrue(self.s.archive_workspace_client(wa, UA, tenant_id=A))

    def test_tax_id_in_use_cross_tenant_blocked(self):
        self._seed()
        self.assertTrue(self.s.tax_id_in_use(UA, A, "111"))
        # B 看不到 A 的主体 → A 的税号对 B 不算占用
        self.assertFalse(self.s.tax_id_in_use(UB, B, "111"))

    def test_seller_routing_cross_tenant_blocked(self):
        wa, _ = self._seed()
        self.assertTrue(self.r.learn_seller_workspace_route("9999999999999", "SellerX", wa, UA, A))
        a_match = self.r.match_workspace_for_seller("9999999999999", "SellerX", UA, A)
        self.assertEqual(a_match["workspace_client_id"], wa)
        # B 既看不到 A 的路由记忆,也看不到 A 的账套 → 分拣无果
        b_match = self.r.match_workspace_for_seller("9999999999999", "SellerX", UB, B)
        self.assertEqual(b_match["action"], "none")


if __name__ == "__main__":
    unittest.main()
