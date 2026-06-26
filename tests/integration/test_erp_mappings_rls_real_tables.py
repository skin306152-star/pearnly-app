# -*- coding: utf-8 -*-
"""B8 RLS wave4 · ERP 4 张映射表真表隔离(REFACTOR-B8)。

在真 postgres 上验 erp_client/account/tax/product_mappings 的租户隔离(第二道防线):
4 张表都 tenant_id NOT NULL(无 user_id 列)→ 纯 tenant 模板。租户 A 写的映射,
租户 B 读不到;WITH CHECK 拦住「往别家租户塞映射」。account/tax/product 三类
还过真 DAL(upsert/list/find)证明穿上下文后业务路径仍工作。
client 映射的 upsert 含 clients↔users 归属 JOIN,本测试用直 SQL 验隔离(不建账号体系)。

CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_erp_mappings_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FAKE = "00000000-0000-0000-0000-0000000000ff"

_STUBS = (
    "CREATE TABLE erp_client_mappings ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL,"
    "  client_id BIGINT NOT NULL, erp_type TEXT NOT NULL, erp_code VARCHAR(128) NOT NULL,"
    "  notes TEXT, created_by UUID, created_at TIMESTAMPTZ DEFAULT NOW(),"
    "  updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, client_id, erp_type))",
    "CREATE TABLE erp_account_mappings ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL,"
    "  erp_type TEXT NOT NULL, pearnly_category VARCHAR(64) NOT NULL, erp_code VARCHAR(128) NOT NULL,"
    "  erp_name TEXT, notes TEXT, created_by UUID, created_at TIMESTAMPTZ DEFAULT NOW(),"
    "  updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, erp_type, pearnly_category))",
    "CREATE TABLE erp_tax_mappings ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL,"
    "  erp_type TEXT NOT NULL, pearnly_tax_kind VARCHAR(32) NOT NULL, erp_code VARCHAR(64) NOT NULL,"
    "  notes TEXT, created_by UUID, created_at TIMESTAMPTZ DEFAULT NOW(),"
    "  updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, erp_type, pearnly_tax_kind))",
    "CREATE TABLE erp_product_mappings ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL,"
    "  erp_type TEXT NOT NULL, item_name TEXT NOT NULL, item_name_norm VARCHAR(256) NOT NULL,"
    "  erp_code VARCHAR(128) NOT NULL, erp_name TEXT, notes TEXT, created_by UUID,"
    "  created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW(),"
    "  UNIQUE(tenant_id, erp_type, item_name_norm))",
)
_TABLES = (
    "erp_client_mappings",
    "erp_account_mappings",
    "erp_tax_mappings",
    "erp_product_mappings",
)


class ErpMappingsRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.erp import mappings_store as store

        cls.db, cls.rls, cls.store = db, rls, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")
            for ddl in _STUBS:
                cur.execute(ddl)
            rls.apply_tenant_rls(cur, *_TABLES)
            cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {', '.join(_TABLES)} TO pearnly_app")
            # FORCE:本地恢复库 owner 也受 policy 约束才能真测隔离(prod 靠非 owner 角色)。
            for t in _TABLES:
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY")

    # ── 真 DAL 写入后跨租户隔离(account / tax / product 不含账号 JOIN)──────
    def test_account_mapping_real_fn_cross_tenant_blocked(self):
        self.assertTrue(
            self.store.upsert_erp_account_mapping(A, "mrerp", "rent", "4000", "Rent", "", None)
        )
        self.assertTrue(
            self.store.upsert_erp_account_mapping(B, "mrerp", "rent", "5000", "Rent", "", None)
        )
        self.assertEqual(len(self.store.list_erp_account_mappings(A)), 1)
        self.assertEqual(self.store.list_erp_account_mappings(A)[0]["erp_code"], "4000")
        self.assertEqual(len(self.store.list_erp_account_mappings(FAKE)), 0)

    def test_tax_mapping_real_fn_cross_tenant_blocked(self):
        self.assertTrue(self.store.upsert_erp_tax_mapping(A, "mrerp", "vat_7", "OUT7", "", None))
        self.assertTrue(self.store.upsert_erp_tax_mapping(B, "mrerp", "vat_7", "OUT9", "", None))
        self.assertEqual(len(self.store.list_erp_tax_mappings(A)), 1)
        self.assertEqual(len(self.store.list_erp_tax_mappings(FAKE)), 0)

    def test_product_mapping_real_fn_isolated_find(self):
        self.assertTrue(
            self.store.upsert_erp_product_mapping(
                A, "mrerp", "Widget-A", "WID1", "Widget A", "", None
            )
        )
        self.assertTrue(
            self.store.upsert_erp_product_mapping(
                B, "mrerp", "Widget-A", "WID2", "Widget A", "", None
            )
        )
        found_a = self.store.find_erp_product_mappings_batch(A, "mrerp", ["Widget-A"])
        self.assertEqual(found_a.get("widgeta", {}).get("erp_code"), "WID1")
        self.assertEqual(
            self.store.find_erp_product_mappings_batch(FAKE, "mrerp", ["Widget-A"]), {}
        )

    # ── WITH CHECK:不能往别家租户塞映射 ─────────────────────────────
    def test_with_check_blocks_writing_other_tenant(self):
        import psycopg2

        with self.assertRaises(psycopg2.errors.Error):
            with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
                cur.execute(
                    "INSERT INTO erp_account_mappings(tenant_id, erp_type, pearnly_category, erp_code) "
                    "VALUES (%s, 'mrerp', 'rent', '4000')",
                    (B,),
                )

    # ── client 映射(含归属 JOIN)直 SQL 验隔离 ─────────────────────
    def test_client_mapping_cross_tenant_blocked(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_client_mappings(tenant_id, client_id, erp_type, erp_code) "
                "VALUES (%s, 1, 'mrerp', 'C-A'),(%s, 2, 'mrerp', 'C-B')",
                (A, B),
            )
        with self.db.get_cursor_rls(tenant_id=A) as cur:
            cur.execute("SELECT count(*) n FROM erp_client_mappings")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(tenant_id=FAKE) as cur:
            cur.execute("SELECT count(*) n FROM erp_client_mappings")
            self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main()
