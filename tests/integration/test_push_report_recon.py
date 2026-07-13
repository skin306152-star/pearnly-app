# -*- coding: utf-8 -*-
"""T4c · 推送回执接入(F2 注入点3)真库集成测试。

覆盖 reconcile._default_shadow_push_report 端到端(真 erp_push_logs 表 · services/erp/
push_log_queries.list_push_logs_by_invoice_nos 新 DAL):工单 3 票号落 2 success 1 failed →
挂进 gates.r5_shadow.reconcile_gl.push 的 all_pushed/incomplete 判定 + reasons 透传 +
matched_by/matched_rows 标注;skipped_dup 归 success 侧;pending 未终态两侧都不进落 missing;
查无匹配行降级 no_report;跨租户行不可见(SQL 显式 tenant_id 隔离,非 RLS)。

MC2-C(erp_push_logs.work_order_id 列):同票号两工单场景下新推送精确归属零串(见
test_cross_work_order_same_invoice_no_zero_bleed);老数据(work_order_id 全 NULL)回落
invoice_no 路径不回归(见 test_legacy_null_work_order_id_falls_back)。

CI 默认 skip(tests/integration 惯例),本地跑:
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_push_report_recon -v
"""

from __future__ import annotations

import os
import unittest
import uuid

from tests.integration._helpers import require_db


class _FakeStore:
    """items/events 走内存态(与 tests/unit 的 workorder 测试同款 FakeStore)——本测试只需
    erp_push_logs 那一段是真库,items/events 不必真落 work_order_items/work_order_events。"""

    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)


def _money_evt(item_id, inv, net="1000.00", vat="70.00", grand="1070.00"):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "purchase_invoice",
            "status": "ok",
            "money": {"subtotal": net, "vat": vat, "total_amount": grand, "invoice_number": inv},
        },
    }


def _sales_evt():
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": "s1",
            "kind": "sales_summary",
            "status": "ok",
            "sales_read": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": ["01/05/2569", "5000.00", "350.00"], "is_summary": False}],
            },
        },
    }


class PushReportReconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        from core import db
        from services.erp import push_log_queries
        from services.workorder.engine import StepContext
        from services.workorder.steps import reconcile

        cls.db = db
        cls.q = push_log_queries
        cls.StepContext = StepContext
        cls.reconcile = reconcile

    def setUp(self):
        self.tenant_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        # 真 work_order_id 须是合法 UUID(erp_push_logs.work_order_id 列是 uuid 类型 · MC2-C)。
        self.work_order_id = str(uuid.uuid4())
        with self.db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users(id, username, password_hash) VALUES (%s, %s, 'x')",
                (self.user_id, f"t4c-test-{self.user_id[:8]}"),
            )
        self._prev_gate = self.reconcile._shadow_draft_enabled
        self._prev_gl_rows = self.reconcile._shadow_gl_rows
        self.reconcile._shadow_draft_enabled = lambda ctx: True
        self.reconcile._shadow_gl_rows = lambda ctx: {"rows": [], "source": "none", "note": None}

    def tearDown(self):
        self.reconcile._shadow_draft_enabled = self._prev_gate
        self.reconcile._shadow_gl_rows = self._prev_gl_rows
        with self.db.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM erp_push_logs WHERE user_id = %s", (self.user_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))

    def _insert_log(self, invoice_no, status, tenant_id=None, error_msg=None, work_order_id=None):
        with self.db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO erp_push_logs"
                "(user_id, tenant_id, invoice_no, status, error_msg, attempt, work_order_id) "
                "VALUES (%s,%s,%s,%s,%s,1,%s)",
                (
                    self.user_id,
                    tenant_id or self.tenant_id,
                    invoice_no,
                    status,
                    error_msg,
                    work_order_id,
                ),
            )

    def _ctx(self, cur, invoice_nos, work_order_id=None):
        items = [
            {"id": f"p{i}", "kind": "purchase_invoice", "status": "ok", "flag_reason": None}
            for i in range(1, len(invoice_nos) + 1)
        ] + [{"id": "s1", "kind": "sales_summary", "status": "ok", "flag_reason": None}]
        events = [_money_evt(f"p{i}", inv) for i, inv in enumerate(invoice_nos, start=1)] + [
            _sales_evt()
        ]
        store = _FakeStore(items, events)
        return self.StepContext(
            cur=cur,
            tenant_id=self.tenant_id,
            work_order_id=work_order_id or self.work_order_id,
            store=store,
            data={},
        )

    def _push(self, invoice_nos, work_order_id=None):
        with self.db.get_cursor() as cur:
            out = self.reconcile.run(self._ctx(cur, invoice_nos, work_order_id=work_order_id))
        self.assertEqual(out.status, "ok")
        return out.payload["gates"]["r5_shadow"]["reconcile_gl"]["push"]

    def test_two_success_one_failed_marks_incomplete_with_reasons(self):
        self._insert_log("IV-1", "success")
        self._insert_log("IV-2", "success")
        self._insert_log("IV-3", "failed", error_msg="ไม่พบลูกค้า")
        push = self._push(["IV-1", "IV-2", "IV-3"])
        self.assertEqual(push["status"], "incomplete")
        self.assertTrue(push["alert"])
        self.assertEqual(sorted(push["pushed_ok"]), ["IV-1", "IV-2"])
        self.assertEqual(push["rejected"], [{"invoice_no": "IV-3", "reasons": ["ไม่พบลูกค้า"]}])
        self.assertEqual(push["missing"], [])
        self.assertEqual(push["matched_by"], "invoice_no")
        self.assertEqual(push["matched_rows"], 3)

    def test_skipped_dup_counts_as_success_side(self):
        self._insert_log("IV-1", "skipped_dup")
        push = self._push(["IV-1"])
        self.assertEqual(push["status"], "all_pushed")
        self.assertEqual(push["pushed_ok"], ["IV-1"])

    def test_pending_is_neither_success_nor_failed(self):
        self._insert_log("IV-1", "pending")
        push = self._push(["IV-1"])
        # 未终态两侧都不进 → 落 missing(如实"仍在途",不冒充成功/失败)。
        self.assertEqual(push["status"], "incomplete")
        self.assertEqual(push["missing"], ["IV-1"])
        self.assertEqual(push["pushed_ok"], [])
        self.assertEqual(push["rejected"], [])

    def test_no_matching_rows_stays_no_report(self):
        push = self._push(["IV-NEVER-PUSHED"])
        self.assertEqual(push["status"], "no_report")
        self.assertNotIn("matched_by", push)
        self.assertNotIn("matched_rows", push)

    def test_cross_tenant_row_invisible(self):
        other_tenant = str(uuid.uuid4())
        self._insert_log("IV-X", "success", tenant_id=other_tenant)
        push = self._push(["IV-X"])
        self.assertEqual(push["status"], "no_report")  # 本租户查无匹配行,不串号

    def test_cross_work_order_same_invoice_no_zero_bleed(self):
        # MC2-C 验收剧本:同租户两工单各自推过同一票号——本工单那行 success,
        # 另一工单那行 failed。按 work_order_id 精确查必须只看见本工单那行(success),
        # 绝不被另一工单的 failed 行串扰(旧口径靠 invoice_no 会两行都命中、行为不确定)。
        other_wo = str(uuid.uuid4())
        self._insert_log("IV-DUP", "success", work_order_id=self.work_order_id)
        self._insert_log("IV-DUP", "failed", error_msg="อีกงานหนึ่งพลาด", work_order_id=other_wo)
        push = self._push(["IV-DUP"])
        self.assertEqual(push["status"], "all_pushed")
        self.assertEqual(push["pushed_ok"], ["IV-DUP"])
        self.assertEqual(push["rejected"], [])
        self.assertEqual(push["matched_by"], "work_order_id")
        self.assertEqual(push["matched_rows"], 1)

    def test_legacy_null_work_order_id_falls_back(self):
        # 老数据(work_order_id 列 NULL,补列前的历史行)回落 invoice_no 路径不回归。
        self._insert_log("IV-LEGACY", "success", work_order_id=None)
        push = self._push(["IV-LEGACY"])
        self.assertEqual(push["status"], "all_pushed")
        self.assertEqual(push["pushed_ok"], ["IV-LEGACY"])
        self.assertEqual(push["matched_by"], "invoice_no")
        self.assertEqual(push["matched_rows"], 1)


if __name__ == "__main__":
    unittest.main()
