# -*- coding: utf-8 -*-
"""置信分级判定(docs/smart-intake/15 §1)。

锁:高置信齐全 → post;缺字段/低置信 → confirm;无金额/方向不明 → inbox;重复 → confirm+dup。
"""

import unittest

from services.expense.confidence import grade


class GradeTests(unittest.TestCase):
    def _full(self, **over):
        base = dict(
            amount="190.00",
            vendor_name="ACME",
            invoice_number="INV-1",
            document_type="tax_invoice",
            direction="purchase",
            confidence_band="high",
            has_category=True,
            is_duplicate=False,
        )
        base.update(over)
        return grade(**base)

    def test_high_and_complete_posts(self):
        v = self._full()
        self.assertEqual(v.action, "post")
        self.assertFalse(v.dup)

    def test_receipt_without_invoice_no_still_posts(self):
        # 收据不强制发票号 → 齐全即 post。
        v = self._full(document_type="receipt", invoice_number="")
        self.assertEqual(v.action, "post")

    def test_tax_invoice_missing_no_confirms(self):
        v = self._full(invoice_number="")
        self.assertEqual(v.action, "confirm")
        self.assertIn("invoice_no_missing", v.reasons)

    def test_low_band_confirms(self):
        v = self._full(confidence_band="needs_review")
        self.assertEqual(v.action, "confirm")
        self.assertIn("low_confidence_band", v.reasons)

    def test_no_category_confirms(self):
        v = self._full(has_category=False)
        self.assertEqual(v.action, "confirm")

    def test_zero_amount_to_inbox(self):
        v = self._full(amount="0")
        self.assertEqual(v.action, "inbox")

    def test_missing_amount_to_inbox(self):
        self.assertEqual(self._full(amount=None).action, "inbox")
        self.assertEqual(self._full(amount="").action, "inbox")

    def test_sales_direction_to_inbox(self):
        v = self._full(direction="sales")
        self.assertEqual(v.action, "inbox")

    def test_duplicate_confirms_and_flags(self):
        v = self._full(is_duplicate=True)
        self.assertEqual(v.action, "confirm")
        self.assertTrue(v.dup)

    def test_amount_with_comma(self):
        self.assertEqual(self._full(amount="2,722.00").action, "post")

    def test_casual_text_no_vendor_no_doctype_posts(self):
        # 文字记账「ค่าน้ำ 50」无卖家、无单据类型 → 仍可 post(卖家只对正式票据要求)。
        v = grade(
            amount="50",
            vendor_name="",
            invoice_number="",
            document_type="",
            direction="expense",
            confidence_band="high",
            has_category=True,
            is_duplicate=False,
        )
        self.assertEqual(v.action, "post")

    def test_formal_receipt_no_vendor_confirms(self):
        v = self._full(document_type="receipt", vendor_name="", invoice_number="")
        self.assertEqual(v.action, "confirm")
        self.assertIn("vendor_missing", v.reasons)


if __name__ == "__main__":
    unittest.main()
