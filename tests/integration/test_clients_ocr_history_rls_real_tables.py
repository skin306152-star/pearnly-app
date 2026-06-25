# -*- coding: utf-8 -*-
"""B8 RLS wave3 · 真 clients + ocr_history 表端到端隔离(REFACTOR-B8)。

用真 ensure_clients_table()(建 clients + ALTER ocr_history + enroll tenant_or_user)+ 真 store
函数(create_client/list_clients/get_client + list_ocr_history/get_ocr_history_detail/
delete_ocr_history),在真 postgres 上验证:租户 A 建的客户/发票,租户 B 一概读不到、删不到。
CI 默认 skip(无真 DB),本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_clients_ocr_history_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"

_OCR_STUB = """
CREATE TABLE ocr_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, tenant_id UUID,
    filename TEXT, page_count INT, file_size_kb INT, file_hash TEXT,
    pages JSONB DEFAULT '[]'::jsonb, confidence TEXT, elapsed_ms INT,
    invoice_no TEXT, invoice_date DATE, seller_name TEXT, total_amount NUMERIC,
    archive_name TEXT, category_tag TEXT, archived_at TIMESTAMPTZ,
    fields_edited_at TIMESTAMPTZ, edit_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(),
    source_pdf_id UUID, source_page_indices JSONB, source_index INT, source_total INT,
    source TEXT DEFAULT 'manual', source_ref TEXT,
    pdf_storage_path TEXT, pdf_size_bytes INT,
    workspace_client_id INT
)
"""


class ClientsOcrHistoryRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.clients import store as clients_store
        from services.ocr_history import queries, mutations

        cls.db, cls.clients, cls.q, cls.m = db, clients_store, queries, mutations
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS ocr_history, clients, users CASCADE")
            # users 根表(不 enroll)· clients/ocr_history 的 tenant 子查询读它
            cur.execute("CREATE TABLE users (id UUID PRIMARY KEY, tenant_id UUID)")
            cur.execute("INSERT INTO users(id,tenant_id) VALUES (%s,%s),(%s,%s)", (UA, A, UB, B))
            cur.execute(_OCR_STUB)  # ocr_history 须先存在(ensure_clients_table 会 ALTER 它)

        clients_store.ensure_clients_table()  # 建 clients + ALTER ocr_history.client_id + enroll 两表

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            # 买方目录列由独立迁移加(不在 ensure 的 CREATE)· 补上以测 create_client
            cur.execute(
                "ALTER TABLE clients ADD COLUMN IF NOT EXISTS party_type TEXT, "
                "ADD COLUMN IF NOT EXISTS branch TEXT, ADD COLUMN IF NOT EXISTS promptpay_id TEXT"
            )
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON clients,ocr_history,users TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            # FORCE:本地恢复库 owner 也受 policy 约束才能真测隔离(prod 靠非 owner 角色)
            for t in ("clients", "ocr_history"):
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS ocr_history, clients, users CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE clients, ocr_history RESTART IDENTITY")

    def _seed(self):
        # 真 store 函数建客户(RLS 下 WITH CHECK 校验租户)
        cida = self.clients.create_client(UA, A, "ClientA")
        cidb = self.clients.create_client(UB, B, "ClientB")
        self.assertIsNotNone(cida)
        self.assertIsNotNone(cidb)
        # 发票直接 seed(系统侧 bypass · 模拟 OCR 落库)
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO ocr_history(user_id,tenant_id,filename,invoice_no,client_id) "
                "VALUES (%s,%s,'a.pdf','INV-A',%s) RETURNING id",
                (UA, A, cida),
            )
            ra = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO ocr_history(user_id,tenant_id,filename,invoice_no,client_id) "
                "VALUES (%s,%s,'b.pdf','INV-B',%s)",
                (UB, B, cidb),
            )
        return cida, cidb, str(ra)

    def test_clients_cross_tenant_blocked(self):
        cida, cidb, _ = self._seed()
        a_list = self.clients.list_clients(UA, tenant_id=A)
        self.assertEqual([c["name"] for c in a_list], ["ClientA"])
        b_list = self.clients.list_clients(UB, tenant_id=B)
        self.assertEqual([c["name"] for c in b_list], ["ClientB"])
        # B 凭 A 的 client_id 点名也读不到
        self.assertIsNone(self.clients.get_client(UB, cida, tenant_id=B))
        self.assertIsNotNone(self.clients.get_client(UA, cida, tenant_id=A))

    def test_ocr_history_cross_tenant_blocked(self):
        _, _, ra = self._seed()
        a_hist = self.q.list_ocr_history(UA, retention_days=-1, tenant_id=A)
        self.assertEqual(a_hist["total"], 1)
        self.assertEqual(a_hist["items"][0]["invoice_no"], "INV-A")
        b_hist = self.q.list_ocr_history(UB, retention_days=-1, tenant_id=B)
        self.assertEqual(b_hist["total"], 1)
        self.assertEqual(b_hist["items"][0]["invoice_no"], "INV-B")
        # B 凭 A 的 row id 点名读不到详情
        self.assertIsNone(self.q.get_ocr_history_detail(UB, ra, tenant_id=B))
        self.assertIsNotNone(self.q.get_ocr_history_detail(UA, ra, tenant_id=A))

    def test_cross_tenant_cannot_mutate(self):
        _, _, ra = self._seed()
        # B 删 A 的发票 → 0 行(看不到删不到)
        self.assertFalse(self.m.delete_ocr_history(UB, ra, tenant_id=B))
        self.assertIsNotNone(self.q.get_ocr_history_detail(UA, ra, tenant_id=A))
        # A 删自己的 → True
        self.assertTrue(self.m.delete_ocr_history(UA, ra, tenant_id=A))


if __name__ == "__main__":
    unittest.main()
