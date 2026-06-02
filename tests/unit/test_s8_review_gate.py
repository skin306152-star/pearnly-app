# -*- coding: utf-8 -*-
"""ADR-006 S8a-wire · 银行对账 handler「核对闸」守门测试。

验证真 handler 代码路径(非纯 mock 逻辑):低信心 PDF 账单 → 返回 needs_review 哨兵;
Excel 账单 → 不触发(走 S1–S7);确认重对账(注入 confirmed_stmt_rows)→ 跳过核对闸。
解析/读盘用 patch 替身(避免真 OCR/真文件)· 闸在落库前返回 · 无需 DB。
"""

import datetime as dt
import unittest
from unittest.mock import patch

import db
import recon_routes as RR
import services.recon_jobs.handlers as H
import services.recon_jobs.bank_handler as BH
from bank_recon_v2 import StatementRow


def _low_conf_pdf_result():
    return {
        "ok": True,
        "rows": [
            StatementRow(
                date=dt.date(2026, 5, 1),
                description="ฝาก",
                withdrawal=0,
                deposit=100.0,
                balance=1100.0,
                confidence="low",
            ),
        ],
        "opening": 1000.0,
        "closing": 1100.0,
        "low_conf_count": 1,
        "completeness": {"ok": True},
    }


def _read_inputs_fake(stmt_name="scan.pdf"):
    def _f(input_ref, role):
        if role == "stmt":
            return [(b"x", stmt_name)]
        return [(b"y", "gl.xlsx")]

    return _f


class S8ReviewGateTests(unittest.TestCase):
    def test_low_conf_pdf_triggers_needs_review(self):
        with (
            patch.object(BH, "_read_inputs", side_effect=_read_inputs_fake("scan.pdf")),
            patch.object(RR, "parse_bank_statement_pdf", return_value=_low_conf_pdf_result()),
            patch.object(RR, "parse_gl_v2", return_value={"ok": True, "rows": []}),
        ):
            result = H.run_bank_recon(
                {"is_exempt": True, "user_id": "u1", "tenant_id": None},
                [{"role": "stmt"}, {"role": "gl"}],
                lambda p: None,
            )
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], "__needs_review__")
        self.assertEqual(result[1]["kind"], "bank_stmt_rows")
        self.assertEqual(result[1]["row_count"], 1)
        self.assertEqual(result[1]["opening"], 1000.0)
        self.assertEqual(result[1]["files"], ["scan.pdf"])

    def test_excel_stmt_does_not_trigger_review_gate(self):
        # Excel 账单即使低信心也不归 S8 核对(走 S1–S7 列映射)→ 闸不触发 → 不返回哨兵
        with (
            patch.object(BH, "_read_inputs", side_effect=_read_inputs_fake("book.xlsx")),
            patch.object(RR, "parse_bank_statement_pdf", return_value=_low_conf_pdf_result()),
            patch.object(RR, "parse_gl_v2", return_value={"ok": True, "rows": []}),
            patch.object(RR, "merge_statements", return_value=([], 0.0, 0.0, "generic")),
            patch.object(RR, "merge_gl_files", return_value=([], [], 0.0, 0.0)),
        ):
            # merge 返回空 → handler 走 _save_failed_task(需 db)· 我们只验证『没在闸处返回哨兵』
            with patch.object(db, "create_bank_recon_v2_task", return_value="failtask"):
                result = H.run_bank_recon(
                    {"is_exempt": True, "user_id": "u1", "tenant_id": None},
                    [{"role": "stmt"}, {"role": "gl"}],
                    lambda p: None,
                )
        self.assertNotEqual(result[0], "__needs_review__")

    def test_confirmed_rows_skip_review_gate(self):
        # 注入 confirmed_stmt_rows → 跳过 OCR + 跳过核对闸 · 直接进对账(此处 merge 替身返回空走失败落库)
        confirmed = [
            {
                "idx": 0,
                "date": "2026-05-01",
                "description": "ฝาก",
                "withdrawal": 0,
                "deposit": 100.0,
                "balance": 1100.0,
                "confidence": "high",
            }
        ]
        with (
            patch.object(BH, "_read_inputs", side_effect=_read_inputs_fake("scan.pdf")),
            patch.object(RR, "parse_gl_v2", return_value={"ok": True, "rows": []}),
            patch.object(RR, "merge_statements", return_value=([], 0.0, 0.0, "generic")),
            patch.object(RR, "merge_gl_files", return_value=([], [], 0.0, 0.0)),
            patch.object(db, "create_bank_recon_v2_task", return_value="failtask"),
        ):
            result = H.run_bank_recon(
                {
                    "is_exempt": True,
                    "user_id": "u1",
                    "tenant_id": None,
                    "confirmed_stmt_rows": confirmed,
                    "confirmed_opening": 1000.0,
                },
                [{"role": "stmt"}, {"role": "gl"}],
                lambda p: None,
            )
        self.assertNotEqual(result[0], "__needs_review__")


if __name__ == "__main__":
    unittest.main()
