# -*- coding: utf-8 -*-
"""
tests/test_validators_6091.py

Regression lock for the 6091 case described in the 2026-05-21 multi-schema
refactor: a GL document with '6091' appearing in the Description column
must NEVER have that number assigned to debit/credit/amount/balance.

If this test starts failing, the validators in services/ocr/validators.py
are no longer catching mis-sourced amounts — the bug is back.
"""

import unittest

from services.ocr.schemas import (
    BankStatementDocument,
    BankStatementEntry,
    FieldRef,
    GLEntry,
    GeneralLedgerDocument,
    Page,
    ThaiInvoice,
)
from services.ocr.validators import (
    validate_bank_document,
    validate_gl_document,
    validate_invoice,
)


def _empty_page():
    return Page(
        page_number=1,
        width=0,
        height=0,
        full_text="",
        avg_confidence=1.0,
        blocks=[],
    )


class GLDescription6091RegressionTests(unittest.TestCase):
    """The motivating bug: '6091' in description column being parsed as amount."""

    def test_6091_in_description_with_legit_amounts_from_debit_credit_passes_clean(self):
        entry = GLEntry(
            transaction_date="2026-05-21",
            voucher_no="JV681130.1",
            account_code="1112-07",
            description="6091 - Sales revenue Bangkok",
            debit="1500.00",
            credit="",
            amount="1500.00",
            direction="deposit",
            debit_ref=FieldRef(value="1500.00", source_column="Debit", source_text="1,500.00"),
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertEqual(
            warnings, [], f"clean GL row with 6091 in desc should pass — got {warnings}"
        )
        # Original fields untouched
        self.assertEqual(entry.debit, "1500.00")
        self.assertEqual(entry.amount, "1500.00")

    def test_6091_mis_sourced_from_description_column_is_rejected_and_cleared(self):
        entry = GLEntry(
            transaction_date="2026-05-21",
            voucher_no="JV681130.1",
            description="6091 - Sales revenue",
            debit="6091.00",  # WRONG — same number as description
            credit="",
            amount="6091.00",
            direction="deposit",
            debit_ref=FieldRef(value="6091.00", source_column="Description"),  # gives it away
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertEqual(len(warnings), 1, f"expected 1 warning, got {warnings}")
        self.assertIn("description column", warnings[0])
        # And the bad value was cleared so downstream doesn't use it
        self.assertEqual(entry.debit, "")
        self.assertEqual(entry.amount, "")
        self.assertEqual(entry.direction, "")

    def test_amount_from_voucher_number_column_is_rejected(self):
        entry = GLEntry(
            voucher_no="JV681130.1",
            description="Sales",
            debit="681130.1",
            debit_ref=FieldRef(value="681130.1", source_column="Voucher No."),
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertEqual(len(warnings), 1)
        self.assertIn("voucher-number column", warnings[0])
        self.assertEqual(entry.debit, "")

    def test_amount_from_account_code_column_is_rejected(self):
        entry = GLEntry(
            account_code="1112-07",
            description="Cash",
            debit="111207",
            debit_ref=FieldRef(value="111207", source_column="Account Code"),
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertEqual(len(warnings), 1)
        self.assertIn("account-code column", warnings[0])
        self.assertEqual(entry.debit, "")

    def test_thai_description_column_label_rejected(self):
        entry = GLEntry(
            description="6091",
            debit="6091.00",
            debit_ref=FieldRef(value="6091.00", source_column="รายการ"),
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertEqual(len(warnings), 1)
        self.assertEqual(entry.debit, "")

    def test_both_debit_and_credit_nonzero_flagged(self):
        entry = GLEntry(
            voucher_no="V1",
            debit="100.00",
            credit="50.00",
            debit_ref=FieldRef(value="100.00", source_column="Debit"),
            credit_ref=FieldRef(value="50.00", source_column="Credit"),
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        msgs = " ".join(warnings)
        self.assertIn("both debit", msgs.lower())

    def test_direction_deposit_requires_debit(self):
        entry = GLEntry(
            voucher_no="V2",
            debit="",
            credit="500.00",
            direction="deposit",
            credit_ref=FieldRef(value="500.00", source_column="Credit"),
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertTrue(any("direction=deposit" in w for w in warnings))

    def test_no_ref_means_no_source_check(self):
        # When Gemini didn't fill *_ref (legacy / older response), validators
        # should not crash and not spuriously reject.
        entry = GLEntry(
            voucher_no="V3",
            description="some text 6091",
            debit="1500.00",
            credit="",
            direction="deposit",
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        # 6091 doesn't appear in description as a standalone token here
        self.assertEqual(warnings, [])

    def test_description_token_leak_detected_without_ref(self):
        # Even without source_refs, the description-token-leak heuristic
        # should warn when an amount value matches a bare token in description.
        entry = GLEntry(
            voucher_no="V4",
            description="6091",  # bare token
            debit="6091.00",
            direction="deposit",
        )
        doc = GeneralLedgerDocument(entries=[entry])
        warnings = validate_gl_document(doc, _empty_page())
        self.assertTrue(
            any("description" in w for w in warnings),
            f"expected description-leak warning, got {warnings}",
        )


class BankStatementValidatorTests(unittest.TestCase):

    def test_clean_bank_row_passes(self):
        entry = BankStatementEntry(
            transaction_date="2026-05-21",
            description="ATM withdrawal Sukhumvit",
            reference="TXN-100200",
            deposit="",
            withdrawal="500.00",
            amount="500.00",
            direction="withdrawal",
            balance="9500.00",
            withdrawal_ref=FieldRef(value="500.00", source_column="Withdrawal"),
            balance_ref=FieldRef(value="9500.00", source_column="Balance"),
        )
        doc = BankStatementDocument(entries=[entry])
        warnings = validate_bank_document(doc, _empty_page())
        self.assertEqual(warnings, [])

    def test_amount_from_reference_column_rejected(self):
        entry = BankStatementEntry(
            description="ATM",
            reference="TXN-100200",
            withdrawal="100200",
            withdrawal_ref=FieldRef(value="100200", source_column="Reference"),
        )
        doc = BankStatementDocument(entries=[entry])
        warnings = validate_bank_document(doc, _empty_page())
        self.assertEqual(len(warnings), 1)
        self.assertIn(
            "voucher-number column", warnings[0]
        )  # Reference falls under voucher-keyword set
        self.assertEqual(entry.withdrawal, "")

    def test_deposit_from_description_column_rejected(self):
        entry = BankStatementEntry(
            description="6091",
            deposit="6091",
            deposit_ref=FieldRef(value="6091", source_column="Description"),
        )
        doc = BankStatementDocument(entries=[entry])
        warnings = validate_bank_document(doc, _empty_page())
        self.assertEqual(len(warnings), 1)
        self.assertEqual(entry.deposit, "")


class InvoiceValidatorSourceColumnTests(unittest.TestCase):

    def test_invoice_amount_from_description_rejected(self):
        inv = ThaiInvoice(
            total_amount="6091.00",
            source_refs={
                "total_amount": FieldRef(value="6091.00", source_column="Description"),
            },
        )
        warnings = validate_invoice(inv, _empty_page())
        self.assertEqual(len(warnings), 1)
        self.assertIn("description column", warnings[0])


if __name__ == "__main__":
    unittest.main()
