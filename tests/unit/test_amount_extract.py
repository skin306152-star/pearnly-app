# -*- coding: utf-8 -*-
"""金额抽取的非金额数字剥离(模糊测试 NO_RECORD FAIL 115 的根因修复)。

真机跑批(brain OFF)实测:车牌/年份/房号/年龄/时长/时间/折扣/人数 + 负数 + 笑声555 全被 L1
当总额误记。根因 = 旧 _extract_amount「取最大裸数」无金钱语境判断。修 = strip_nonmoney 按
单位/标签/时间/百分比/负号剥离 + 多数字时丢 5{3,} 笑声。
"""

import unittest
from decimal import Decimal

from services.expense import amount_extract as ae


def _amt(text):
    return ae.extract_amount(text, None, None)


class NonMoneyNumberTests(unittest.TestCase):
    def test_noise_numbers_not_amount(self):
        # 跑批 NO_RECORD FAIL 主类:这些数字都不是钱 → 抽不出金额。
        cases = [
            "ทะเบียน กข 1234",  # 车牌
            "ป้ายทะเบียน 103",  # 车牌(ป้าย 前缀粘连·不被 ค่า 保护误放行)
            "ปี 2567",  # 佛历年
            "ห้อง 305",  # 房号
            "อายุ 25 ปี",  # 年龄
            "รอ 15 นาที",  # 时长
            "เวลา 14:30",  # 时间
            "ส่วนลด 10%",  # 折扣百分比
            "มีลูก 2 คน",  # 人数
            "ยื่น ภพ30 แล้วยัง",  # 税表名+数字
            "โทร 0812345678",  # 电话(旧逻辑已挡·确认不回归)
        ]
        for t in cases:
            self.assertIsNone(_amt(t), t)

    def test_negative_not_amount(self):
        self.assertIsNone(_amt("กาแฟ -50"))  # 负数不记

    def test_laughter_555_not_amount_when_other_number(self):
        self.assertEqual(_amt("กาแฟ 50 555"), Decimal("50"))  # 555 是笑声·真额 50

    def test_real_amounts_survive(self):
        # 守卫不误伤真记账。
        self.assertEqual(_amt("กาแฟ 65"), Decimal("65"))
        self.assertEqual(_amt("ค่าไฟ 500 บาท"), Decimal("500"))
        self.assertEqual(_amt("จ่าย 1,250.5"), Decimal("1250.5"))
        self.assertEqual(_amt("打车 50"), Decimal("50"))

    def test_single_555_is_amount(self):
        # 「ค่าไฟ 555」单数字 → 555 是真额(不当笑声丢)。
        self.assertEqual(_amt("ค่าไฟ 555"), Decimal("555"))

    def test_qty_unit_price_product(self):
        self.assertEqual(
            ae.extract_amount("买2杯共120", Decimal("2"), Decimal("60")), Decimal("120")
        )


class MoneyNumbersTests(unittest.TestCase):
    def test_money_numbers_excludes_noise(self):
        self.assertEqual(ae.money_numbers("ห้อง 305"), [])  # 房号不是钱
        self.assertEqual(ae.money_numbers("อายุ 25 ปี"), [])
        self.assertIn(Decimal("150"), ae.money_numbers("ค่าอาหาร 150 บาท"))

    def test_money_numbers_keeps_real(self):
        self.assertEqual(ae.money_numbers("กาแฟ 65"), [Decimal("65")])


if __name__ == "__main__":
    unittest.main()
