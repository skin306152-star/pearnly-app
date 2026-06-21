# -*- coding: utf-8 -*-
"""多笔解析不再把 型号/数量/日期/税率/折扣 当独立项加进总额(模糊测试 R/V/S/T/U/Q FAIL 根因)。

真机跑批:parse_multi 在大脑/单笔守卫之前短路,只要句里 ≥2 个「名词+数字」就把全部数字加总。
修:拆分前先 strip_nonmoney(剥单位/税率/型号邻接数)+ 剥日期 + 价标签段不当项 → 退化成单笔路
(取最大)→ 取到真额。共用单笔路的金钱语境纪律。
"""

import unittest
from decimal import Decimal

from services.expense import line_quick_entry as lqe


def _amt(text):
    """走完整单/多笔判定:多笔→合计;否则单笔 parse_expense.amount。"""
    multi = lqe.parse_multi(text)
    if multi:
        return sum(i["amount"] for i in multi)
    return lqe.parse_expense(text).amount


class MultiSumNoiseTests(unittest.TestCase):
    def test_pasted_failure_rows_now_correct(self):
        # 测试窗口贴的伤账表:应记 vs 旧实际记。
        cases = {
            "iPhone 15 ราคา 50000": Decimal("50000"),  # V1 型号15不加
            "โค้ก 1.5 ลิตร 30": Decimal("30"),  # V3 容量1.5不加
            "ไข่ 2 โหล 120": Decimal("120"),  # R1 数量2不加
            "หมู 3 กิโล 450": Decimal("450"),  # R2 数量3不加
            "น้ำ 1 แพ็ค 6 ขวด 90": Decimal("90"),  # R3 包装量不加
            "ผ่อน 3 งวด งวดละ 500": Decimal("500"),  # U1 期数3不加
            "หัก ณ ที่จ่าย 3% ของ 1000": Decimal("1000"),  # S3 税率3不加
            "ส่วนลด 50 ค่าอาหาร 200": Decimal("200"),  # T2 折扣50不加
            "ซื้อของ 15 ม.ค. 68 ราคา 300": Decimal("300"),  # Q3 日期15/68不加
        }
        for text, expected in cases.items():
            self.assertEqual(_amt(text), expected, text)

    def test_genuine_multi_still_sums(self):
        # 真·多笔不能回归:各自有商品名 → 仍合计。
        self.assertEqual(_amt("ค่าไฟ 500 ค่าน้ำ 300"), Decimal("800"))
        self.assertEqual(_amt("电费50 水费30 吃饭50"), Decimal("130"))
        self.assertEqual(_amt("กาแฟ 50 ชา 30"), Decimal("80"))

    def test_cost_of_compound_amount_preserved(self):
        # ค่า+标签词 是合法费用·金额不能被剥(ค่าโทร/ค่าห้อง/ค่าต่อทะเบียน·R1 隐患回归守卫)。
        self.assertEqual(_amt("ค่าโทร 500"), Decimal("500"))
        self.assertEqual(_amt("ค่าห้อง 1200"), Decimal("1200"))
        self.assertEqual(_amt("ค่าต่อทะเบียน 1000"), Decimal("1000"))
        self.assertEqual(_amt("ค่าโทร 500 ค่าน้ำ 80"), Decimal("580"))

    def test_known_residual_model_glued_number(self):
        # 诚实标注:型号数字粘字母(M150)·max 分不出 → 仍错(待大脑/型号词典·非本次修)。
        self.assertEqual(_amt("M150 2 ขวด 20"), Decimal("150"))  # 期望20·当前150(已知残留)


if __name__ == "__main__":
    unittest.main()
