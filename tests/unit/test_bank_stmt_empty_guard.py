# -*- coding: utf-8 -*-
"""银行对账单 Gemini 兜底:整张读空(0 行 + 无余额)必须升级重试,不能当成功放行。

回归 KTB 6694 现象:一张合法的零交易对账单(期末 26.89),某次识别把它读成
0 行 + 无余额并 ok=True 放行 → 对账里变成假的 0.00 期末。判据 _stmt_has_content
把"整张读空"和"合法零交易(有余额)"区分开。
"""

import unittest

from services.ocr.gemini_models import try_with_fallback
from services.recon.bank_stmt_gemini import _stmt_has_content


class StmtHasContentTests(unittest.TestCase):
    def test_rows_present_is_content(self):
        self.assertTrue(_stmt_has_content({"rows": [{"date": "2568-01-01"}]}))

    def test_zero_txn_with_balance_is_content(self):
        # 合法零交易单:0 行但有余额 → 算抽到内容,不该升级
        self.assertTrue(_stmt_has_content({"rows": [], "opening_balance": 26.89}))
        self.assertTrue(_stmt_has_content({"rows": [], "closing_balance": 26.89}))

    def test_empty_read_is_not_content(self):
        self.assertFalse(_stmt_has_content({"rows": [], "opening_balance": None}))
        self.assertFalse(_stmt_has_content({"rows": []}))
        self.assertFalse(_stmt_has_content(None))


class EscalationBehaviorTests(unittest.TestCase):
    def test_empty_first_read_escalates_and_recovers(self):
        calls = []

        def fake(model):
            calls.append(model)
            return {"rows": []} if len(calls) == 1 else {"rows": [{"date": "2568-01-01"}]}

        out = try_with_fallback(fake, primary="m1", ok=_stmt_has_content)
        self.assertEqual(len(calls), 2, "整张读空应升级到兜底模型")
        self.assertTrue(out["rows"])

    def test_both_reads_empty_returns_none(self):
        def fake_empty(_model):
            return {"rows": [], "opening_balance": None}

        self.assertIsNone(try_with_fallback(fake_empty, primary="m1", ok=_stmt_has_content))

    def test_legit_empty_statement_not_escalated(self):
        calls = []

        def fake_balance_only(model):
            calls.append(model)
            return {"rows": [], "opening_balance": 26.89}

        out = try_with_fallback(fake_balance_only, primary="m1", ok=_stmt_has_content)
        self.assertEqual(len(calls), 1, "有余额的合法零交易单不该浪费一次升级")
        self.assertEqual(out["opening_balance"], 26.89)


if __name__ == "__main__":
    unittest.main()
