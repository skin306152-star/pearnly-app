# -*- coding: utf-8 -*-
"""手动改额「以票面为准」合计校验(totals.override_totals · 阶段一)。

票面是法定真值:override 用票面的 小计/折扣/VAT/合计,后端校验自洽(±0.01)、
rounding 反算吸收余项保证 含税合计 = (净) + VAT + rounding 恒等(过账借贷必平);
WHT 不随 override 改、仍按行权威计。纯函数,不连库。
"""

import unittest
from decimal import Decimal

from services.purchase.totals import override_totals


def _lines(unit_price, vat_rate=7, vat_applicable=True, wht_rate=0):
    return [
        {
            "description": "x",
            "qty": 1,
            "unit_price": unit_price,
            "vat_rate": vat_rate,
            "vat_applicable": vat_applicable,
            "wht_rate": wht_rate,
        }
    ]


class OverrideTotalsTests(unittest.TestCase):
    def test_aligns_doc_totals_to_invoice_face(self):
        # 行算 102.79 → 含税 109.99;票面印 102.80 / VAT 7.20 / 合计 110.00。
        ov = {
            "override_on": True,
            "subtotal": "102.80",
            "discount_total": "0",
            "vat_amount": "7.20",
            "grand_total": "110.00",
        }
        calc, ok = override_totals(_lines("102.79"), override=ov)
        self.assertTrue(ok)
        self.assertEqual(calc["subtotal"], Decimal("102.80"))
        self.assertEqual(calc["vat_amount"], Decimal("7.20"))
        self.assertEqual(calc["grand_total"], Decimal("110.00"))
        self.assertEqual(calc["rounding"], Decimal("0.00"))
        self.assertEqual(calc["net_payable"], Decimal("110.00"))

    def test_balance_identity_holds_after_override(self):
        # 借贷平前提:含税合计 == (小计 − 折扣) + VAT + rounding(过账走 doc 级金额)。
        ov = {
            "override_on": True,
            "subtotal": "1000.00",
            "discount_total": "50.00",
            "vat_amount": "66.50",
            "grand_total": "1016.50",
        }
        calc, ok = override_totals(_lines("900"), override=ov)
        self.assertTrue(ok)
        base = calc["subtotal"] - calc["discount_total"]
        self.assertEqual(base + calc["vat_amount"] + calc["rounding"], calc["grand_total"])

    def test_rounding_noise_within_tolerance_absorbed(self):
        # 票面 ±0.01 凑整噪声 → 接受,rounding 吸收。
        ov = {
            "override_on": True,
            "subtotal": "102.80",
            "discount_total": "0",
            "vat_amount": "7.20",
            "grand_total": "110.01",
        }
        calc, ok = override_totals(_lines("102.79"), override=ov)
        self.assertTrue(ok)
        self.assertEqual(calc["rounding"], Decimal("0.01"))
        self.assertEqual(calc["grand_total"], Decimal("110.01"))

    def test_inconsistent_face_rejected(self):
        # 合计与 净+VAT 差 > 0.01(110 vs 115)→ ok=False,返回行算原值不污染。
        ov = {
            "override_on": True,
            "subtotal": "102.80",
            "discount_total": "0",
            "vat_amount": "7.20",
            "grand_total": "115.00",
        }
        calc, ok = override_totals(_lines("102.79"), override=ov)
        self.assertFalse(ok)
        self.assertEqual(calc["grand_total"], Decimal("109.99"))  # 行算原值

    def test_wht_kept_from_lines_not_override(self):
        # WHT 不在 override 字段集:按行 wht_rate=3 计,net_payable = 合计 − WHT。
        ov = {
            "override_on": True,
            "subtotal": "1000.00",
            "discount_total": "0",
            "vat_amount": "70.00",
            "grand_total": "1070.00",
        }
        calc, ok = override_totals(_lines("1000", wht_rate=3), override=ov)
        self.assertTrue(ok)
        self.assertEqual(calc["wht_amount"], Decimal("30.00"))
        self.assertEqual(calc["net_payable"], Decimal("1040.00"))

    def test_missing_override_fields_fall_back_to_line_calc(self):
        # 只给 override_on 不给数 → 退回行算值(等价无 override)。
        calc, ok = override_totals(_lines("100"), override={"override_on": True})
        self.assertTrue(ok)
        self.assertEqual(calc["subtotal"], Decimal("100.00"))
        self.assertEqual(calc["vat_amount"], Decimal("7.00"))


if __name__ == "__main__":
    unittest.main()
