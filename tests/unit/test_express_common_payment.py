# -*- coding: utf-8 -*-
"""现/赊判定单测(F2-F6 · services/erp/express_push/common.py::payment_verdict/payment_is_paid)。

六级漏斗优先级钉死:人工裁决(F5)> 票面显式付款字段 > 票种语义(F3)> 供应商过账档案(F4)
> 银行流水佐证(F6)> 无信号(留给各 mapper 的固定默认)。payment_verdict 额外留痕来源标签
供排障可查;bank_index 只加固已付,不命中不反证未付。
"""

from __future__ import annotations

import unittest

from services.erp.express_push.common import (
    SRC_BANK,
    SRC_DOC_TYPE,
    SRC_EXPLICIT,
    SRC_MANUAL,
    SRC_NONE,
    SRC_PROFILE,
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


class ManualOverrideTests(unittest.TestCase):
    """F5 · posting_payment_manual 最高优先级(压过票面显式字段/票种语义)。"""

    def test_manual_cash(self):
        self.assertEqual(
            payment_verdict({"posting_payment_manual": "cash", "payment_status": "unpaid"}),
            (True, SRC_MANUAL),
        )

    def test_manual_credit(self):
        self.assertEqual(
            payment_verdict({"posting_payment_manual": "credit", "document_type": "receipt"}),
            (False, SRC_MANUAL),
        )

    def test_manual_unrecognized_value_ignored(self):
        # 非 cash/credit 的脏值 → 不当人工信号,落回下一级判据。
        self.assertEqual(
            payment_verdict({"posting_payment_manual": "maybe", "document_type": "receipt"}),
            (True, SRC_DOC_TYPE),
        )


class ProfileTests(unittest.TestCase):
    """F4 · 供应商过账档案默认(profile.default_payment)· 无票面信号才生效。"""

    def test_profile_cash(self):
        self.assertEqual(
            payment_verdict({}, profile={"default_payment": "cash"}), (True, SRC_PROFILE)
        )

    def test_profile_credit(self):
        self.assertEqual(
            payment_verdict({}, profile={"default_payment": "credit"}), (False, SRC_PROFILE)
        )

    def test_explicit_field_beats_profile(self):
        self.assertEqual(
            payment_verdict({"payment_status": "unpaid"}, profile={"default_payment": "cash"}),
            (False, SRC_EXPLICIT),
        )

    def test_empty_profile_falls_through(self):
        self.assertEqual(payment_verdict({}, profile={}), (None, SRC_NONE))


class BankEvidenceTests(unittest.TestCase):
    """F6 · 银行流水佐证(bank_index)· 只加固已付,不命中不反证未付。"""

    def test_bank_match_returns_paid(self):
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "107.00"}]
        f = {"total_amount": "107.00", "date": "2026-07-03"}
        self.assertEqual(
            payment_verdict(f, bank_index=bank_index, direction="purchase"), (True, SRC_BANK)
        )

    def test_bank_match_via_kwargs_when_fields_lack_date_and_total(self):
        # 仓库惯例:history 顶层 invoice_date/total_amount 权威,fields 常无 date/total_amount
        # 两键 → 调用方传 kwargs;fields 全空也须命中(否则佐证静默死)。
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "107.00"}]
        self.assertEqual(
            payment_verdict(
                {},
                bank_index=bank_index,
                direction="purchase",
                invoice_date="2026-07-03",
                total="107.00",
            ),
            (True, SRC_BANK),
        )

    def test_bank_kwargs_take_precedence_over_fields(self):
        # kwargs 是调用方已解析的权威值,fields 的脏值不得盖过它。
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "107.00"}]
        f = {"total_amount": "999.99", "date": "2020-01-01"}
        self.assertEqual(
            payment_verdict(
                f,
                bank_index=bank_index,
                direction="purchase",
                invoice_date="2026-07-03",
                total="107.00",
            ),
            (True, SRC_BANK),
        )

    def test_bank_no_match_falls_through_to_none(self):
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "5.00"}]
        f = {"total_amount": "107.00", "date": "2026-07-03"}
        self.assertEqual(
            payment_verdict(f, bank_index=bank_index, direction="purchase"), (None, SRC_NONE)
        )

    def test_profile_beats_bank(self):
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "107.00"}]
        f = {"total_amount": "107.00", "date": "2026-07-03"}
        self.assertEqual(
            payment_verdict(
                f,
                profile={"default_payment": "credit"},
                bank_index=bank_index,
                direction="purchase",
            ),
            (False, SRC_PROFILE),
        )


class PriorityChainTests(unittest.TestCase):
    """六级判据全给齐时,只取最高优先级那层(manual > explicit > doc_type > profile > bank)。"""

    def test_manual_beats_everything(self):
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "107.00"}]
        f = {
            "posting_payment_manual": "credit",
            "payment_status": "paid",
            "document_type": "receipt",
            "total_amount": "107.00",
            "date": "2026-07-03",
        }
        self.assertEqual(
            payment_verdict(f, profile={"default_payment": "cash"}, bank_index=bank_index),
            (False, SRC_MANUAL),
        )

    def test_doc_type_beats_profile_and_bank(self):
        bank_index = [{"tx_date": "2026-07-01", "direction": "OUT", "amount": "107.00"}]
        f = {"document_type": "tax_invoice", "total_amount": "107.00", "date": "2026-07-03"}
        self.assertEqual(
            payment_verdict(f, profile={"default_payment": "cash"}, bank_index=bank_index),
            (False, SRC_DOC_TYPE),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
