# -*- coding: utf-8 -*-
"""B5 守门:批次中心展示态派生 + 聚合(纯逻辑 · 无 DB · 无主路径)。

锁定:
  1. 展示态从 erp_push_logs 现有字段派生 · 不依赖新 status(不改状态机);
  2. failed 的三向分流:retrying(有 next_retry_at+未到上限)/ needs_action(用户数据错)
     / failed(技术终态)正确;
  3. 100/1000 张聚合计数正确;
  4. 有/无 batch_id 都能分组(schema 落地前后都可用)。
"""

import unittest

from services.erp.batch_view import (
    classify_push_log,
    summarize_logs,
    group_into_batches,
    NO_BATCH_KEY,
)

# 注入的用户数据错判定替身(不依赖 db)
_UDF = lambda e: (e or "") in ("ERR_NO_CUSTOMER_MAPPING", "ERR_NO_CLIENT")  # noqa: E731


class ClassifyTests(unittest.TestCase):
    def test_success_and_skipped(self):
        self.assertEqual(
            classify_push_log({"status": "success"}, is_user_data_error=_UDF), "success"
        )
        self.assertEqual(
            classify_push_log({"status": "skipped_dup"}, is_user_data_error=_UDF), "skipped"
        )

    def test_failed_retrying(self):
        row = {
            "status": "failed",
            "next_retry_at": "2026-05-26T10:00:00Z",
            "retry_count": 1,
            "max_retries": 3,
            "error_msg": "ERR_TECHNICAL: timeout",
        }
        self.assertEqual(classify_push_log(row, is_user_data_error=_UDF), "retrying")

    def test_failed_needs_action_user_data(self):
        row = {
            "status": "failed",
            "next_retry_at": None,
            "retry_count": 0,
            "max_retries": 3,
            "error_msg": "ERR_NO_CUSTOMER_MAPPING",
        }
        self.assertEqual(classify_push_log(row, is_user_data_error=_UDF), "needs_action")

    def test_failed_terminal_technical(self):
        # 技术错但已到重试上限 → 终态 failed
        row = {
            "status": "failed",
            "next_retry_at": "2026-05-26T10:00:00Z",
            "retry_count": 3,
            "max_retries": 3,
            "error_msg": "ERR_TECHNICAL: timeout",
        }
        self.assertEqual(classify_push_log(row, is_user_data_error=_UDF), "failed")

    def test_express_manual_needs_action(self):
        # Express 留人工(缺科目/低置信)· 不重试 · 展示成待处理。
        row = {"status": "manual", "error_msg": "EXPRESS_MANUAL: no_revenue_account"}
        self.assertEqual(classify_push_log(row, is_user_data_error=_UDF), "needs_action")


class SummarizeTests(unittest.TestCase):
    def test_counts_100(self):
        rows = []
        rows += [{"status": "success"}] * 80
        rows += [
            {"status": "failed", "error_msg": "ERR_NO_CUSTOMER_MAPPING", "next_retry_at": None}
        ] * 12
        rows += [
            {
                "status": "failed",
                "error_msg": "ERR_TECHNICAL",
                "next_retry_at": "x",
                "retry_count": 0,
                "max_retries": 3,
            }
        ] * 5
        rows += [{"status": "skipped_dup"}] * 3
        s = summarize_logs(rows, is_user_data_error=_UDF)
        self.assertEqual(s["total"], 100)
        self.assertEqual(s["success"], 80)
        self.assertEqual(s["needs_action"], 12)
        self.assertEqual(s["retrying"], 5)
        self.assertEqual(s["skipped"], 3)
        self.assertEqual(s["failed"], 0)


class GroupTests(unittest.TestCase):
    def test_group_by_batch_id(self):
        rows = [
            {"batch_id": "b1", "status": "success"},
            {"batch_id": "b1", "status": "failed", "error_msg": "ERR_NO_CUSTOMER_MAPPING"},
            {"batch_id": "b2", "status": "success"},
        ]
        g = group_into_batches(rows, is_user_data_error=_UDF)
        self.assertEqual(g["b1"]["total"], 2)
        self.assertEqual(g["b1"]["success"], 1)
        self.assertEqual(g["b1"]["needs_action"], 1)
        self.assertEqual(g["b2"]["total"], 1)

    def test_no_batch_id_falls_back(self):
        rows = [{"status": "success"}, {"status": "success"}]
        g = group_into_batches(rows, is_user_data_error=_UDF)
        self.assertIn(NO_BATCH_KEY, g)
        self.assertEqual(g[NO_BATCH_KEY]["total"], 2)


if __name__ == "__main__":
    unittest.main()
