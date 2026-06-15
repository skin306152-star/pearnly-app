# -*- coding: utf-8 -*-
"""线 A · L3 触发收紧 + 文档类型分流(doc 09 §3)。

锁三件事:
  1. 缺号/税号触发按文档类型门控 —— 只完整税票较真,简式/收据/非税票不触发(§3.1/3.2)。
  2. 低词置信但值在 L1 文本 → 移出 L3 触发,改 soft_flag(降置信到 yellow_confirm,不跑 L3)。
  3. soft_flag 计入置信 penalty;L3 超时默认收到 15s。
"""

import unittest

from services.ocr.confidence import MIN_OVERLAP_CHARS  # noqa: F401 (阈值上下文)
from services.ocr.schemas import Page, Word
from services.ocr.schemas_invoice import ThaiInvoice
from services.ocr.schemas_layer1 import BoundingBox, Block, Paragraph
from services.ocr.triggers import (
    _aggregate_page_confidence,
    _bucket_confidence,
    _evaluate_soft_flags,
    _evaluate_triggers,
)


def _bbox():
    return BoundingBox(vertices=[(0, 0), (1, 0), (1, 1), (0, 1)])


def _page(words, full_text=""):
    para = Paragraph(
        text=" ".join(w.text for w in words), confidence=1.0, bbox=_bbox(), words=words
    )
    block = Block(text=para.text, confidence=1.0, bbox=_bbox(), paragraphs=[para])
    return Page(
        page_number=1,
        width=100,
        height=100,
        full_text=full_text or para.text,
        avg_confidence=1.0,
        blocks=[block],
    )


def _word(text, conf):
    return Word(text=text, confidence=conf, bbox=_bbox())


class Rule1NumberGateTests(unittest.TestCase):
    def test_full_tax_invoice_missing_number_escalates(self):
        inv = ThaiInvoice(document_type="tax_invoice", invoice_number=None, total_amount="100")
        out = _evaluate_triggers(_page([], full_text=""), inv)
        self.assertIn("invoice_number missing", out)

    def test_simplified_missing_number_does_not_escalate(self):
        inv = ThaiInvoice(
            document_type="simplified_tax_invoice", invoice_number=None, total_amount="100"
        )
        out = _evaluate_triggers(_page([], full_text=""), inv)
        self.assertNotIn("invoice_number missing", out)

    def test_receipt_missing_number_does_not_escalate(self):
        inv = ThaiInvoice(document_type="receipt", invoice_number=None, total_amount="100")
        self.assertNotIn("invoice_number missing", _evaluate_triggers(_page([], ""), inv))

    def test_missing_total_always_escalates(self):
        inv = ThaiInvoice(document_type="simplified_tax_invoice", total_amount=None)
        self.assertIn("total_amount missing", _evaluate_triggers(_page([], ""), inv))


class Rule3TaxIdGateTests(unittest.TestCase):
    def test_full_tax_invoice_bad_taxid_escalates(self):
        inv = ThaiInvoice(
            document_type="tax_invoice", invoice_number="X", total_amount="100", seller_tax="123"
        )
        out = " ".join(_evaluate_triggers(_page([], "X 123"), inv))
        self.assertIn("seller_tax format invalid", out)

    def test_simplified_bad_taxid_does_not_escalate(self):
        inv = ThaiInvoice(
            document_type="simplified_tax_invoice",
            invoice_number="X",
            total_amount="100",
            seller_tax="28232536",
        )
        out = " ".join(_evaluate_triggers(_page([], "X 28232536"), inv))
        self.assertNotIn("seller_tax format invalid", out)


class SoftFlagTests(unittest.TestCase):
    def _inv(self, number):
        # 金额自洽 + 税号留空(隔离:只剩发票号"低词置信"这一个信号)
        return ThaiInvoice(
            document_type="tax_invoice",
            invoice_number=number,
            total_amount="107",
            seller_tax="",
            subtotal="100",
            vat="7",
        )

    def test_low_conf_in_text_is_soft_not_escalation(self):
        # 发票号在 L1 文本里,但词置信 0.72 < 0.85 → soft,不跑 L3
        page = _page([_word("IV69/00179", 0.72)], full_text="ใบกำกับภาษี IV69/00179 total 107")
        inv = self._inv("IV69/00179")
        self.assertEqual(_evaluate_triggers(page, inv), [])
        soft = _evaluate_soft_flags(page, inv)
        self.assertTrue(any("invoice_number" in s for s in soft))

    def test_low_conf_not_in_text_escalates_via_rule5(self):
        # 值不在文本(疑似幻觉)→ Rule 5 升级,不进 soft
        page = _page([_word("IV69/00179", 0.72)], full_text="ใบกำกับภาษี IV69/00179 total 107")
        inv = self._inv("IV99/99999")
        out = " ".join(_evaluate_triggers(page, inv))
        self.assertIn("not found in L1 OCR text", out)
        self.assertEqual(_evaluate_soft_flags(page, inv), [])

    def test_not_invoice_has_no_soft_flags(self):
        page = _page([_word("IV69/00179", 0.5)], full_text="IV69/00179")
        inv = ThaiInvoice(is_not_invoice=True, invoice_number="IV69/00179")
        self.assertEqual(_evaluate_soft_flags(page, inv), [])


class ConfidencePenaltyTests(unittest.TestCase):
    def test_soft_flag_lowers_to_yellow_confirm(self):
        inv = ThaiInvoice(document_type="tax_invoice", invoice_number="X", total_amount="1")
        page = _page([], full_text="")
        # 无触发 + 1 个 soft_flag:base 1.0 - 0.05 = 0.95 → yellow_confirm(不是 auto)
        conf = _aggregate_page_confidence(
            l1_page=page,
            invoice=inv,
            document=None,
            triggers=[],
            needs_manual_review=False,
            document_type="auto",
            soft_flags=["invoice_number low word conf"],
        )
        self.assertLess(conf, _bucket_thresh_auto())
        self.assertEqual(_bucket_confidence(conf, False), "yellow_confirm")

    def test_no_soft_no_trigger_stays_auto(self):
        inv = ThaiInvoice(document_type="tax_invoice", invoice_number="X", total_amount="1")
        page = _page([], full_text="")
        conf = _aggregate_page_confidence(
            l1_page=page,
            invoice=inv,
            document=None,
            triggers=[],
            needs_manual_review=False,
            document_type="auto",
            soft_flags=[],
        )
        self.assertEqual(_bucket_confidence(conf, False), "auto")


def _bucket_thresh_auto():
    from services.ocr.triggers import CONFIDENCE_AUTO_THRESHOLD

    return CONFIDENCE_AUTO_THRESHOLD


class SchemaAndTimeoutTests(unittest.TestCase):
    def test_simplified_doc_type_accepted(self):
        inv = ThaiInvoice(document_type="simplified_tax_invoice")
        self.assertEqual(inv.document_type, "simplified_tax_invoice")

    def test_unknown_doc_type_coerced_to_other(self):
        inv = ThaiInvoice(document_type="weird_value")
        self.assertEqual(inv.document_type, "other")

    def test_l3_timeout_capped(self):
        # 有界但不过紧:15s 太狠会掐断正经 L3 救场(Punthai 15.7s)→ 回退;放宽到 45s
        # 既保速度(触发器已收紧·L3 罕跑)又救准确率(doc 09 §3.3 修正)。
        from services.ocr.layer3_fallback import DEFAULT_TIMEOUT_SECONDS

        self.assertLessEqual(DEFAULT_TIMEOUT_SECONDS, 60)
        self.assertGreaterEqual(DEFAULT_TIMEOUT_SECONDS, 30)


if __name__ == "__main__":
    unittest.main()
