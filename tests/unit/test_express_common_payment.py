# -*- coding: utf-8 -*-
"""现/赊判定单测(F3 · services/erp/express_push/common.py::payment_verdict/payment_is_paid)。

优先级钉死:票面显式付款字段(payment_status/method)> 票种语义(收据在场=已付,仅税票=赊)
> 无信号(留给各 mapper 的固定默认)。payment_verdict 额外留痕来源标签供排障可查。
"""

from __future__ import annotations

import unittest

from services.erp.express_push.common import (
    SRC_DOC_TYPE,
    SRC_EXPLICIT,
    SRC_NONE,
    payment_is_paid,
    payment_verdict,
)


class PaymentIsPaidTests(unittest.TestCase):
    def test_explicit_status_overrides_doc_type(self):
        # receipt 票种语义本应 True,但显式 unpaid 优先生效。
        f = {"document_type": "receipt", "payment_status": "unpaid"}
        self.assertFalse(payment_is_paid(f))

    def test_explicit_method_overrides_doc_type(self):
        # tax_invoice 票种语义本应 False,但显式付款方式(转账)优先生效。
        f = {"document_type": "tax_invoice", "payment_method": "โอนเงิน transfer"}
        self.assertTrue(payment_is_paid(f))

    def test_receipt_without_explicit_field_is_paid(self):
        self.assertTrue(payment_is_paid({"document_type": "receipt"}))

    def test_simplified_tax_invoice_without_explicit_field_is_paid(self):
        self.assertTrue(payment_is_paid({"document_type": "simplified_tax_invoice"}))

    def test_tax_invoice_without_explicit_field_is_unpaid(self):
        self.assertFalse(payment_is_paid({"document_type": "tax_invoice"}))

    def test_credit_note_without_explicit_field_is_unpaid(self):
        self.assertFalse(payment_is_paid({"document_type": "credit_note"}))

    def test_no_signal_at_all_returns_none(self):
        self.assertIsNone(payment_is_paid({}))
        self.assertIsNone(payment_is_paid({"document_type": "payment_evidence"}))


class PaymentVerdictSourceTests(unittest.TestCase):
    def test_explicit_status_labeled(self):
        self.assertEqual(
            payment_verdict({"document_type": "receipt", "payment_status": "paid"}),
            (True, SRC_EXPLICIT),
        )

    def test_explicit_method_labeled(self):
        self.assertEqual(payment_verdict({"payment_method": "cash เงินสด"}), (True, SRC_EXPLICIT))

    def test_doc_type_labeled(self):
        self.assertEqual(payment_verdict({"document_type": "receipt"}), (True, SRC_DOC_TYPE))
        self.assertEqual(payment_verdict({"document_type": "tax_invoice"}), (False, SRC_DOC_TYPE))

    def test_none_labeled(self):
        self.assertEqual(payment_verdict({}), (None, SRC_NONE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
