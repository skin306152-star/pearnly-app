# -*- coding: utf-8 -*-
"""R1-R9 规则模板单测(docs/accounting/02 · 每模板 ≥1 例 + 借贷平 + 反解一致)。"""

import unittest
from decimal import Decimal

from services.accounting import rules


def _sum(entries, dr_cr):
    return sum((e["amount"] for e in entries if e["dr_cr"] == dr_cr), Decimal("0"))


def _by_role(entries, role, dr_cr=None):
    return [e for e in entries if e["role"] == role and (dr_cr is None or e["dr_cr"] == dr_cr)]


def _purchase_ctx(**over):
    ctx = {
        "source_type": "purchase",
        "source_tier": "first_party",
        "doc_kind": "purchase_invoice",
        "amounts": {
            "grand_total": Decimal("1070.00"),
            "vat_amount": Decimal("70.00"),
            "wht_amount": Decimal("0.00"),
        },
        "lines": [
            {
                "item_type": "goods",
                "product_id": "p1",
                "line_total": Decimal("1000.00"),
                "category_id": None,
                "description": "สินค้า",
            }
        ],
        "ref": "进项单 X",
        "scope_keys": [],
    }
    ctx.update(over)
    return ctx


class PurchaseRulesTests(unittest.TestCase):
    def test_r1_goods_invoice_balanced(self):
        r = rules.build(_purchase_ctx())
        self.assertEqual(r["rule_key"], "R1")
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(
            _by_role(r["entries"], "inventory", "debit")[0]["amount"], Decimal("1000.00")
        )
        self.assertEqual(
            _by_role(r["entries"], "input_vat", "debit")[0]["amount"], Decimal("70.00")
        )
        self.assertEqual(_by_role(r["entries"], "ap", "credit")[0]["amount"], Decimal("1070.00"))
        self.assertEqual(r["uncertainties"], [])

    def test_r1_unmatched_goods_line_goes_expense(self):
        ctx = _purchase_ctx(
            lines=[
                {
                    "item_type": "goods",
                    "product_id": None,
                    "line_total": Decimal("1000.00"),
                    "category_id": None,
                    "description": "x",
                }
            ]
        )
        r = rules.build(ctx)
        self.assertEqual(_by_role(r["entries"], "inventory"), [])
        self.assertEqual(
            _by_role(r["entries"], "expense_default", "debit")[0]["amount"], Decimal("1000.00")
        )

    def test_r1_doc_discount_folds_into_biggest_debit(self):
        # subtotal 1000 整单折扣 100 → base 900 + vat 70 = grand 970;借方并折扣进库存桶
        ctx = _purchase_ctx(
            amounts={
                "grand_total": Decimal("970.00"),
                "vat_amount": Decimal("70.00"),
                "wht_amount": Decimal("0.00"),
            }
        )
        r = rules.build(ctx)
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(
            _by_role(r["entries"], "inventory", "debit")[0]["amount"], Decimal("900.00")
        )

    def test_r2_service_expense_with_wht(self):
        # 服务 1000 + VAT 70 − WHT 30:贷分流 应付 1040 + 预扣税应缴 30
        ctx = _purchase_ctx(
            doc_kind="expense",
            amounts={
                "grand_total": Decimal("1070.00"),
                "vat_amount": Decimal("70.00"),
                "wht_amount": Decimal("30.00"),
            },
            lines=[
                {
                    "item_type": "service",
                    "product_id": None,
                    "line_total": Decimal("1000.00"),
                    "category_id": "c1",
                    "description": "ค่าบริการ",
                }
            ],
        )
        r = rules.build(ctx)
        self.assertEqual(r["rule_key"], "R2")
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(
            _by_role(r["entries"], "wht_payable", "credit")[0]["amount"], Decimal("30.00")
        )
        self.assertEqual(_by_role(r["entries"], "ap", "credit")[0]["amount"], Decimal("1040.00"))
        self.assertEqual(
            _by_role(r["entries"], "expense:c1", "debit")[0]["amount"], Decimal("1000.00")
        )

    def test_r2_ocr_expense_uncertain_until_learned(self):
        ctx = _purchase_ctx(doc_kind="expense", source_tier="ocr")
        self.assertIn("item_type_guess", rules.build(ctx)["uncertainties"])
        ctx_learned = _purchase_ctx(
            doc_kind="expense", source_tier="ocr", learned={"confirmed_rule": "R2"}
        )
        self.assertNotIn("item_type_guess", rules.build(ctx_learned)["uncertainties"])

    def test_r2_learned_account_overrides_bucket(self):
        ctx = _purchase_ctx(
            doc_kind="expense",
            lines=[
                {
                    "item_type": "service",
                    "product_id": None,
                    "line_total": Decimal("1000.00"),
                    "category_id": None,
                    "description": "x",
                }
            ],
            learned={"account_id": "acc-9"},
        )
        r = rules.build(ctx)
        learned_line = [e for e in r["entries"] if e["account_id"] == "acc-9"]
        self.assertEqual(learned_line[0]["amount"], Decimal("1000.00"))

    def test_r3_purchase_order_no_voucher(self):
        self.assertIsNone(rules.build(_purchase_ctx(doc_kind="purchase_order")))


class SaleRulesTests(unittest.TestCase):
    def _ctx(self, **over):
        ctx = {
            "source_type": "sale",
            "source_tier": "first_party",
            "doc_kind": "tax_invoice",
            "amounts": {
                "grand_total": Decimal("1070.00"),
                "vat_amount": Decimal("70.00"),
                "wht_amount": Decimal("0.00"),
                "paid_amount": Decimal("0.00"),
            },
            "paid_at_issue": False,
            "payment_method": None,
            "ref": "销售单 INV-1",
            "scope_keys": [],
        }
        ctx.update(over)
        return ctx

    def test_r4_credit_sale(self):
        r = rules.build(self._ctx())
        self.assertEqual(r["rule_key"], "R4")
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(_by_role(r["entries"], "ar", "debit")[0]["amount"], Decimal("1070.00"))
        self.assertEqual(
            _by_role(r["entries"], "sales_revenue", "credit")[0]["amount"], Decimal("1000.00")
        )
        self.assertEqual(
            _by_role(r["entries"], "output_vat", "credit")[0]["amount"], Decimal("70.00")
        )

    def test_r4_cash_sale_with_buyer_wht(self):
        ctx = self._ctx(
            amounts={
                "grand_total": Decimal("1070.00"),
                "vat_amount": Decimal("70.00"),
                "wht_amount": Decimal("30.00"),
                "paid_amount": Decimal("1040.00"),
            },
            paid_at_issue=True,
            payment_method="cash",
        )
        r = rules.build(ctx)
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(
            _by_role(r["entries"], "wht_prepaid", "debit")[0]["amount"], Decimal("30.00")
        )
        self.assertEqual(_by_role(r["entries"], "cash", "debit")[0]["amount"], Decimal("1040.00"))
        self.assertEqual(_by_role(r["entries"], "ar"), [])

    def test_r4_quotation_no_voucher(self):
        self.assertIsNone(rules.build(self._ctx(doc_kind="quotation")))

    def test_r8_credit_note_reversed_and_uncertain(self):
        r = rules.build(self._ctx(doc_kind="credit_note"))
        self.assertEqual(r["rule_key"], "R8")
        self.assertIn("reversal_direction", r["uncertainties"])
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        # 反向:收入在借方、应收在贷方
        self.assertEqual(
            _by_role(r["entries"], "sales_revenue", "debit")[0]["amount"], Decimal("1000.00")
        )
        self.assertEqual(_by_role(r["entries"], "ar", "credit")[0]["amount"], Decimal("1070.00"))


class PosRulesTests(unittest.TestCase):
    def _ctx(self, **over):
        ctx = {
            "source_type": "pos",
            "source_tier": "first_party",
            "amounts": {"grand_total": Decimal("484.00"), "vat_amount": Decimal("31.66")},
            "payments": [{"role": "cash", "amount": Decimal("484.00")}],
            "is_refund": False,
            "ref": "POS 小票 R-1",
            "scope_keys": [],
        }
        ctx.update(over)
        return ctx

    def test_r5_pos_sale_split_payment(self):
        ctx = self._ctx(
            payments=[
                {"role": "cash", "amount": Decimal("184.00")},
                {"role": "bank", "amount": Decimal("300.00")},
            ]
        )
        r = rules.build(ctx)
        self.assertEqual(r["rule_key"], "R5")
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(_by_role(r["entries"], "cash", "debit")[0]["amount"], Decimal("184.00"))
        self.assertEqual(_by_role(r["entries"], "bank", "debit")[0]["amount"], Decimal("300.00"))
        self.assertEqual(
            _by_role(r["entries"], "sales_revenue", "credit")[0]["amount"], Decimal("452.34")
        )

    def test_r5_underpaid_remainder_goes_ar(self):
        ctx = self._ctx(payments=[{"role": "cash", "amount": Decimal("400.00")}])
        r = rules.build(ctx)
        self.assertEqual(_by_role(r["entries"], "ar", "debit")[0]["amount"], Decimal("84.00"))
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))

    def test_r8_pos_refund_reversed(self):
        r = rules.build(self._ctx(is_refund=True))
        self.assertEqual(r["rule_key"], "R8")
        self.assertIn("reversal_direction", r["uncertainties"])
        self.assertEqual(_by_role(r["entries"], "cash", "credit")[0]["amount"], Decimal("484.00"))


class PaymentRulesTests(unittest.TestCase):
    def test_r6_receipt(self):
        r = rules.build(
            {
                "source_type": "payment",
                "source_tier": "first_party",
                "amounts": {"amount": Decimal("500.00")},
                "direction": "in",
                "payment_method": "transfer",
            }
        )
        self.assertEqual(r["rule_key"], "R6")
        self.assertEqual(_by_role(r["entries"], "bank", "debit")[0]["amount"], Decimal("500.00"))
        self.assertEqual(_by_role(r["entries"], "ar", "credit")[0]["amount"], Decimal("500.00"))
        self.assertEqual(r["uncertainties"], [])

    def test_r7_payment_method_unknown_flagged(self):
        r = rules.build(
            {
                "source_type": "payment",
                "source_tier": "first_party",
                "amounts": {"amount": Decimal("540.00")},
                "direction": "out",
                "payment_method": None,
            }
        )
        self.assertEqual(r["rule_key"], "R7")
        self.assertIn("payment_method_unknown", r["uncertainties"])
        self.assertEqual(_by_role(r["entries"], "ap", "debit")[0]["amount"], Decimal("540.00"))


class VatClosingRulesTests(unittest.TestCase):
    def test_r9_payable(self):
        r = rules.build(
            {
                "source_type": "vat_closing",
                "source_tier": "first_party",
                "amounts": {
                    "output_vat_total": Decimal("700.00"),
                    "input_vat_total": Decimal("400.00"),
                },
                "ref": "2026-06",
            }
        )
        self.assertEqual(r["rule_key"], "R9")
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))
        self.assertEqual(
            _by_role(r["entries"], "vat_payable", "credit")[0]["amount"], Decimal("300.00")
        )

    def test_r9_receivable_carryover(self):
        r = rules.build(
            {
                "source_type": "vat_closing",
                "source_tier": "first_party",
                "amounts": {
                    "output_vat_total": Decimal("400.00"),
                    "input_vat_total": Decimal("700.00"),
                },
            }
        )
        self.assertEqual(
            _by_role(r["entries"], "vat_receivable", "debit")[0]["amount"], Decimal("300.00")
        )
        self.assertEqual(_sum(r["entries"], "debit"), _sum(r["entries"], "credit"))


class ConfidenceTests(unittest.TestCase):
    def test_three_tiers(self):
        self.assertEqual(rules.compute_confidence("first_party", []), Decimal("100"))
        self.assertEqual(rules.compute_confidence("ocr", []), Decimal("95"))
        self.assertEqual(rules.compute_confidence("ocr", ["item_type_guess"]), Decimal("60"))

    def test_lowest_uncertainty_wins(self):
        self.assertEqual(
            rules.compute_confidence(
                "first_party", ["payment_method_unknown", "reversal_direction"]
            ),
            Decimal("60"),
        )


if __name__ == "__main__":
    unittest.main()
