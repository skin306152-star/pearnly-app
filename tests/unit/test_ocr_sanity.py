# -*- coding: utf-8 -*-
"""services/ocr/sanity.evaluate_sanity 硬闸单测(确定性·不连模型)。

锁每条规则的「该触发」与「不该误杀」两面:负数(贷项单豁免)、串税号、总额<单行
(有折扣豁免)、缺VAT勾稽不平(无税/含税/7%三种合法形态不误杀)。
"""

import unittest
from types import SimpleNamespace

from services.ocr.sanity import evaluate_sanity


def _line(subtotal):
    return SimpleNamespace(subtotal=subtotal)


def _inv(**kw):
    base = dict(
        is_not_invoice=False,
        document_type="tax_invoice",
        subtotal="",
        vat="",
        total_amount="",
        discount="",
        seller_tax="",
        buyer_tax="",
        items=[],
    )
    base.update(kw)
    return SimpleNamespace(**base)


class CleanInvoiceTests(unittest.TestCase):
    def test_balanced_invoice_passes(self):
        inv = _inv(
            subtotal="65.42",
            vat="4.58",
            total_amount="70.00",
            seller_tax="0107561000013",
            buyer_tax="0105556700123",
        )
        self.assertEqual(evaluate_sanity(inv), [])

    def test_not_invoice_shortcircuits(self):
        self.assertEqual(evaluate_sanity(_inv(is_not_invoice=True, total_amount="-999")), [])

    def test_vat_inclusive_receipt_passes(self):
        # 含税小票:sub==total,vat 空 → 合法,不误杀。
        self.assertEqual(evaluate_sanity(_inv(subtotal="100", total_amount="100")), [])

    def test_vat_missing_seven_percent_passes(self):
        # 漏抽销项税但总额=小计+7% → 合法形态,不误杀。
        self.assertEqual(evaluate_sanity(_inv(subtotal="100", total_amount="107")), [])


class NegativeTests(unittest.TestCase):
    def test_negative_total_flagged(self):
        self.assertTrue(any("为负" in r for r in evaluate_sanity(_inv(total_amount="-1141561"))))

    def test_negative_vat_flagged(self):
        self.assertTrue(any("为负" in r for r in evaluate_sanity(_inv(vat="-5"))))

    def test_credit_note_negative_exempt(self):
        inv = _inv(document_type="credit_note", total_amount="-500", subtotal="-500")
        self.assertEqual(evaluate_sanity(inv), [])


class SellerBuyerTests(unittest.TestCase):
    def test_seller_equals_buyer_flagged(self):
        inv = _inv(seller_tax="0-1055-56700-12-3", buyer_tax="0105556700123")
        self.assertTrue(any("串了表头税号" in r for r in evaluate_sanity(inv)))

    def test_distinct_tax_ids_pass(self):
        inv = _inv(seller_tax="0107561000013", buyer_tax="0105556700123")
        self.assertEqual(evaluate_sanity(inv), [])


class TotalBelowLineTests(unittest.TestCase):
    def test_total_below_max_line_flagged(self):
        # 选错列:总额 44.67 但明细里有一行 1780 → 不可能。
        inv = _inv(total_amount="44.67", items=[_line("1780.00"), _line("0")])
        self.assertTrue(any("单条明细" in r for r in evaluate_sanity(inv)))

    def test_total_below_line_with_discount_not_flagged(self):
        # 有折扣时总额可能合法低于单行 → 不误杀。
        inv = _inv(total_amount="500", discount="1500", items=[_line("1000"), _line("1000")])
        self.assertEqual(evaluate_sanity(inv), [])

    def test_total_above_lines_passes(self):
        inv = _inv(total_amount="2000", items=[_line("1000"), _line("900")])
        self.assertEqual(evaluate_sanity(inv), [])


class VatMissingReconcileTests(unittest.TestCase):
    def test_vat_missing_unbalanced_flagged(self):
        # 缺 VAT,总额−小计 既非 0 也非 7% → 不平。
        self.assertTrue(
            any(
                "勾稽不平" in r for r in evaluate_sanity(_inv(subtotal="1000", total_amount="1230"))
            )
        )

    def test_vat_missing_only_total_not_flagged(self):
        # 小计缺,无法勾稽 → 不误杀(交给别的闸)。
        self.assertEqual(evaluate_sanity(_inv(total_amount="1230")), [])

    def test_vat_missing_with_discount_passes(self):
        # 7-11 折扣票陷阱:小计115 − 折扣5 = 总额110,vat 空 → 合法,不误杀。
        inv = _inv(subtotal="115.00", discount="5.00", total_amount="110.00")
        self.assertEqual(evaluate_sanity(inv), [])


if __name__ == "__main__":
    unittest.main()
