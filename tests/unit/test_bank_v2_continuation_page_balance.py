# -*- coding: utf-8 -*-
"""
v118.35.0.48 · 守门测试 · M4 银行对账余额验证 续页/缺期初 不误报 + 合并稳定排序

背景(2026-05-23 真实案例 · KKP 2805 / BBL 2697):
  用户上传银行对账单的『某一页 / 续页』(如 Page 3/3、Page 9/9)· 该页没有
  『ยอดยกมา / 期初余额』行 → 我们当 opening=0 → 验证第一笔交易时拿 0 当上一行
  余额 · 必然对不上 → 误标"余额验证未通过"(原件其实完全正确)。

  另:旧 merge_statements 按 (date, withdrawal, deposit) 排序 · 把同一天多笔按金额
  重排 · 打乱"上一行余额 ± 金额 = 本行余额"链条。

锁定契约:
  1. opening=0(续页·无期初)· 第一笔有金额交易 → balance_ok=None(不是 False)· 不误报
  2. opening 已知 · 第一笔交易照常验证(True/False)
  3. merge_statements 同日多笔保持 PDF 原始顺序(稳定排序 · 不按金额重排)
"""
import unittest
from datetime import date

from bank_recon_v2 import StatementRow, _verify_row_balances, merge_statements


# BBL 2697 Page 9/9 续页真实数据(PDF 顶到底顺序 · 余额链自洽)
_BBL2697 = [
    ("TRF", 713733.48,  0,         9316618.47),
    ("MSC", 0,          157043.90, 9473662.37),
    ("TRF", 1406008.89, 0,         8067653.48),
    ("TRF", 2157441.00, 0,         5910212.48),
    ("TRF", 100660.25,  0,         5809552.23),
    ("MSC", 0,          535000.00, 6344552.23),
    ("MSC", 3463776.72, 0,         2880775.51),
]


def _rows():
    return [StatementRow(date=date(2025, 12, 30), description=d,
                         withdrawal=w, deposit=dep, balance=b)
            for (d, w, dep, b) in _BBL2697]


class ContinuationPageBalanceTests(unittest.TestCase):

    def test_continuation_page_no_false_positive(self):
        """opening=0(续页)→ 第一笔交易标 None · 不误报 False · 其余照常 True"""
        rows = _rows()
        _verify_row_balances(rows, 0.0)
        self.assertIsNone(rows[0].balance_ok, "续页首笔应为 None(无从核对上一行余额)")
        self.assertEqual(sum(1 for r in rows if r.balance_ok is False), 0,
                         "续页不应有任何 False 误报")
        # 后续行用 PDF 印出来的真实余额逐行核对 · 全通过
        self.assertTrue(all(r.balance_ok is True for r in rows[1:]))

    def test_known_opening_verifies_first_row(self):
        """opening 已知(完整页有期初)→ 第一笔正常验证"""
        rows = _rows()
        # 第一笔 TRF 提款 713,733.48 → 余额 9,316,618.47 · 真实期初 = 10,030,351.95
        _verify_row_balances(rows, 10030351.95)
        self.assertTrue(rows[0].balance_ok, "已知期初时第一笔应通过验证")
        self.assertEqual(sum(1 for r in rows if r.balance_ok is False), 0)

    def test_known_opening_catches_misread(self):
        """opening 已知 · 余额被改错一位 → 该行 balance_ok=False(校验仍有效)"""
        rows = _rows()
        rows[0].balance = 9316618.47 + 1000.0  # 篡改首行余额
        _verify_row_balances(rows, 10030351.95)
        self.assertFalse(rows[0].balance_ok, "余额对不上时必须能标 False")

    def test_merge_keeps_pdf_order_same_date(self):
        """merge_statements 同日多笔保持原始顺序(不按金额重排)"""
        parsed = [{"ok": True, "bank_code": "bbl", "rows": _rows(),
                   "opening": 0.0, "closing": 2880775.51}]
        merged, _op, _cl, _bc = merge_statements(parsed)
        self.assertEqual([r.balance for r in merged],
                         [d[3] for d in _BBL2697],
                         "同日多笔合并后顺序应与 PDF 原序一致")


class RowHashDedupTests(unittest.TestCase):
    """v118.35.0.49 · 去重哈希含余额 · 防同日同额同描述的合法两笔被误删
    (真实案例 KKP 30/12 两笔一样的 SWD 65,573.75 · 余额不同 = 不同笔)"""

    def test_same_amount_diff_balance_not_deduped(self):
        """同日 / 同额 / 同描述 · 但余额不同 → 视为不同笔 · 不去重"""
        a = StatementRow(date=date(2025, 12, 30), description="SWD",
                         withdrawal=65573.75, deposit=0, balance=429666.83)
        b = StatementRow(date=date(2025, 12, 30), description="SWD",
                         withdrawal=65573.75, deposit=0, balance=364093.08)
        self.assertNotEqual(a.row_hash, b.row_hash, "余额不同应产生不同 row_hash")
        parsed = [{"ok": True, "bank_code": "kkp", "rows": [a, b],
                   "opening": 0.0, "closing": 364093.08}]
        merged, _op, _cl, _bc = merge_statements(parsed)
        self.assertEqual(len(merged), 2, "两笔合法交易不应被去重删成 1 笔")

    def test_true_duplicate_still_deduped(self):
        """完全相同(含余额)的真重复 · 仍去重(防同份文件传两次)"""
        a = StatementRow(date=date(2025, 12, 30), description="SWD",
                         withdrawal=65573.75, deposit=0, balance=429666.83)
        b = StatementRow(date=date(2025, 12, 30), description="SWD",
                         withdrawal=65573.75, deposit=0, balance=429666.83)
        self.assertEqual(a.row_hash, b.row_hash)
        parsed = [{"ok": True, "bank_code": "kkp", "rows": [a, b],
                   "opening": 0.0, "closing": 429666.83}]
        merged, _op, _cl, _bc = merge_statements(parsed)
        self.assertEqual(len(merged), 1, "真重复应去重")


if __name__ == "__main__":
    unittest.main()
