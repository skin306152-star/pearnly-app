# -*- coding: utf-8 -*-
"""P2C 明细名称展示清洗(services/purchase/item_name.py)。"""

import unittest

from services.purchase import item_name as inm


class CleanTests(unittest.TestCase):
    def test_garble_removed(self):
        self.assertEqual(inm.clean("?????"), "")
        self.assertEqual(inm.clean("��"), "")
        self.assertEqual(inm.clean("Cake ????"), "Cake")

    def test_pos_prefix_stripped(self):
        # Cafe Amazon:外带/SKU 噪声前缀剥除,只剩真品名(验收①)
        self.assertEqual(inm.clean("TW Latte"), "Latte")
        self.assertEqual(inm.clean("TW T- Espresso"), "Espresso")
        self.assertEqual(inm.clean("original Blend"), "Blend")
        self.assertEqual(inm.clean("TAKE AWAY ชาเย็น"), "ชาเย็น")

    def test_pos_prefix_glued_to_real_name_kept(self):
        # 分隔符守卫:噪声词后紧跟字母 = 真名一部分,不误伤
        self.assertEqual(inm.clean("TWG Tea"), "TWG Tea")
        self.assertEqual(inm.clean("T-Bone Steak"), "T-Bone Steak")
        self.assertEqual(inm.clean("Originality Set"), "Originality Set")

    def test_bare_prefix_plus_garble_becomes_empty(self):
        # 「TW ?????」剥乱码后仅剩前缀 → 空(不再裸露「TW」·验收①)
        self.assertEqual(inm.clean("TW ?????"), "")

    def test_bracket_noise(self):
        self.assertEqual(inm.clean("Latte (0%)"), "Latte")
        self.assertEqual(inm.clean("Coffee ( )"), "Coffee")
        self.assertEqual(inm.clean("ชา (ไม่หวาน)"), "ชา (ไม่หวาน)")

    def test_leading_bullets(self):
        self.assertEqual(inm.clean("- ไก่ทอด"), "ไก่ทอด")
        self.assertEqual(inm.clean("• Water"), "Water")

    def test_real_names_passthrough(self):
        self.assertEqual(inm.clean("ไก่ทอดเบตง"), "ไก่ทอดเบตง")
        self.assertEqual(inm.clean("Cake slice"), "Cake slice")


class UnclearTests(unittest.TestCase):
    def test_unclear(self):
        for raw in ("?????", "??", "��", "", "  ", "- ", "TW ?????", "TW", "ก"):
            self.assertTrue(inm.is_unclear(raw), raw)

    def test_clear(self):
        for raw in ("Latte", "ไก่ทอด", "TWG Tea", "Cake slice", "AB"):
            self.assertFalse(inm.is_unclear(raw), raw)


class DisplayTests(unittest.TestCase):
    def test_placeholder_for_unclear(self):
        self.assertEqual(inm.display("?????", 1, "รายการที่ {n}"), "รายการที่ 1")
        self.assertEqual(inm.display("TW ?????", 3, "Item {n}"), "Item 3")

    def test_cleaned_name_kept(self):
        self.assertEqual(inm.display("TW Latte", 1, "Item {n}"), "Latte")
        self.assertEqual(inm.display("ไก่ทอดเบตง", 2, "Item {n}"), "ไก่ทอดเบตง")


class CleanDocLinesTests(unittest.TestCase):
    def test_in_place_clean_and_flag(self):
        lines = [
            {"description": "TW Latte", "product_id": None},
            {"description": "?????", "product_id": None},
            {"description": "", "product_id": "p1"},  # 已配产品·无名 → 不误标
        ]
        inm.clean_doc_lines(lines)
        self.assertEqual(lines[0]["description"], "Latte")
        self.assertFalse(lines[0]["name_unclear"])
        self.assertEqual(lines[1]["description"], "")
        self.assertTrue(lines[1]["name_unclear"])
        self.assertEqual(lines[2]["description"], "")
        self.assertFalse(lines[2]["name_unclear"])

    def test_none_safe(self):
        inm.clean_doc_lines(None)
        inm.clean_doc_lines([])


if __name__ == "__main__":
    unittest.main()
