# -*- coding: utf-8 -*-
"""ERP push tables: legacy user isolation plus dormant shared Express SELECT.

本测试在真 postgres 验:
- legacy 行继续按 user 隔离,WITH CHECK 继续拦跨用户写。
- shared Express 只有 tenant/workspace 匹配且事务内 SET LOCAL 后可读,仍不可跨 actor 写。
- ★JOIN 富化难点:list_push_logs JOIN 的 ocr_history/clients 是 tenant_or_user 隔离 →
  穿 tenant_id+user_id 富化保住(client_name 命中);只穿 user_id 时 tenant_id 已落库的
  ocr_history 行不可见 → 富化丢(client_name 空)。证明路由穿 _tid 的必要性。

CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly_throwaway
    (这个库会被 DROP TABLE 拆掉,别指开发库;先对它执行
     CREATE TABLE IF NOT EXISTS _pearnly_disposable_test_db(note text);)
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_erp_push_rls_real_tables -v
"""

import os
import unittest
from unittest import mock

from tests.integration._helpers import require_disposable_db

TA = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # tenant A
TB = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # tenant B
UA = "11111111-1111-1111-1111-111111111111"  # user A
UB = "22222222-2222-2222-2222-222222222222"  # user B
UC = "33333333-3333-3333-3333-333333333333"  # user C
EXPRESS_EP = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0001"
MRERP_EP = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0002"
EXP_DISABLED_EP = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0003"
EXP_PRIVATE_EP = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0004"
DMS_EP = "eeeeeeee-eeee-eeee-eeee-eeeeeeee0005"
WS_A = 101
WS_B = 202

_STUBS = (
    "CREATE TABLE erp_endpoints ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, tenant_id UUID,"
    "  name TEXT, adapter TEXT, config JSONB DEFAULT '{}'::jsonb, is_default BOOLEAN DEFAULT false,"
    "  auto_push BOOLEAN DEFAULT false, enabled BOOLEAN DEFAULT true, last_used_at TIMESTAMPTZ,"
    "  last_status TEXT, success_count INT DEFAULT 0, failure_count INT DEFAULT 0,"
    "  created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW(),"
    "  workspace_client_id BIGINT, shared_scope BOOLEAN NOT NULL DEFAULT false,"
    "  binding_generation BIGINT NOT NULL DEFAULT 0)",
    "CREATE TABLE erp_push_logs ("
    "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL, tenant_id UUID,"
    "  workspace_client_id BIGINT,"
    "  endpoint_id UUID, history_id TEXT, invoice_no TEXT, seller_name TEXT, total_amount NUMERIC,"
    "  status TEXT, http_status INT, request_body JSONB, response_body TEXT, error_msg TEXT,"
    "  attempt INT DEFAULT 1, elapsed_ms INT DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW(),"
    "  trigger TEXT DEFAULT 'manual', retry_count INT DEFAULT 0, max_retries INT DEFAULT 3,"
    "  next_retry_at TIMESTAMPTZ, lease_owner TEXT, lease_expires_at TIMESTAMPTZ,"
    # 2026-07-14(3a29e228)产品给 erp_push_logs 加了 work_order_id 并写进 insert_push_log;
    # 这张表全仓只有这份手抄 DDL,漏补 → insert_push_log 整条 INSERT 撞 UndefinedColumn。
    "  work_order_id UUID)",
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
        require_disposable_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.erp import push_store, push_log_queries, shared_express_schema

        cls.db, cls.rls = db, rls
        cls.push_store, cls.q, cls.shared = push_store, push_log_queries, shared_express_schema
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")
            for ddl in _STUBS:
                cur.execute(ddl)
            # erp 推送表 = 纯 user;JOIN 的实体表 = tenant_or_user(与 prod enroll 一致)。
            rls.apply_user_rls(cur, "erp_endpoints", "erp_push_logs")
            shared_express_schema.apply_shared_express_foundation(cur)
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

    def _seed_shared_rows(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_endpoints "
                "(id,user_id,tenant_id,workspace_client_id,name,adapter,enabled,shared_scope) "
                "VALUES (%s,%s,%s,%s,'Shared Express','express',TRUE,TRUE),"
                "(%s,%s,%s,%s,'Legacy MRERP','mrerp',TRUE,TRUE),"
                "(%s,%s,%s,%s,'Disabled Express','express',FALSE,TRUE),"
                "(%s,%s,%s,%s,'Private Express','express',TRUE,FALSE),"
                "(%s,%s,%s,%s,'Shared MRERP DMS','mrerp_dms',TRUE,TRUE)",
                (
                    EXPRESS_EP,
                    UA,
                    TA,
                    WS_A,
                    MRERP_EP,
                    UA,
                    TA,
                    WS_A,
                    EXP_DISABLED_EP,
                    UA,
                    TA,
                    WS_A,
                    EXP_PRIVATE_EP,
                    UA,
                    TA,
                    WS_A,
                    DMS_EP,
                    UA,
                    TA,
                    WS_A,
                ),
            )

    def _enable_shared(self, cur, tenant_id=TA, workspace_id=WS_A):
        with mock.patch.object(
            self.shared,
            "erp_shared_express_endpoint_enabled_for",
            return_value=True,
        ):
            self.assertTrue(self.shared.enable_shared_express_select(cur, tenant_id, workspace_id))

    def test_shared_endpoint_requires_transaction_local_gate(self):
        self._seed_shared_rows()
        with self.db.get_cursor_rls(tenant_id=TA, workspace_client_id=WS_A, user_id=UB) as cur:
            cur.execute("SELECT name FROM erp_endpoints ORDER BY name")
            self.assertEqual(cur.fetchall(), [])

        with self.db.get_cursor_rls(tenant_id=TA, workspace_client_id=WS_A, user_id=UB) as cur:
            self._enable_shared(cur)
            cur.execute("SELECT name FROM erp_endpoints ORDER BY name")
            self.assertEqual([row["name"] for row in cur.fetchall()], ["Shared Express"])

        with self.db.get_cursor_rls(tenant_id=TA, workspace_client_id=WS_A, user_id=UB) as cur:
            cur.execute("SELECT name FROM erp_endpoints ORDER BY name")
            self.assertEqual(cur.fetchall(), [], "SET LOCAL must not survive the transaction")

    def test_shared_endpoint_is_workspace_scoped_and_select_only(self):
        self._seed_shared_rows()
        with self.db.get_cursor_rls(tenant_id=TA, workspace_client_id=WS_B, user_id=UB) as cur:
            self._enable_shared(cur, TA, WS_B)
            cur.execute("SELECT count(*) AS n FROM erp_endpoints")
            self.assertEqual(cur.fetchone()["n"], 0)

        with self.db.get_cursor_rls(tenant_id=TB, workspace_client_id=WS_A, user_id=UB) as cur:
            self._enable_shared(cur, TB)
            cur.execute("SELECT count(*) AS n FROM erp_endpoints")
            self.assertEqual(cur.fetchone()["n"], 0)

        with self.db.get_cursor_rls(
            tenant_id=TA, workspace_client_id=WS_A, user_id=UB, commit=True
        ) as cur:
            self._enable_shared(cur)
            cur.execute("UPDATE erp_endpoints SET name = 'changed' WHERE id = %s", (EXPRESS_EP,))
            self.assertEqual(cur.rowcount, 0)
            cur.execute("DELETE FROM erp_endpoints WHERE id = %s", (EXPRESS_EP,))
            self.assertEqual(cur.rowcount, 0)

        import psycopg2

        with self.assertRaises(psycopg2.errors.Error):
            with self.db.get_cursor_rls(
                tenant_id=TA, workspace_client_id=WS_A, user_id=UB, commit=True
            ) as cur:
                self._enable_shared(cur)
                cur.execute(
                    "INSERT INTO erp_endpoints "
                    "(user_id,tenant_id,workspace_client_id,name,adapter,enabled,shared_scope) "
                    "VALUES (%s,%s,%s,'forged-owner','express',TRUE,FALSE)",
                    (UA, TA, WS_A),
                )

        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT name FROM erp_endpoints WHERE id = %s", (EXPRESS_EP,))
            self.assertEqual(cur.fetchone()["name"], "Shared Express")

    def test_shared_push_log_requires_express_endpoint_and_gate(self):
        self._seed_shared_rows()
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_push_logs "
                "(user_id,tenant_id,workspace_client_id,endpoint_id,invoice_no,status) "
                "VALUES (%s,%s,%s,%s,'EXP-1','success'),"
                "(%s,%s,%s,%s,'MR-1','success'),"
                "(%s,%s,%s,%s,'DMS-1','success'),"
                "(%s,%s,%s,%s,'EXP-DISABLED','success'),"
                "(%s,%s,%s,%s,'EXP-PRIVATE','success'),"
                "(%s,%s,%s,%s,'EXP-WRONG-WS','success'),"
                "(%s,%s,%s,%s,'EXP-WRONG-TENANT','success')",
                (
                    UA,
                    TA,
                    WS_A,
                    EXPRESS_EP,
                    UA,
                    TA,
                    WS_A,
                    MRERP_EP,
                    UA,
                    TA,
                    WS_A,
                    DMS_EP,
                    UA,
                    TA,
                    WS_A,
                    EXP_DISABLED_EP,
                    UA,
                    TA,
                    WS_A,
                    EXP_PRIVATE_EP,
                    UA,
                    TA,
                    WS_B,
                    EXPRESS_EP,
                    UA,
                    TB,
                    WS_A,
                    EXPRESS_EP,
                ),
            )

        with self.db.get_cursor_rls(tenant_id=TA, workspace_client_id=WS_A, user_id=UB) as cur:
            cur.execute("SELECT invoice_no FROM erp_push_logs")
            self.assertEqual(cur.fetchall(), [])
            self._enable_shared(cur)
            cur.execute("SELECT invoice_no FROM erp_push_logs ORDER BY invoice_no")
            self.assertEqual([row["invoice_no"] for row in cur.fetchall()], ["EXP-1"])

        with self.db.get_cursor_rls(user_id=UA) as cur:
            cur.execute("SELECT invoice_no FROM erp_push_logs ORDER BY invoice_no")
            self.assertEqual(
                [row["invoice_no"] for row in cur.fetchall()],
                [
                    "DMS-1",
                    "EXP-1",
                    "EXP-DISABLED",
                    "EXP-PRIVATE",
                    "EXP-WRONG-TENANT",
                    "EXP-WRONG-WS",
                    "MR-1",
                ],
            )

    def test_partial_unique_only_rejects_active_shared_express(self):
        import psycopg2

        self._seed_shared_rows()
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute(
                "SELECT adapter FROM erp_endpoints WHERE id IN (%s,%s) ORDER BY adapter",
                (EXPRESS_EP, MRERP_EP),
            )
            self.assertEqual([row["adapter"] for row in cur.fetchall()], ["express", "mrerp"])
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "INSERT INTO erp_endpoints "
                    "(user_id,tenant_id,workspace_client_id,name,adapter,enabled,shared_scope) "
                    "VALUES (%s,%s,%s,'duplicate','express',TRUE,TRUE)",
                    (UB, TA, WS_A),
                )

        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_endpoints "
                "(user_id,tenant_id,workspace_client_id,name,adapter,enabled,shared_scope) "
                "VALUES (%s,%s,%s,'duplicate-disabled','express',FALSE,TRUE),"
                "(%s,%s,%s,'duplicate-private','express',TRUE,FALSE)",
                (UB, TA, WS_A, UC, TA, WS_A),
            )
            cur.execute(
                "SELECT count(*) AS n FROM erp_endpoints "
                "WHERE name IN ('duplicate-disabled','duplicate-private')"
            )
            self.assertEqual(cur.fetchone()["n"], 2)

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
