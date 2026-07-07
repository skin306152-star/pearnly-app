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
            buyer_tax="0105535134278",
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
        inv = _inv(seller_tax="0-1055-35134-27-8", buyer_tax="0105535134278")
        self.assertTrue(any("串了表头税号" in r for r in evaluate_sanity(inv)))

    def test_distinct_tax_ids_pass(self):
        inv = _inv(seller_tax="0107561000013", buyer_tax="0105535134278")
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


class TaxIdChecksumTests(unittest.TestCase):
    def test_bad_checksum_seller_flagged(self):
        # Big C 实测误读 0107538000633(真值 …536…):13 位但 MOD-11 不过 → 转人工。
        inv = _inv(seller_tax="0107538000633", subtotal="84", total_amount="84")
        self.assertTrue(any("校验位不符" in r for r in evaluate_sanity(inv)))

    def test_good_checksum_not_flagged(self):
        # Big C 真值 0107536000633:校验位过 → 不误杀。
        inv = _inv(seller_tax="0107536000633", subtotal="84", total_amount="84")
        self.assertFalse(any("校验位不符" in r for r in evaluate_sanity(inv)))

    def test_non_13_digit_not_flagged(self):
        # 残缺/空税号不归此规则(交别的处理) → 不误杀。
        self.assertFalse(any("校验位不符" in r for r in evaluate_sanity(_inv(seller_tax="010753"))))
        self.assertFalse(any("校验位不符" in r for r in evaluate_sanity(_inv(seller_tax=""))))

    def test_bad_checksum_buyer_flagged(self):
        inv = _inv(seller_tax="0105535134278", buyer_tax="0107538000633")
        self.assertTrue(any("校验位不符" in r for r in evaluate_sanity(inv)))

    def test_dashed_bad_checksum_flagged(self):
        # 票面带连字符的误读税号:归一去分隔后 13 位但校验不过 → 仍抓。
        inv = _inv(seller_tax="0-1075-38000-63-3", subtotal="84", total_amount="84")
        self.assertTrue(any("校验位不符" in r for r in evaluate_sanity(inv)))

    def test_dashed_good_checksum_not_flagged(self):
        # 同款连字符格式但真值:校验过 → 不误杀。
        inv = _inv(seller_tax="0-1075-36000-63-3", subtotal="84", total_amount="84")
        self.assertFalse(any("校验位不符" in r for r in evaluate_sanity(inv)))


class LineSumExceedsSubtotalTests(unittest.TestCase):
    # 规则 6(trap08 实案):重影把小计/总额同一位数字糊错(1896→1396·1846→1346),
    # 勾稽自平+双读一致全绿,但明细行和(396.68+1500=1896.68)供出真数。

    def _items(self, *subs):
        from services.ocr.schemas import LineItem

        return [LineItem(name=f"i{i}", subtotal=s) for i, s in enumerate(subs)]

    def test_trap08_shape_flagged(self):
        inv = _inv(
            subtotal="1396.68",
            vat="0.00",
            total_amount="1346.68",
            discount="50.00",
            items=self._items("396.68", "1500.00"),
        )
        self.assertTrue(any("明细行和" in r for r in evaluate_sanity(inv)))

    def test_partial_items_not_flagged(self):
        # 只读到部分明细(行和 < 小计)= 合法漏行,不误杀
        inv = _inv(subtotal="1896.68", total_amount="1896.68", items=self._items("396.68"))
        self.assertFalse(any("明细行和" in r for r in evaluate_sanity(inv)))

    def test_rounding_within_tolerance_not_flagged(self):
        inv = _inv(
            subtotal="100.00",
            total_amount="107.00",
            vat="7.00",
            items=self._items("60.00", "40.30"),
        )  # 0.30 < max(0.5, 2%)
        self.assertFalse(any("明细行和" in r for r in evaluate_sanity(inv)))

    def test_single_item_not_judged(self):
        # 单行明细信息量不足(行本身可能读错),≥2 行才判
        inv = _inv(subtotal="100.00", total_amount="100.00", items=self._items("999.00"))
        self.assertFalse(any("明细行和" in r for r in evaluate_sanity(inv)))


class MultiInvoicePageTests(unittest.TestCase):
    # 规则 7 + 附加票过闸(trap11 实案 2026-07-05):同页三张小票,主票被整片偷走
    # 另一张的自洽三元组(759/0/759)→ 单票勾稽全平静默放行;行和 700 供出真数。

    def _items(self, *subs):
        from services.ocr.schemas import LineItem

        return [LineItem(name=f"i{i}", subtotal=s) for i, s in enumerate(subs)]

    def test_trap11_stolen_triple_flagged(self):
        extra = _inv(
            subtotal="419.00",
            vat="29.33",
            total_amount="448.33",
            items=self._items("59.00", "360.00"),
        )
        inv = _inv(
            subtotal="759.00",
            vat="0.00",
            total_amount="759.00",  # 偷来的自洽三元组
            items=self._items("360.00", "80.00", "260.00"),  # 本票行和 700
            additional_invoices=[extra],
        )
        self.assertTrue(any("跨票错配" in r for r in evaluate_sanity(inv)))

    def test_consistent_multi_page_passes(self):
        extra = _inv(
            subtotal="419.00",
            vat="29.33",
            total_amount="448.33",
            items=self._items("59.00", "360.00"),
        )
        inv = _inv(
            subtotal="700.00",
            vat="49.00",
            total_amount="749.00",
            items=self._items("360.00", "80.00", "260.00"),
            additional_invoices=[extra],
        )
        self.assertEqual(evaluate_sanity(inv), [])

    def test_extra_invoice_core_rules_gated(self):
        # 附加票拆成独立入库条目 · 它自己的结构硬伤(负总额)必须被闸住
        extra = _inv(total_amount="-500")
        inv = _inv(subtotal="100", total_amount="107", additional_invoices=[extra])
        reasons = evaluate_sanity(inv)
        self.assertTrue(any(r.startswith("同页第2张") and "为负" in r for r in reasons))

    def test_single_ticket_underread_lines_still_legal(self):
        # 单票页行和 < 小计(服务费/未列项)不收紧 —— 规则 7 只管多票页
        inv = _inv(
            subtotal="759.00", total_amount="759.00", items=self._items("360.00", "80.00", "260.00")
        )
        self.assertEqual(evaluate_sanity(inv), [])


class VatRatioMismatchTests(unittest.TestCase):
    # 规则 4c(NBC 折扣票实案 2026-07-08):sub+vat=total 仍自洽(规则 4b 放行)但
    # VAT 不再是净额的法定 7% —— 抓「小计/VAT/总额被同时误读却互相凑巧对平」这类
    # 自洽性幻觉。

    def test_self_consistent_but_wrong_ratio_flagged(self):
        inv = _inv(subtotal="53129.00", vat="4060.05", total_amount="57189.05")
        reasons = evaluate_sanity(inv)
        self.assertTrue(any("单数位误读" in r for r in reasons))
        # 规则 4b 本身不该重复报警(三者本就互相对平)
        self.assertFalse(any("勾稽不平" in r for r in reasons))

    def test_true_seven_percent_passes(self):
        inv = _inv(subtotal="58129.35", vat="4069.05", total_amount="62198.40")
        self.assertEqual(evaluate_sanity(inv), [])

    def test_discount_pre_discount_base_passes(self):
        # VAT 算在折前小计上,折扣只减 payable(trap08_discount_net_payable 语义)。
        inv = _inv(subtotal="100.00", vat="7.00", discount="50.00", total_amount="57.00")
        self.assertEqual(evaluate_sanity(inv), [])

    def test_discount_post_discount_base_passes(self):
        # VAT 算在折后净额上,小计印的是折前数(f003 语义)。
        inv = _inv(subtotal="5210.00", vat="354.90", discount="140.00", total_amount="5424.90")
        self.assertEqual(evaluate_sanity(inv), [])

    def test_zero_vat_not_flagged(self):
        # VAT=0(免税/未列示销项)是合法形态,不该被 7% 关系误杀。
        inv = _inv(subtotal="1396.68", vat="0.00", total_amount="1346.68", discount="50.00")
        self.assertFalse(any("单数位误读" in r for r in evaluate_sanity(inv)))

    def test_vat_missing_not_flagged(self):
        self.assertFalse(any("单数位误读" in r for r in evaluate_sanity(_inv(subtotal="100"))))


class CreditNoteReviewTests(unittest.TestCase):
    # P1 台账 #8:贷记单=方向性单据,两链共用本判定强制人工,不许当普通发票静默过账。

    def test_credit_note_flagged_for_review(self):
        from services.ocr.sanity import credit_note_review_reason

        inv = _inv(
            document_type="credit_note", subtotal="-65.42", vat="-4.58", total_amount="-70.00"
        )
        self.assertIsNotNone(credit_note_review_reason(inv))
        # 负数金额在 credit_note 上不该被 sanity 规则 1 硬毙(既有豁免的守门)
        self.assertFalse(any("不可能为负" in r for r in evaluate_sanity(inv)))

    def test_normal_invoice_not_flagged(self):
        from services.ocr.sanity import credit_note_review_reason

        self.assertIsNone(credit_note_review_reason(_inv(total_amount="70.00")))
        self.assertIsNone(credit_note_review_reason(_inv(is_not_invoice=True)))


if __name__ == "__main__":
    unittest.main()
