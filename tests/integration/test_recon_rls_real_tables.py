# -*- coding: utf-8 -*-
"""B8 RLS wave2 · 真 recon 表端到端隔离(REFACTOR-B8)。

用真 ensure_vat_recon_tables() 建表+enroll + 真 store 函数(create/get/update/list/
record_field_override),在真 postgres 上验证:租户 A 建的 reconciliation_task/row/vat_report,
租户 B 凭 task_id/row_id 一概读不到、改不到。证 hard point 1(传递式)+ hard point 2(穿上下文)
合起来真闭合。CI 默认 skip(无真 DB),本地/恢复库跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_recon_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"


class ReconRealTableRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.recon import vat_recon_schema, vat_recon_store

        cls.db, cls.store = db, vat_recon_store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            # 干净重建(测试库可能残留上轮 stub)· 顺序:先 recon 表(引 FK)再 stub
            cur.execute(
                "DROP TABLE IF EXISTS reconciliation_row, reconciliation_task, vat_report, "
                "ocr_history, clients CASCADE"
            )
            # FK 依赖:clients(id) + ocr_history(id) 必须先存在(只建 store 用到的列)
            cur.execute("CREATE TABLE clients (id BIGSERIAL PRIMARY KEY)")
            cur.execute(
                "CREATE TABLE ocr_history ("
                "id UUID PRIMARY KEY, invoice_no TEXT, invoice_date DATE, seller_name TEXT, "
                "total_amount NUMERIC, filename TEXT, pages JSONB)"
            )
        vat_recon_schema.ensure_vat_recon_tables()  # 建 vat_report/task/row + enroll
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON vat_report,reconciliation_task,"
                "reconciliation_row,clients,ocr_history TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            # field_overrides 列在真库由独立迁移加(不在 ensure DDL)· 补上以测 field_override 写
            cur.execute(
                "ALTER TABLE reconciliation_row ADD COLUMN IF NOT EXISTS field_overrides JSONB"
            )
            # FORCE:本地恢复库的 owner 也受 policy 约束,才能真测隔离(prod 靠非 owner 角色)
            for t in ("vat_report", "reconciliation_task", "reconciliation_row"):
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
            cur.execute(
                "TRUNCATE reconciliation_row, reconciliation_task, vat_report RESTART IDENTITY"
            )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                for t in ("vat_report", "reconciliation_task", "reconciliation_row"):
                    cur.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")

    def _seed_tenant_a(self):
        rid = self.store.create_vat_report(A, UA, None, 2026, 5, [{"row_no": 1}], {"total_vat": 7})
        tid = self.store.create_recon_task(A, UA, None, 2026, 5, rid)
        self.store.bulk_insert_recon_rows(
            [{"task_id": tid, "invoice_id": None, "status": "matched", "diff_fields": {}}],
            tenant_id=A,
            user_id=UA,
        )
        rows = self.store.list_recon_rows_detailed(tid, tenant_id=A, user_id=UA)
        return rid, tid, rows[0]["id"]

    def test_owner_sees_own_other_tenant_blocked(self):
        report_id, task_id, row_id = self._seed_tenant_a()

        # A 看得到自己的
        self.assertIsNotNone(self.store.get_recon_task(task_id, tenant_id=A, user_id=UA))
        self.assertIsNotNone(self.store.get_vat_report(report_id, tenant_id=A, user_id=UA))
        self.assertIsNotNone(self.store.get_recon_row(row_id, tenant_id=A, user_id=UA))
        self.assertEqual(
            len(self.store.list_recon_rows_detailed(task_id, tenant_id=A, user_id=UA)), 1
        )

        # B 凭同样的 id 一概读不到(传递式 + tenant_or_user 双重)
        self.assertIsNone(self.store.get_recon_task(task_id, tenant_id=B, user_id=UB))
        self.assertIsNone(self.store.get_vat_report(report_id, tenant_id=B, user_id=UB))
        self.assertIsNone(self.store.get_recon_row(row_id, tenant_id=B, user_id=UB))
        self.assertEqual(
            len(self.store.list_recon_rows_detailed(task_id, tenant_id=B, user_id=UB)), 0
        )

    def test_other_tenant_cannot_mutate(self):
        _, task_id, row_id = self._seed_tenant_a()

        # B 改 A 的 task 状态 → 影响 0 行(看不到就改不到)
        self.store.update_recon_task_status(task_id, "failed", tenant_id=B, user_id=UB)
        task = self.store.get_recon_task(task_id, tenant_id=A, user_id=UA)
        self.assertNotEqual(task["status"], "failed")

        # B 改 A 的 row action → False(改 0 行)
        self.assertFalse(
            self.store.update_recon_row_action(row_id, "resolved", tenant_id=B, user_id=UB)
        )
        # A 自己改 → True
        self.assertTrue(
            self.store.update_recon_row_action(row_id, "resolved", tenant_id=A, user_id=UA)
        )

    def test_field_override_cross_tenant_row_not_found(self):
        from services.recon import field_override as fo

        _, _, row_id = self._seed_tenant_a()
        # B 校正 A 的行 → 查空 → row_not_found
        r = fo.record_field_override(row_id, "buyer_name", "x", tenant_id=B, user_id=UB)
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "row_not_found")
        # A 自己校正 → ok
        r2 = fo.record_field_override(row_id, "buyer_name", "ACME Co", tenant_id=A, user_id=UA)
        self.assertTrue(r2["ok"])


if __name__ == "__main__":
    unittest.main()
