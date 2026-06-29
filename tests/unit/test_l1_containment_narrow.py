# -*- coding: utf-8 -*-
"""收窄 L3 过度触发:L1 containment(Rule 5)归一不足导致的【假幻觉→无谓视觉复读】。

速度根因之一:`check_field_in_l1_text` 判"抽出的关键字段是否在 L1 文本里"——若归一只剥
空格+逗号,不剥连字符/货币符,则:
  · 税号 0105546015062(抽出)vs L1 文本 0-1055-46015-06-2(带横线)→ 判"找不到"→ 升 L3
  · ฿1,780.00 vs L1 1,780.00 → 判"找不到"→ 升 L3
都是正确值被误判幻觉,白白触发 9–61s 的视觉复读。

收窄:归一额外剥连字符/货币符 → 正确值识别为"在文本中"→ 不升 L3(快);真幻觉(数字
压根不同)即便剥了也匹配不上 → 仍升 L3(准度不丢)。本测把两面都钉死。
"""

import unittest

from services.ocr.confidence import check_field_in_l1_text
from services.ocr.schemas import Page, Word
from services.ocr.schemas_layer1 import BoundingBox, Block, Paragraph


def _page(full_text: str) -> Page:
    para = Paragraph(
        text=full_text,
        confidence=1.0,
        bbox=BoundingBox(vertices=[(0, 0), (1, 0), (1, 1), (0, 1)]),
        words=[
            Word(
                text=full_text,
                confidence=1.0,
                bbox=BoundingBox(vertices=[(0, 0), (1, 0), (1, 1), (0, 1)]),
            )
        ],
    )
    block = Block(text=full_text, confidence=1.0, bbox=para.bbox, paragraphs=[para])
    return Page(
        page_number=1,
        width=100,
        height=100,
        full_text=full_text,
        avg_confidence=1.0,
        blocks=[block],
    )


class NoFalseHallucinationEscalationTests(unittest.TestCase):
    def test_dash_formatted_tax_id_is_found(self):
        # 抽出无横线税号,L1 文本带横线 → 应判"在文本中"(不升 L3)
        page = _page("ผู้ขาย เลขประจำตัวผู้เสียภาษี 0-1055-46015-06-2 สาขา 001")
        self.assertTrue(check_field_in_l1_text(page, "0105546015062"))

    def test_currency_prefixed_amount_is_found(self):
        page = _page("ยอดรวมทั้งสิ้น 1,780.00 บาท")
        self.assertTrue(check_field_in_l1_text(page, "฿1,780.00"))

    def test_dash_formatted_date_is_found(self):
        page = _page("วันที่ 28/02/2026 เลขที่ IV69100179")
        self.assertTrue(check_field_in_l1_text(page, "28-02-2026"))


class RealHallucinationStillEscalatesTests(unittest.TestCase):
    def test_wrong_tax_id_not_found(self):
        page = _page("ผู้ขาย เลขประจำตัวผู้เสียภาษี 0-1055-46015-06-2")
        self.assertFalse(check_field_in_l1_text(page, "9999999999999"))

    def test_wrong_amount_not_found(self):
        page = _page("ยอดรวมทั้งสิ้น 1,780.00 บาท")
        self.assertFalse(check_field_in_l1_text(page, "44.67"))


if __name__ == "__main__":
    unittest.main()
