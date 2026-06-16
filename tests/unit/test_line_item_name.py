# -*- coding: utf-8 -*-
"""LINE 单笔「详情」结构化(#10b)守门测试。

锁定:_extract_item_name 从一句话清出干净物品名(去 日期/金额/数量/币种/卖家/动词);
parse_expense.note = 干净物品名(供详情结构化 + 入账行描述),清不出回落原文。"""

import unittest

from services.expense.line_quick_entry import _extract_item_name, parse_expense


class ItemNameTests(unittest.TestCase):
    def test_clean_common(self):
        self.assertEqual(_extract_item_name("买咖啡60"), "咖啡")
        self.assertEqual(_extract_item_name("买2杯咖啡共120"), "咖啡")
        self.assertEqual(_extract_item_name("ค่าน้ำ 50"), "ค่าน้ำ")  # 「ค่า」保留(费用名)
        self.assertEqual(_extract_item_name("จ่ายค่าไฟ 800"), "ค่าไฟ")

    def test_strips_vendor_date_verb(self):
        # 昨天/星巴克/ดื่ม/金额 都去掉,主物品保留
        out = _extract_item_name("เมื่อวานดื่มน้ำแร่ 30 ที่สตาร์บัคส์ในห้าง")
        self.assertIn("น้ำแร่", out)
        self.assertNotIn("30", out)
        self.assertNotIn("สตาร์บัคส์", out)
        self.assertNotIn("ดื่ม", out)

    def test_parse_expense_note_is_clean_item(self):
        d = parse_expense("昨天在星巴克买咖啡60")
        self.assertEqual(d.note, "咖啡")  # 详情 = 干净物品名,不再整句
        self.assertEqual(d.raw_text, "昨天在星巴克买咖啡60")  # 原文留底


if __name__ == "__main__":
    unittest.main()
