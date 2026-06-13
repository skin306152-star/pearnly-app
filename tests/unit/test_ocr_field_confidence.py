# -*- coding: utf-8 -*-
"""逐字段置信(page_runner._field_confidences)· 喂复核屏「需复核高亮」(阶段一)。

关键字段(发票号/总额/卖家税号/日期)取其在 L1 词里的最低置信;字段不在 OCR 文本
(L2 幻觉/缺)→ 0.0;空字段省略;在全文但无词级匹配(短值)省略(不误标低)。纯只读。
"""

import unittest
from types import SimpleNamespace

from services.ocr.page_runner import _field_confidences
from services.ocr.schemas import Page, Word
from services.ocr.schemas_layer1 import Block, BoundingBox, Paragraph


def _bbox():
    return BoundingBox(vertices=[(0, 0), (1, 0), (1, 1), (0, 1)])


def _word(text, conf):
    return Word(text=text, confidence=conf, bbox=_bbox())


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


def _inv(**kw):
    base = dict(invoice_number="", total_amount="", seller_tax="", date="")
    base.update(kw)
    return SimpleNamespace(**base)


class FieldConfidenceTests(unittest.TestCase):
    def test_high_confidence_field_reported(self):
        page = _page([_word("NZ01000017838", 0.93)])
        out = _field_confidences(page, _inv(invoice_number="NZ01000017838"))
        self.assertEqual(out["invoice_number"], 0.93)

    def test_low_confidence_word_reported_low(self):
        page = _page([_word("NZ01000017838", 0.61)])
        out = _field_confidences(page, _inv(invoice_number="NZ01000017838"))
        self.assertEqual(out["invoice_number"], 0.61)

    def test_hallucinated_field_zero(self):
        # 提取值不在 OCR 文本(L2 幻觉)→ 0.0,喂高亮强制复核。
        page = _page([_word("SOMETHING", 0.99)], full_text="SOMETHING ELSE")
        out = _field_confidences(page, _inv(invoice_number="HZ01000017838"))
        self.assertEqual(out["invoice_number"], 0.0)

    def test_empty_field_omitted(self):
        page = _page([_word("ABCDEFGH", 0.9)])
        out = _field_confidences(page, _inv())
        self.assertEqual(out, {})

    def test_multiple_fields(self):
        page = _page(
            [_word("INV12345", 0.88), _word("0105556", 0.95)],
            full_text="INV12345 0105556 1234.50",
        )
        out = _field_confidences(
            page, _inv(invoice_number="INV12345", seller_tax="0105556", total_amount="1234.50")
        )
        self.assertEqual(out["invoice_number"], 0.88)
        self.assertEqual(out["seller_tax"], 0.95)
        # total 在全文但无独立词级匹配 → 省略(不误判)
        self.assertNotIn("total_amount", out)


if __name__ == "__main__":
    unittest.main()
