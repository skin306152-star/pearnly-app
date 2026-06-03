# -*- coding: utf-8 -*-
"""
v118.35.0.63 · 守门测试 · 完整性交叉校验(_audit_completeness)· 主动发现漏行/读错

思路:账单底部通常印『笔数 + 合计』(skin AM 账单页脚:No. of Credits 4 / Total 8,000)。
把提取结果和这些印刷数 + 期末平衡交叉对一遍 —— 对不上就证明漏了行或读错了,
哪怕余额链看着没破绽。笔数对不上是『漏一整笔』最硬的证据。

锁定契约:
  1. 全一致 → ok=True · 无 issue
  2. 印刷笔数 > 识别笔数 → credit/debit_count_mismatch(抓漏行)
  3. 印刷合计 ≠ 识别合计 → sum_mismatch
  4. opening+Σ存−Σ取 ≠ closing → closing_mismatch
  5. 没有印刷汇总 + 期末也没给 → 不误报(ok=True)
"""

import unittest

from services.recon.bank_recon_v2 import StatementRow, _audit_completeness


def _r(dep=0.0, wd=0.0, bal=0.0):
    return StatementRow(date=None, description="t", withdrawal=wd, deposit=dep, balance=bal)


class CompletenessTests(unittest.TestCase):

    def test_all_consistent_ok(self):
        rows = [
            _r(dep=2000, bal=4786),
            _r(dep=2000, bal=6786),
            _r(dep=2000, bal=8786),
            _r(dep=2000, bal=10786),
        ]
        printed = {"total_credit": 8000, "total_debit": 0, "credit_count": 4, "debit_count": 0}
        res = _audit_completeness(rows, opening=2786, closing=10786, printed=printed)
        self.assertTrue(res["ok"], res["issues"])

    def test_credit_count_mismatch_detects_missed_row(self):
        # 账单印 4 笔存款 · 只识别 3 笔 → 漏了一笔
        rows = [_r(dep=2000, bal=4786), _r(dep=2000, bal=6786), _r(dep=2000, bal=8786)]
        printed = {"total_credit": 8000, "credit_count": 4, "total_debit": 0, "debit_count": 0}
        res = _audit_completeness(rows, opening=2786, closing=10786, printed=printed)
        self.assertFalse(res["ok"])
        types = {i["type"] for i in res["issues"]}
        self.assertIn("credit_count_mismatch", types)

    def test_sum_mismatch_detects_misread(self):
        rows = [
            _r(dep=2000, bal=4786),
            _r(dep=1800, bal=6586),  # 第二笔读成1800
            _r(dep=2000, bal=8586),
            _r(dep=2000, bal=10586),
        ]
        printed = {"total_credit": 8000, "credit_count": 4, "total_debit": 0, "debit_count": 0}
        res = _audit_completeness(rows, opening=2786, closing=10786, printed=printed)
        self.assertFalse(res["ok"])
        types = {i["type"] for i in res["issues"]}
        self.assertIn("credit_sum_mismatch", types)

    def test_closing_mismatch_without_printed_totals(self):
        # 没印刷汇总 · 但 opening+Σ ≠ closing → 仍能抓
        rows = [_r(dep=2000, bal=4786), _r(dep=2000, bal=6786)]
        res = _audit_completeness(rows, opening=2786, closing=99999, printed=None)
        self.assertFalse(res["ok"])
        self.assertIn("closing_mismatch", {i["type"] for i in res["issues"]})

    def test_no_anchors_no_false_alarm(self):
        rows = [_r(dep=2000, bal=4786), _r(dep=2000, bal=6786)]
        res = _audit_completeness(rows, opening=0.0, closing=0.0, printed=None)
        self.assertTrue(res["ok"])

    def test_polluted_sum_fields_suppressed_count_kept(self):
        # 真实案例 BAY:Gemini 把 closing(919384.8)同时填进 total_credit + total_debit
        # → sum 校验不可信必须跳过;但 count(314 vs 179)是真信号必须保留
        rows = [_r(dep=100, bal=100) for _ in range(179)]
        printed = {
            "total_credit": 919384.8,
            "total_debit": 919384.8,
            "credit_count": 314,
            "debit_count": 31,
        }
        res = _audit_completeness(rows, opening=500, closing=919384.8, printed=printed)
        types = {i["type"] for i in res["issues"]}
        self.assertNotIn("credit_sum_mismatch", types)
        self.assertNotIn("debit_sum_mismatch", types)
        self.assertIn("credit_count_mismatch", types)

    def test_wrong_sum_near_opening_still_flagged(self):
        # ④ 修复(2026-05-24)· 真错的合计恰好落在期初余额 0.1% 内时,旧实现(_tol=0.1% 宽容差)
        # 会把它当成"误填的期初余额"静默跳过 → 漏报。测试:opening=10000,印刷 Total Deposit=9999
        # (真值 5700,差期初仅 1 元),必须仍触发 credit_sum_mismatch(不被误当误填余额)。
        rows = [
            _r(dep=5000, bal=15000),
            _r(wd=1200, bal=13800),
            _r(wd=300, bal=13500),
            _r(dep=700, bal=14200),
        ]
        printed = {
            "total_credit": 9999.0,
            "total_debit": 1500.0,
            "credit_count": 2,
            "debit_count": 2,
        }
        res = _audit_completeness(rows, opening=10000.0, closing=14200.0, printed=printed)
        self.assertFalse(res["ok"])
        self.assertIn("credit_sum_mismatch", {i["type"] for i in res["issues"]})

    def test_exact_balance_misfile_still_suppressed(self):
        # ④ 反向保护:合计被原样复制成期末余额(精确)时,仍判误填 → 跳过(不误报)。
        rows = [
            _r(dep=5000, bal=15000),
            _r(wd=1200, bal=13800),
            _r(wd=300, bal=13500),
            _r(dep=700, bal=14200),
        ]
        printed = {
            "total_credit": 14200.0,
            "total_debit": 1500.0,
            "credit_count": 2,
            "debit_count": 2,
        }
        res = _audit_completeness(rows, opening=10000.0, closing=14200.0, printed=printed)
        # total_credit 精确等于期末(误填)→ 不应报 credit_sum_mismatch
        self.assertNotIn("credit_sum_mismatch", {i["type"] for i in res["issues"]})


if __name__ == "__main__":
    unittest.main()
