"""执行器只读跑通(mock core.db)+ 租户隔离参数透传 + B 档留桩。"""

import unittest
from unittest.mock import patch

from services.agent.contracts import AgentContext
from services.agent.executor import AgentToolset

_CTX = AgentContext(user={"id": "u1", "history_retention_days": 90}, tenant_id="t1")


class TestAgentExecutor(unittest.TestCase):
    def setUp(self):
        self.ts = AgentToolset()

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
        self.assertEqual(kwargs["retention_days"], 90)
        self.assertTrue(res.receipt.startswith("agent.ok.history"))

    @patch("services.agent.executor.db")
    def test_history_summary_uses_month_overview(self, db):
        db.get_visible_client_ids_for_user.return_value = None
        db.month_overview.return_value = {
            "doc_count": 4,
            "amount_total": 1234.0,
            "by_category": [("fuel", 3), ("food", 1)],
        }
        res = self.ts.summarize_ocr_history(_CTX)
        self.assertTrue(res.ok)
        self.assertEqual(res.data["doc_count"], 4)
        # 本月量透传给渲染:合计฿(千分位)+ 分类。
        self.assertIn("count=4", res.receipt)
        self.assertIn("1,234", res.receipt)
        self.assertIn("fuel 3", res.receipt)
        kwargs = db.month_overview.call_args.kwargs
        self.assertEqual(kwargs["retention_days"], 90)

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
        db.month_overview.return_value = {"doc_count": 5, "amount_total": 0.0, "by_category": []}
        res = self.ts.get_usage_this_month(_CTX)
        self.assertTrue(res.ok)
        self.assertIn("pages=7", res.receipt)
        self.assertIn("docs=5", res.receipt)
        # 用量只要张数,不查分类分布(省一次分组查询)。
        self.assertFalse(db.month_overview.call_args.kwargs["include_categories"])

    @patch("services.agent.executor.db")
    def test_list_notifications(self, db):
        db.list_notification_logs.return_value = [{"id": 1}, {"id": 2}]
        res = self.ts.list_notification_logs(_CTX)
        self.assertTrue(res.ok)
        db.list_notification_logs.assert_called_once_with("u1", tenant_id="t1", limit=20)
        self.assertIn("count=2", res.receipt)

    def test_b_bucket_stub_not_implemented(self):
        res = self.ts.push_to_erp(_CTX, history_id="h1")
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, "not_implemented_m1")


if __name__ == "__main__":
    unittest.main()
