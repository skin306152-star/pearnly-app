# -*- coding: utf-8 -*-
"""
BUG-FIX-RECON-ASYNC #16 守门测试 · GET /bank-v2/{id} 还原 run 响应的顶层
stats / parse_info / warnings(从 summary_json)· 让异步完成 + 历史载入渲染不丢内容。
"""

import asyncio
import json
import unittest
from unittest import mock

import recon_routes as rr


class BankGetEnrichTests(unittest.TestCase):
    def _task(self):
        summary = {
            "matched_count": 5,
            "gl_debit_only_count": 1,
            "gl_credit_only_count": 2,
            "stmt_withdrawal_only_count": 3,
            "stmt_deposit_only_count": 4,
            "formula_diff": 0.0,
            "_parse_info": {"stmt_files": [{"file": "s.pdf", "ok": True}]},
            "_brv2_warnings": ["期间不匹配"],
        }
        return {
            "id": 42,
            "bank_code": "BAY",
            "gl_account": "1010",
            "matched_count": 5,
            "unmatched_gl": 3,
            "unmatched_stmt": 7,
            "stmt_opening": 0,
            "stmt_closing": 0,
            "gl_opening": 0,
            "gl_closing": 0,
            "formula_diff": 0,
            "detail_json": [],
            "summary_json": json.dumps(summary),
            "created_at": "2026-05-24",
        }

    def test_stats_parse_info_warnings_restored(self):
        with (
            mock.patch(
                "recon_routes_bankv2.get_current_user_from_request",
                return_value={"id": "u1", "tenant_id": "t1"},
            ),
            mock.patch.object(rr.db, "get_bank_recon_v2_task", return_value=self._task()),
        ):
            out = asyncio.run(rr.bank_v2_get_task(42, request=None))
        st = out["stats"]
        self.assertEqual(st["matched"], 5)
        self.assertEqual(st["gl_debit_only"], 1)
        self.assertEqual(st["gl_credit_only"], 2)
        self.assertEqual(st["stmt_withdrawal_only"], 3)
        self.assertEqual(st["stmt_deposit_only"], 4)
        self.assertEqual(out["parse_info"], {"stmt_files": [{"file": "s.pdf", "ok": True}]})
        self.assertEqual(out["warnings"], ["期间不匹配"])

    def test_missing_summary_safe(self):
        task = self._task()
        task["summary_json"] = None
        with (
            mock.patch(
                "recon_routes_bankv2.get_current_user_from_request",
                return_value={"id": "u1", "tenant_id": "t1"},
            ),
            mock.patch.object(rr.db, "get_bank_recon_v2_task", return_value=task),
        ):
            out = asyncio.run(rr.bank_v2_get_task(42, request=None))
        self.assertEqual(out["stats"]["matched"], 5)  # 回退 task.matched_count
        self.assertIsNone(out["parse_info"])
        self.assertEqual(out["warnings"], [])


if __name__ == "__main__":
    unittest.main()
