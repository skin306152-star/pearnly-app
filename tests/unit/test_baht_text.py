# -*- coding: utf-8 -*-
"""泰文金额大写守门(读法特例 เอ็ด/ยี่สิบ/สิบ · ล้าน 递归 · สตางค์ · 四舍五入)。"""

import unittest

from services.sales.baht_text import baht_text


class BahtTextTests(unittest.TestCase):
    def test_basic_amounts(self):
        self.assertEqual(baht_text(100), "หนึ่งร้อยบาทถ้วน")
        self.assertEqual(baht_text(0), "ศูนย์บาทถ้วน")

    def test_reading_specials(self):
        # 个位 1 读 เอ็ด(仅多位数)、十位 2 读 ยี่สิบ、十位 1 读 สิบ。
        self.assertEqual(baht_text(21), "ยี่สิบเอ็ดบาทถ้วน")
        self.assertEqual(baht_text(11), "สิบเอ็ดบาทถ้วน")
        self.assertEqual(baht_text(1), "หนึ่งบาทถ้วน")
        self.assertEqual(baht_text(20), "ยี่สิบบาทถ้วน")

    def test_satang(self):
        self.assertEqual(baht_text(1234.50), "หนึ่งพันสองร้อยสามสิบสี่บาทห้าสิบสตางค์")
        self.assertEqual(baht_text("0.25"), "ศูนย์บาทยี่สิบห้าสตางค์")

    def test_million_recursion(self):
        self.assertEqual(baht_text(1_000_000), "หนึ่งล้านบาทถ้วน")
        self.assertEqual(baht_text(2_500_000), "สองล้านห้าแสนบาทถ้วน")
        # ล้านล้าน(超 12 位)也读得出,不炸。
        self.assertEqual(baht_text(1_000_000_000_000), "หนึ่งล้านล้านบาทถ้วน")

    def test_rounding_half_up(self):
        # 0.005 → 0.01(ROUND_HALF_UP,与票面金额同规)。
        self.assertEqual(baht_text("0.005"), "ศูนย์บาทหนึ่งสตางค์")

    def test_prototype_sample(self):
        # 桌面原型 G2 示意的两个参考值(有/无折扣)。
        self.assertEqual(baht_text(1157), "หนึ่งพันหนึ่งร้อยห้าสิบเจ็ดบาทถ้วน")
        self.assertEqual(baht_text(1100), "หนึ่งพันหนึ่งร้อยบาทถ้วน")


if __name__ == "__main__":
    unittest.main()
