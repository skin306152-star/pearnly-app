# -*- coding: utf-8 -*-

import unittest

from services.expense import amount_extract
from tests.unit.test_line_expense_thai_nonassertive import _run


class NonMoneyNoiseTests(unittest.TestCase):
    def test_repeated_thai_age_marker_is_not_amount(self):
        self.assertIsNone(amount_extract.extract_amount("อาายุ 25 ปี", None, None))
        out, calls = _run("อาายุ 25 ปี")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])

    def test_repeated_thai_minute_marker_is_not_amount(self):
        self.assertIsNone(amount_extract.extract_amount("รอ 15 นาาที", None, None))
        out, calls = _run("รอ 15 นาาที")
        self.assertTrue(out)
        self.assertEqual(calls["record"], [])

    def test_food_drink_quantity_units_are_not_amount(self):
        # 餐饮量词后的数字=份数不是钱(治「3 แก้ว」被当 ฿3 记账·大脑无关)。
        for text in ("กาแฟ 3 แก้ว", "ข้าว 3 จาน", "ก๋วยเตี๋ยว 2 ชาม", "น้ำ 2 ถ้วย"):
            self.assertIsNone(amount_extract.extract_amount(text, None, None), text)
            self.assertEqual(amount_extract.money_numbers(text), [], text)

    def test_amount_with_currency_survives_quantity_unit(self):
        # 有币种标记时正常取价,量词不误伤(「กาแฟ 3 แก้ว 120 บาท」→ 120)。
        self.assertEqual(amount_extract.extract_amount("กาแฟ 3 แก้ว 120 บาท", None, None), 120)


if __name__ == "__main__":
    unittest.main()
