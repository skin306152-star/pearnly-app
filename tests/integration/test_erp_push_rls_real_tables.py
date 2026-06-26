# -*- coding: utf-8 -*-
"""B8 RLS wave4 · erp_endpoints / erp_push_logs 真表隔离 + JOIN 富化(REFACTOR-B8)。

两表 user_id 全非空、访问纯 user scope(INSERT 不写 tenant_id)→ 纯 user 隔离(apply_user_rls)。
本测试在真 postgres 验:
- 用户 A 的端点/推送日志,用户 B 在 role 上下文读不到;WITH CHECK 拦跨用户写日志。
- ★JOIN 富化难点:list_push_logs JOIN 的 ocr_history/clients 是 tenant_or_user 隔离 →
  穿 tenant_id+user_id 富化保住(client_name 命中);只穿 user_id 时 tenant_id 已落库的
  ocr_history 行不可见 → 富化丢(client_name 空)。证明路由穿 _tid 的必要性。

CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_erp_push_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

TA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # tenant A
UA = "11111111-1111-1111-1111-111111111111"  # user A
UB = "22222222-2222-2222-2222-222222222222"  # user B

_STUBS = (
    "CREATE TABLE erp_endpoints ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, tenant_id UUID,"
    "  name TEXT, adapter TEXT, config JSONB DEFAULT '{}'::jsonb, is_default BOOLEAN DEFAULT false,"
    "  auto_push BOOLEAN DEFAULT false, enabled BOOLEAN DEFAULT true, last_used_at TIMESTAMPTZ,"
    "  last_status TEXT, success_count INT DEFAULT 0, failure_count INT DEFAULT 0,"
    "  created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())",
    "CREATE TABLE erp_push_logs ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, tenant_id UUID,"
    "  endpoint_id UUID, history_id TEXT, invoice_no TEXT, seller_name TEXT, total_amount NUMERIC,"
    "  status TEXT, http_status INT, request_body JSONB, response_body TEXT, error_msg TEXT,"
    "  attempt INT DEFAULT 1, elapsed_ms INT DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW(),"
    "  trigger TEXT DEFAULT 'manual', retry_count INT DEFAULT 0, max_retries INT DEFAULT 3,"
    "  next_retry_at TIMESTAMPTZ, lease_owner TEXT, lease_expires_at TIMESTAMPTZ)",
    "CREATE TABLE ocr_history ("
    "  id TEXT PRIMARY KEY, user_id UUID, tenant_id UUID, client_id BIGINT,"
    "  workspace_client_id BIGINT, pages JSONB DEFAULT '[]'::jsonb)",
    "CREATE TABLE clients (" "  id BIGINT PRIMARY KEY, user_id UUID, tenant_id UUID, name TEXT)",
    "CREATE TABLE workspace_clients ("
    "  id BIGINT PRIMARY KEY, user_id UUID, tenant_id UUID, name TEXT)",
)
_TABLES = ("erp_push_logs", "erp_endpoints", "ocr_history", "clients", "workspace_clients")


class ErpPushRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.erp import push_store, push_log_queries

        cls.db, cls.rls = db, rls
        cls.push_store, cls.q = push_store, push_log_queries
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")
            for ddl in _STUBS:
                cur.execute(ddl)
            # erp 推送表 = 纯 user;JOIN 的实体表 = tenant_or_user(与 prod enroll 一致)。
            rls.apply_user_rls(cur, "erp_endpoints", "erp_push_logs")
            rls.apply_tenant_or_user_rls(cur, "ocr_history", "clients", "workspace_clients")
            cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {', '.join(_TABLES)} TO pearnly_app")
            for t in _TABLES:
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(f"TRUNCATE {', '.join(_TABLES)}")

    def _seed_endpoints(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_endpoints(user_id, name, adapter) "
                "VALUES (%s,'A-ep','mrerp'),(%s,'B-ep','mrerp')",
                (UA, UB),
            )

    def test_endpoints_user_isolated_direct(self):
        self._seed_endpoints()
        with self.db.get_cursor_rls(user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM erp_endpoints")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(user_id=UB) as cur:
            cur.execute("SELECT count(*) n FROM erp_endpoints")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(user_id="33333333-3333-3333-3333-333333333333") as cur:
            cur.execute("SELECT count(*) n FROM erp_endpoints")
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_list_erp_endpoints_real_fn_isolated(self):
        self._seed_endpoints()
        self.assertEqual(len(self.push_store.list_erp_endpoints(UA)), 1)
        self.assertEqual(self.push_store.list_erp_endpoints(UA)[0]["name"], "A-ep")
        self.assertEqual(len(self.push_store.list_erp_endpoints(UB)), 1)

    def test_insert_push_log_real_fn_then_user_isolated(self):
        # 真 DAL 各自写自己的日志,跨用户读不到。
        self.assertIsNotNone(
            self.push_store.insert_push_log(
                UA, None, None, "INV-A", "S", 100, "success", 200, None, None, None, 1, 5
            )
        )
        self.assertIsNotNone(
            self.push_store.insert_push_log(
                UB, None, None, "INV-B", "S", 100, "success", 200, None, None, None, 1, 5
            )
        )
        self.assertEqual(self.q.get_push_stats_today(UA)["total"], 1)
        self.assertEqual(self.q.get_push_stats_today(UB)["total"], 1)

    def test_with_check_blocks_writing_other_user(self):
        import psycopg2

        with self.assertRaises(psycopg2.errors.Error):
            with self.db.get_cursor_rls(user_id=UA, commit=True) as cur:
                cur.execute(
                    "INSERT INTO erp_push_logs(user_id, status, attempt) VALUES (%s,'success',1)",
                    (UB,),
                )

    def _seed_richenment(self):
        # ocr_history.tenant_id 已落库(TA)+ 关联 clients;push_log 属用户 A。
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO clients(id, user_id, tenant_id, name) VALUES (1,%s,%s,'ACME')",
                (UA, TA),
            )
            cur.execute(
                "INSERT INTO ocr_history(id, user_id, tenant_id, client_id) VALUES ('h1',%s,%s,1)",
                (UA, TA),
            )
            cur.execute(
                "INSERT INTO erp_push_logs(user_id, tenant_id, history_id, invoice_no, status) "
                "VALUES (%s,%s,'h1','INV-1','success')",
                (UA, TA),
            )

    def test_richenment_preserved_with_tenant_context(self):
        self._seed_richenment()
        res = self.q.list_push_logs(UA, tenant_id=TA)
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["client_name"], "ACME")  # 富化保住

    def test_richenment_lost_without_tenant_context(self):
        # 只穿 user_id:erp_push_logs 行仍可见(user 命中),但 tenant_id 已落库的
        # ocr_history 在 user-only 上下文不可见 → JOIN 富化 client_name 丢(为 None)。
        self._seed_richenment()
        res = self.q.list_push_logs(UA, tenant_id=None)
        self.assertEqual(res["total"], 1)  # 日志本身仍在
        self.assertIsNone(res["items"][0]["client_name"])  # 富化丢


if __name__ == "__main__":
    unittest.main()
