# -*- coding: utf-8 -*-
"""
v118.35.0.62 · 守门测试 · 余额链自动修复读错的金额(_repair_amount_from_balance)

真实案例(skin 实测 BAY/KBank):某行金额被 OCR 读错一两位,但前后两个余额都对得上
→ 真实金额可由『本行余额 − 上行余额』唯一反推。此时自动修正(差异小才动);
差太大(可能漏了一整笔)则保持 ⚠ 让用户核对 · 决不瞎改。

锁定契约:
  1. 金额读错(差异<30%)+ 前后余额佐证 → 自动修正 · balance_ok=True · amount_autocorrected=True
  2. 大额不符(>30% · 疑似漏行)→ 不修 · 保持 balance_ok=False
  3. 上一行不可靠 → 不修(无从反推)
  4. 本行余额未被下一行佐证 → 不修
  5. 方向本来就对、金额也对的行 → 不动
"""

import unittest

from services.recon.bank_recon_v2 import (
    StatementRow,
    _verify_row_balances,
    _repair_amount_from_balance,
)


def _row(dep=0.0, wd=0.0, bal=0.0, desc="t"):
    return StatementRow(date=None, description=desc, withdrawal=wd, deposit=dep, balance=bal)


def _run(rows, opening):
    _verify_row_balances(rows, opening)
    _repair_amount_from_balance(rows, opening)


class AmountRepairTests(unittest.TestCase):

    def test_small_misread_amount_autofixed(self):
        # opening 1000 · row1 印 dep=250 但真值 300(1500→1800)· 前后佐证 → 修成 300
        rows = [
            _row(dep=500, bal=1500),  # 1000+500=1500 ✓
            _row(dep=250, bal=1800),  # 印错;真值 300
            _row(dep=200, bal=2000),
        ]  # 1800+200=2000 ✓ 佐证上一行余额
        _run(rows, 1000.0)
        self.assertTrue(rows[1].amount_autocorrected)
        self.assertEqual(rows[1].deposit, 300.0)
        self.assertIs(rows[1].balance_ok, True)

    def test_large_diff_not_fixed_kept_warn(self):
        # row1 印 dep=50 但 delta=500(疑似漏了一整笔)· 差异 90% → 不修 · 保持 ⚠
        rows = [
            _row(dep=500, bal=1500),
            _row(dep=50, bal=2000),  # delta=500 远大于 50
            _row(dep=200, bal=2200),
        ]
        _run(rows, 1000.0)
        self.assertFalse(rows[1].amount_autocorrected)
        self.assertIs(rows[1].balance_ok, False)

    def test_unreliable_prev_not_fixed(self):
        # row0 自身就错(不可靠)→ row1 不修
        rows = [
            _row(dep=500, bal=9999),  # 1000+500≠9999 → balance_ok False
            _row(dep=250, bal=10299),
            _row(dep=200, bal=10499),
        ]
        _run(rows, 1000.0)
        self.assertFalse(rows[1].amount_autocorrected)

    def test_next_not_corroborating_not_fixed(self):
        # 本行余额没被下一行对上 → 不敢认本行余额 → 不修
        rows = [
            _row(dep=500, bal=1500),
            _row(dep=250, bal=1800),  # 真值 300 但…
            _row(dep=200, bal=5000),
        ]  # 1800+200≠5000 · 不佐证
        _run(rows, 1000.0)
        self.assertFalse(rows[1].amount_autocorrected)

    def test_correct_rows_untouched(self):
        rows = [_row(dep=500, bal=1500), _row(dep=300, bal=1800), _row(dep=200, bal=2000)]
        _run(rows, 1000.0)
        self.assertFalse(any(r.amount_autocorrected for r in rows))
        self.assertTrue(all(r.balance_ok is not False for r in rows))


if __name__ == "__main__":
    unittest.main()
