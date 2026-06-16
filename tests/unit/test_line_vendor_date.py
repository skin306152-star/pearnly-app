# -*- coding: utf-8 -*-
"""LINE 单笔路 卖家+相对日期 平价(#9)守门测试。

锁定:L1 parse_expense 也抽卖家(品牌字典 + 中文「在X买」)与相对日期(今天/昨天/前天/N天前),
与多笔 LLM 路对齐;无线索时卖家为空(不乱填)。"""

import unittest
from datetime import date, timedelta

from services.expense.line_quick_entry import _extract_vendor, parse_expense


def _d(n):
    return (date.today() - timedelta(days=n)).isoformat()


class VendorTests(unittest.TestCase):
    def test_brand_dict(self):
        self.assertEqual(_extract_vendor("昨天在星巴克买咖啡60"), "Starbucks")
        self.assertEqual(_extract_vendor("ที่เซเว่นซื้อน้ำ 20"), "7-Eleven")
        self.assertEqual(_extract_vendor("เติมน้ำมัน ปตท 1000"), "PTT")
        self.assertEqual(_extract_vendor("grab ไปสนามบิน 250"), "Grab")

    def test_zh_at_pattern(self):
        self.assertEqual(_extract_vendor("在小卖部买水10"), "小卖部")
        self.assertEqual(_extract_vendor("在楼下便利店花了35"), "楼下便利店")

    def test_no_cue_empty(self):
        self.assertEqual(_extract_vendor("ค่าน้ำ 50"), "")
        self.assertEqual(_extract_vendor("电费 800"), "")


class ParseExpenseParityTests(unittest.TestCase):
    def test_vendor_and_date_into_draft(self):
        d = parse_expense("昨天在星巴克买咖啡60")
        self.assertEqual(d.vendor_name, "Starbucks")
        self.assertEqual(d.doc_date, _d(1))
        self.assertEqual(str(d.amount), "60")

    def test_relative_dates(self):
        self.assertEqual(parse_expense("前天买菜50").doc_date, _d(2))
        self.assertEqual(parse_expense("3天前打车100").doc_date, _d(3))
        self.assertEqual(parse_expense("今天ค่าน้ำ50").doc_date, _d(0))

    def test_plain_no_vendor(self):
        d = parse_expense("ค่าไฟ 800")
        self.assertEqual(d.vendor_name, "")


if __name__ == "__main__":
    unittest.main()
