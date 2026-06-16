# -*- coding: utf-8 -*-
"""LINE 收入 vs 支出识别(#7)守门测试。

锁定:明确收入(收款/卖出)→ True(不误记为支出);任何带购买/付款动词的支出 → False
(保守·绝不误挡正常买东西)。"""

import unittest

from services.expense.line_quick_entry import detect_income


class IncomeDetectTests(unittest.TestCase):
    def test_clear_income_true(self):
        for t in [
            "收到货款500",
            "今天营业额3000",
            "ขายได้ 500 บาท",
            "卖了2杯咖啡共120",
            "received payment 1000",
            "รับเงินจากลูกค้า 800",
        ]:
            self.assertTrue(detect_income(t), f"应判收入: {t}")

    def test_expense_never_blocked(self):
        # 有购买/付款动词 → 必 False(防误挡支出)
        for t in [
            "买咖啡60",
            "ซื้อกาแฟ 60",
            "จ่ายค่าน้ำ 50",
            "花了50买菜",
            "paid 300 for lunch",
            "bought water 10",
            "ขายของแต่ซื้อวัตถุดิบ 300",  # 同时含 ขาย 和 ซื้อ → 让位给支出
        ]:
            self.assertFalse(detect_income(t), f"不应误判收入: {t}")

    def test_plain_expense_no_income_marker_false(self):
        # 无收入词的普通支出 → False(走正常记账)
        for t in ["ค่าน้ำ 50", "电费 50", "Water 50", "ทุเรียน 300"]:
            self.assertFalse(detect_income(t), f"无收入词不该判收入: {t}")


if __name__ == "__main__":
    unittest.main()
