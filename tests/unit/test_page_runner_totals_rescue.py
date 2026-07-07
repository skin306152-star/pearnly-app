# -*- coding: utf-8 -*-
"""page_runner._process_one_page · L3 全量复读失败后的窄口径救援接线(2026-07-08)。

NBC 折扣票实案:确定性闸报 amount math fail 触发 L3,L3 视觉复读吐不出合法 JSON
(Layer3FallbackError)—— 修前:原样带着 L2 的错读数字举手(needs_manual_review);
修后:先试一次 totals_rescue 窄口径重抽,救回来就用对的数字(仍非 auto,confirm
即可),救不回来才原样举手,数字绝不比修前更差。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ocr import page_runner
from services.ocr.layer3_fallback import Layer3FallbackError
from services.ocr.schemas import Layer1Result, Layer2PageResult, Page, ThaiInvoice

_PAGE = Page(page_number=1, width=10, height=10, full_text="x", avg_confidence=1.0, blocks=[])

# sub+vat=total 仍自洽(规则 4b 放行),但 VAT 不是净额的 7%(NBC 实案真实误读)。
_MISREAD_INVOICE = ThaiInvoice(
    document_type="tax_invoice", subtotal="53129.00", vat="4060.05", total_amount="57189.05"
)
_FIXED_INVOICE = ThaiInvoice(
    document_type="tax_invoice", subtotal="58129.35", vat="4069.05", total_amount="62198.40"
)


def _fake_l1(image_bytes, page_number):
    return Layer1Result(pages=[_PAGE], page_count=1, elapsed_ms=1)


def _fake_l2(l1_page, **kw):
    return Layer2PageResult(page_number=1, invoice=_MISREAD_INVOICE)


def _fake_l3_no_valid_json(**kw):
    raise Layer3FallbackError("layer3: gateway returned no valid JSON after 2 attempts (parse)")


class TotalsRescueWiringTests(unittest.TestCase):
    def _run(self):
        with (
            mock.patch.object(page_runner, "_l1_extract_image", _fake_l1),
            mock.patch.object(page_runner, "_l2_extract_page", _fake_l2),
            mock.patch.object(page_runner, "_l3_refine_page", _fake_l3_no_valid_json),
        ):
            return page_runner._process_one_page(
                b"\xff\xd8fakejpeg",
                page_number=1,
                api_key=None,
                enable_layer3=True,
                fallback_to_layer2_on_layer3_error=True,
            )

    def test_successful_rescue_replaces_misread_totals(self):
        with (
            mock.patch.object(
                page_runner.totals_rescue,
                "rescue_totals",
                return_value={"subtotal": "58129.35", "vat": "4069.05", "total_amount": "62198.40"},
            ),
            mock.patch.object(
                page_runner.totals_rescue, "apply_rescue", return_value=_FIXED_INVOICE
            ),
        ):
            pr = self._run()
        self.assertEqual(pr.invoice.subtotal, "58129.35")
        self.assertEqual(pr.invoice.vat, "4069.05")
        self.assertEqual(pr.invoice.total_amount, "62198.40")
        self.assertEqual(pr.layer_chain[-1], "L3_totals_rescue")
        self.assertFalse(pr.needs_manual_review)

    def test_failed_rescue_still_raises_hand_with_original_numbers(self):
        with (
            mock.patch.object(page_runner.totals_rescue, "rescue_totals", return_value=None),
            mock.patch.object(page_runner.totals_rescue, "apply_rescue"),
        ):
            pr = self._run()
        # 数字不比修前更差:救不回来就原样带 L2 的读数举手,绝不硬套一个还不平的数。
        self.assertEqual(pr.invoice.subtotal, "53129.00")
        self.assertEqual(pr.invoice.vat, "4060.05")
        self.assertEqual(pr.layer_chain[-1], "L3_failed")
        self.assertTrue(pr.needs_manual_review)


if __name__ == "__main__":
    unittest.main()
