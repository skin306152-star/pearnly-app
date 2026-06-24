# -*- coding: utf-8 -*-
"""守门:GL 期初余额反推修正(mrerp 2026-06-24 真因 · OCR 把 215,228.06 截成 215.00)。

GL 行带运行余额 → 用首笔『余额 − (借 − 贷)』反推真期初,整列自洽时采信,
否则保留原值不瞎改。修在 merge_gl_files(路由对账唯一汇合点)。
"""

import unittest
from datetime import date

from services.recon.bank_recon_merge import _reconcile_gl_opening, merge_gl_files
from services.recon.bank_recon_types import GlRow


def _rows(balances_debits_credits):
    """[(balance, debit, credit), ...] → [GlRow]。日期递增,银行 GL:借增余额。"""
    out = []
    for i, (bal, d, c) in enumerate(balances_debits_credits):
        out.append(
            GlRow(
                date=date(2025, 6, i + 1),
                doc_no=f"V{i}",
                account_code="1112-01",
                description="x",
                debit=float(d),
                credit=float(c),
                balance=float(bal),
            )
        )
    return out


# 真账套(mrerp):期初 215,228.06;首笔借 200,000→余额 415,228.06;次笔贷 380,000→35,228.06
_GOOD = [(415228.06, 200000.0, 0.0), (35228.06, 0.0, 380000.0)]


class GlOpeningReconcileTests(unittest.TestCase):
    def test_truncated_opening_auto_corrected(self):
        # OCR 把 215,228.06 截成 215.00 → 反推修回(整列自洽)
        self.assertEqual(_reconcile_gl_opening(215.00, _rows(_GOOD)), 215228.06)

    def test_correct_opening_unchanged(self):
        self.assertEqual(_reconcile_gl_opening(215228.06, _rows(_GOOD)), 215228.06)

    def test_no_running_balance_keeps_original(self):
        rows = _rows([(0.0, 200000.0, 0.0), (0.0, 0.0, 380000.0)])
        self.assertEqual(_reconcile_gl_opening(215.00, rows), 215.00)

    def test_inconsistent_balances_not_force_corrected(self):
        # 连行余额也被截断(415.00)→ 反推不自洽 → 不瞎改,保留原值
        rows = _rows([(415.00, 200000.0, 0.0), (35228.06, 0.0, 380000.0)])
        self.assertEqual(_reconcile_gl_opening(215.00, rows), 215.00)

    def test_merge_gl_files_fixes_opening_and_closing(self):
        parsed = [{"ok": True, "opening": 215.00, "accounts": ["1112-01"], "rows": _rows(_GOOD)}]
        _rows_out, _accts, opening, closing = merge_gl_files(parsed)
        self.assertEqual(opening, 215228.06)
        # closing = 期初 + Σ借 − Σ贷 = 215228.06 + 200000 − 380000
        self.assertEqual(closing, 35228.06)


if __name__ == "__main__":
    unittest.main()
