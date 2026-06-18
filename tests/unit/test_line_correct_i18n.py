# -*- coding: utf-8 -*-
"""采购改错澄清文案(line_correct_i18n · P1E-2):4 语齐全 + 占位渲染。"""

import unittest

from services.expense import line_correct_i18n as ci

_LANGS = ("zh", "th", "en", "ja")


class CorrectI18nTests(unittest.TestCase):
    def test_pools_four_langs(self):
        for pool in (ci.CLARIFY_FIELDS, ci.ASK_VALUE, ci.DETAIL_INCOMPLETE):
            for lg in _LANGS:
                self.assertTrue(pool.get(lg), f"missing {lg}")

    def test_field_labels_four_langs(self):
        for field in ("amount", "date", "seller", "category", "payment"):
            for lg in _LANGS:
                self.assertTrue(ci.field_label(field, lg))

    def test_payment_field_key_maps_to_payment_method(self):
        self.assertEqual(ci.FIELD_TO_KEY["payment"], "payment_method")
        self.assertEqual(ci.key_label("payment_method", "zh"), "付款方式")

    def test_pay_label_localizes_code(self):
        # 付款方式码 → 人话(复用卡片同口径);未知码原样保留不丢信息。
        self.assertEqual(ci.pay_label("cash", "zh"), "现金")
        self.assertEqual(ci.pay_label("promptpay", "en"), "PromptPay")
        self.assertEqual(ci.pay_label("เก็บปลายทาง", "th"), "เก็บปลายทาง")

    def test_disp_only_localizes_payment(self):
        self.assertEqual(ci.disp("payment_method", "cash", "zh"), "现金")
        self.assertEqual(ci.disp("vendor_name", "7-11", "zh"), "7-11")

    def test_ask_value_interpolates_field(self):
        body = ci.t(ci.ASK_VALUE, "zh", field=ci.field_label("seller", "zh"))
        self.assertIn("卖家", body)
        self.assertNotIn("{field}", body)

    def test_t_falls_back_to_zh(self):
        self.assertEqual(ci.t(ci.CLARIFY_FIELDS, "xx"), ci.CLARIFY_FIELDS["zh"])


if __name__ == "__main__":
    unittest.main()
