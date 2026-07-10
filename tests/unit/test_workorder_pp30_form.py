# -*- coding: utf-8 -*-
"""ภ.พ.30 全字段契约测试(services/workorder/steps/pp30_form.py)。

纯函数,不碰库/OCR。覆盖:真客户 Sister Makeup 官方申报逐字段(T0 语料盘点 §二);派生字段
(应税销售额、应缴、净应缴、合计)算对;本期无数据源字段诚实置 0 且标注来源;留抵(进项>销项)
方向的应缴/超缴/净应缴符号正确。
"""

import unittest
from decimal import Decimal

from services.workorder.steps import pp30_form

# 官方申报数(T0 语料盘点 §二,读自 ภ.พ.30 电子签收原件,锁定不许改)。
GOLDEN_SALES = "858780.16"
GOLDEN_OUTPUT_VAT = "60114.61"
GOLDEN_PURCHASE = "418046.86"
GOLDEN_INPUT_VAT = "29263.28"
GOLDEN_NET_TAX_DUE = "30851.33"


class Ppp30GoldenFieldsTests(unittest.TestCase):
    def setUp(self):
        self.form = pp30_form.build(
            sales_amount=GOLDEN_SALES,
            output_vat=GOLDEN_OUTPUT_VAT,
            purchase_amount=GOLDEN_PURCHASE,
            input_vat=GOLDEN_INPUT_VAT,
        )
        self.amounts = pp30_form.amounts(self.form)

    def test_all_official_fields_match_declared_return(self):
        expected = {
            "sales_total": GOLDEN_SALES,
            "sales_zero_rated": "0",
            "sales_exempt": "0",
            "sales_taxable": GOLDEN_SALES,
            "output_vat": GOLDEN_OUTPUT_VAT,
            "purchase_creditable": GOLDEN_PURCHASE,
            "input_vat": GOLDEN_INPUT_VAT,
            "tax_payable": GOLDEN_NET_TAX_DUE,
            "tax_overpaid": "0",
            "prior_credit": "0",
            "net_tax_due": GOLDEN_NET_TAX_DUE,
            "surcharge": "0",
            "penalty": "0",
            "total_payable": GOLDEN_NET_TAX_DUE,
        }
        self.assertEqual(self.amounts, expected)
        for key, val in expected.items():
            self.assertEqual(Decimal(self.amounts[key]), Decimal(val), key)

    def test_net_tax_due_equals_output_minus_input(self):
        self.assertEqual(
            self.form["net_tax_due"], str(Decimal(GOLDEN_OUTPUT_VAT) - Decimal(GOLDEN_INPUT_VAT))
        )

    def test_no_source_fields_flagged_honestly_not_fabricated(self):
        by_key = {f["key"]: f for f in self.form["fields"]}
        for key in ("sales_zero_rated", "sales_exempt", "prior_credit", "surcharge", "penalty"):
            self.assertEqual(by_key[key]["source"], pp30_form.SRC_NO_SOURCE_M1, key)
            self.assertEqual(Decimal(by_key[key]["amount"]), Decimal("0"), key)

    def test_line_numbers_and_labels_present(self):
        by_key = {f["key"]: f for f in self.form["fields"]}
        self.assertEqual(by_key["purchase_creditable"]["line"], "6")
        self.assertEqual(by_key["input_vat"]["line"], "7")
        self.assertIn("ภาษีซื้อ", by_key["input_vat"]["label_th"])


class Ppp30CreditCarryDirectionTests(unittest.TestCase):
    """进项 > 销项(留抵)时:应缴=0、超缴=正、净应缴=负、合计=0——符号诚实不 clamp 错向。"""

    def test_input_exceeds_output_reports_overpaid_and_negative_net(self):
        form = pp30_form.build(
            sales_amount="1000.00",
            output_vat="70.00",
            purchase_amount="7142.86",
            input_vat="500.00",
        )
        amounts = pp30_form.amounts(form)
        self.assertEqual(Decimal(amounts["tax_payable"]), Decimal("0"))
        self.assertEqual(Decimal(amounts["tax_overpaid"]), Decimal("430.00"))
        self.assertEqual(Decimal(amounts["net_tax_due"]), Decimal("-430.00"))
        self.assertEqual(Decimal(amounts["total_payable"]), Decimal("0"))


if __name__ == "__main__":
    unittest.main()
