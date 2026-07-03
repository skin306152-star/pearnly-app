"""执行器只读跑通(mock core.db)+ 租户隔离参数透传 + B 档留桩。"""

import unittest
from unittest.mock import patch

from services.agent.contracts import AgentContext
from services.agent.executor import AgentToolset

_CTX = AgentContext(user={"id": "u1", "history_retention_days": 90}, tenant_id="t1")


class TestAgentExecutor(unittest.TestCase):
    def setUp(self):
        self.ts = AgentToolset()

    def test_recon_overview(self):
        # 2026-07-03 起双档形状({bank:{recent},income:{recent}})· 细契约在 test_agent_recon_tools。
        tasks = [
            {
                "bank_code": "KBANK",
                "matched_count": 42,
                "unmatched_gl": 2,
                "unmatched_stmt": 1,
                "status": "done",
                "created_at": "2026-07-01 09:00",
            },
        ]
        with (
            patch(
                "services.recon.bank_recon_v2_store.list_bank_recon_v2_tasks", return_value=tasks
            ),
            patch("services.recon.gl_vat_store.list_gl_vat_tasks", return_value=[]),
        ):
            res = self.ts.get_recon_overview(_CTX)
        self.assertTrue(res.ok)
        self.assertEqual(res.data["bank"]["recent"][0]["matched"], 42)
        self.assertIn("42", res.receipt)
        self.assertIn("3", res.receipt)  # 不一致 = unmatched_gl+unmatched_stmt

    def test_recon_overview_empty(self):
        with (
            patch("services.recon.bank_recon_v2_store.list_bank_recon_v2_tasks", return_value=[]),
            patch("services.recon.gl_vat_store.list_gl_vat_tasks", return_value=[]),
        ):
            res = self.ts.get_recon_overview(_CTX)
        self.assertTrue(res.ok)
        self.assertIn("hint", res.data)
        self.assertEqual(res.receipt, "")  # 无任务:数据诚实,成文交模型

    @patch("services.agent.executor.db")
    def test_list_history_passes_identity(self, db):
        db.get_visible_client_ids_for_user.return_value = [5]
        db.list_ocr_history.return_value = {"items": [{"id": "a"}], "total": 1, "status_counts": {}}
        res = self.ts.list_ocr_history(_CTX, keyword="7-11", status="failed")
        self.assertTrue(res.ok)
        kwargs = db.list_ocr_history.call_args.kwargs
        self.assertEqual(kwargs["user_id"], "u1")
        self.assertEqual(kwargs["tenant_id"], "t1")
        self.assertEqual(kwargs["keyword"], "7-11")
        self.assertEqual(kwargs["status_filter"], "failed")
        self.assertEqual(kwargs["restrict_client_ids"], [5])
        self.assertEqual(kwargs["retention_days"], 365)  # 套餐口径(非原始字段),与网页一致
        self.assertIsNone(kwargs["workspace_client_id"])  # 跨套账聚合
        self.assertTrue(res.receipt.startswith("agent.ok.history"))

    @patch("services.agent.executor.db")
    def test_history_summary_uses_overview(self, db):
        db.get_visible_client_ids_for_user.return_value = None
        db.docs_overview.return_value = {
            "doc_count": 4,
            "amount_total": 1234.0,
            "by_category": [("fuel", 3), ("food", 1)],
        }
        res = self.ts.summarize_ocr_history(_CTX)
        self.assertTrue(res.ok)
        self.assertEqual(res.data["doc_count"], 4)
        self.assertIn("count=4", res.receipt)
        self.assertIn("1,234", res.receipt)
        self.assertIn("fuel 3", res.receipt)
        kwargs = db.docs_overview.call_args.kwargs
        self.assertEqual(kwargs["retention_days"], 365)
        self.assertFalse(kwargs["this_month"])  # 汇总走保留期窗口,非本月
        self.assertIsNone(kwargs["workspace_client_id"])  # 跨套账聚合

    @patch("services.agent.executor.db")
    def test_balance(self, db):
        db.get_billing_status_combined.return_value = {
            "balance_thb": 123.45,
            "pages_used_this_month": 2,
        }
        res = self.ts.get_balance(_CTX)
        self.assertTrue(res.ok)
        db.get_billing_status_combined.assert_called_once_with("u1", "t1")
        self.assertIn("123.45", res.receipt)

    @patch("services.agent.executor.db")
    def test_usage_this_month(self, db):
        db.get_billing_status_combined.return_value = {"balance_thb": 0, "pages_used_this_month": 7}
        db.get_visible_client_ids_for_user.return_value = None
        db.docs_overview.return_value = {"doc_count": 5, "amount_total": 0.0, "by_category": []}
        res = self.ts.get_usage_this_month(_CTX)
        self.assertTrue(res.ok)
        self.assertIn("pages=7", res.receipt)
        self.assertIn("docs=5", res.receipt)
        kwargs = db.docs_overview.call_args.kwargs
        self.assertFalse(kwargs["include_categories"])  # 用量只要张数
        self.assertTrue(kwargs["this_month"])  # 用量是计费口径 → 本月

    @patch("services.agent.executor.db")
    def test_list_notifications(self, db):
        db.list_notification_logs.return_value = [{"id": 1}, {"id": 2}]
        res = self.ts.list_notification_logs(_CTX)
        self.assertTrue(res.ok)
        db.list_notification_logs.assert_called_once_with("u1", tenant_id="t1", limit=20)
        self.assertIn("count=2", res.receipt)
        # 契约:data 恒 dict(list 结果包成 {"items"}),消费侧不再 isinstance
        self.assertEqual(res.data, {"items": [{"id": 1}, {"id": 2}]})

    def test_push_prepare_requires_permission(self):
        # push_to_erp 已从 M1 桩变备料实现(全链在 test_agent_push_confirm):无权限先拦。
        with patch(
            "services.agent.executor._plan_permissions", return_value={"can_push_erp": False}
        ):
            res = self.ts.push_to_erp(_CTX, doc_keyword="7-11")
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, "forbidden")


if __name__ == "__main__":
    unittest.main()
