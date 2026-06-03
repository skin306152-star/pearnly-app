# -*- coding: utf-8 -*-
"""
v118.35.0.50 · 守门测试 · 用余额涨跌自动纠正 OCR 借贷方向读反

真实案例(BBL 2697 / 2645 · 90° 旋转扫描图 · Gemini 把提款/存款列对错位):
  余额从 9,473,662 跌到 8,067,653(明明是提款),却被记成存款 1,406,008。
  金额跟余额涨跌完全吻合 · 仅方向放反 → 系统按余额摆正(明显列错位 · 非替用户判断)。

锁定契约:
  1. 金额吻合 |余额涨跌| 但方向相反 → 自动摆正 + direction_autocorrected=True · 余额验证转通过
  2. 金额对不上 |余额涨跌|(漏行/金额识别错)→ 不纠 · 仍标 balance_ok=False 让用户核对
  3. 续页首笔(opening 不可靠)→ 不纠(无上一行余额可比)
  4. 方向本来就对的行 → 不动 · 不打 direction_autocorrected
"""

import unittest
from datetime import date

from services.recon.bank_recon_v2 import (
    StatementRow,
    _correct_direction_from_balance,
    _verify_row_balances,
)


def _r(wd, dep, bal):
    return StatementRow(
        date=date(2025, 12, 30), description="x", withdrawal=wd, deposit=dep, balance=bal
    )


class DirectionCorrectTests(unittest.TestCase):

    def test_swap_corrected_when_amount_matches_delta(self):
        """余额跌但记成存款 · 金额吻合 → 摆正为提款 + 标记 · 余额验证转通过"""
        rows = [
            _r(0, 0, 10030351.95),  # 期初无动行(seed prev)
            _r(0, 1406008.89, 8624343.06),  # 余额跌 1,406,008.89 · 却记成存款 → 应纠成提款
        ]
        _correct_direction_from_balance(rows, 10030351.95)
        self.assertEqual(rows[1].withdrawal, 1406008.89)
        self.assertEqual(rows[1].deposit, 0.0)
        self.assertTrue(rows[1].direction_autocorrected)
        # 纠正后余额验证应通过
        _verify_row_balances(rows, 10030351.95)
        self.assertTrue(rows[1].balance_ok)

    def test_up_balance_recorded_as_withdrawal_corrected(self):
        """余额涨但记成提款 → 摆正为存款"""
        rows = [_r(0, 0, 1000.0), _r(500.0, 0, 1500.0)]  # 涨 500 却记提款
        _correct_direction_from_balance(rows, 1000.0)
        self.assertEqual(rows[1].deposit, 500.0)
        self.assertEqual(rows[1].withdrawal, 0.0)
        self.assertTrue(rows[1].direction_autocorrected)

    def test_amount_mismatch_not_corrected(self):
        """金额对不上余额涨跌(漏行/金额错)→ 不纠 · 仍标异常"""
        rows = [_r(0, 0, 1000.0), _r(0, 15.0, 1100.0)]  # 涨 100 却记存款 15(不吻合)
        _correct_direction_from_balance(rows, 1000.0)
        self.assertEqual(rows[1].deposit, 15.0)  # 未动
        self.assertFalse(rows[1].direction_autocorrected)
        _verify_row_balances(rows, 1000.0)
        self.assertFalse(rows[1].balance_ok)  # 仍标异常给用户核对

    def test_continuation_first_row_not_corrected(self):
        """续页首笔(opening=0 不可靠)· 无上一行余额可比 → 不纠"""
        rows = [_r(0, 713733.48, 9316618.47)]  # 续页首行
        _correct_direction_from_balance(rows, 0.0)
        self.assertFalse(rows[0].direction_autocorrected)

    def test_correct_direction_untouched(self):
        """方向本来就对 → 不动 · 不打标记"""
        rows = [_r(0, 0, 1000.0), _r(300.0, 0, 700.0)]  # 跌 300 记提款 · 正确
        _correct_direction_from_balance(rows, 1000.0)
        self.assertEqual(rows[1].withdrawal, 300.0)
        self.assertFalse(rows[1].direction_autocorrected)


if __name__ == "__main__":
    unittest.main()
