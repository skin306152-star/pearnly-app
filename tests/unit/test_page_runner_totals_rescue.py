# -*- coding: utf-8 -*-
"""page_runner._process_one_page · L3 全量复读失败后的窄口径救援接线(2026-07-08)。

NBC 折扣票实案:确定性闸报 amount math fail 触发 L3,L3 视觉复读吐不出合法 JSON
(Layer3FallbackError)—— 修前:原样带着 L2 的错读数字举手(needs_manual_review);
修后:先试一次 totals_rescue 窄口径重抽,救回来就用对的数字,救不回来才原样举手,
数字绝不比修前更差。

★2026-07-20(A-2)改判「救回来就不用人看」:救援成功曾是本函数唯一不设
needs_manual_review 的分支,而它的验收条件只有两条算术自洽 —— 第一次读错时同样成立
(本文件的 _MISREAD 就是 sub+vat=total 自洽却整体错)。「自洽」证明不了「读对」,只
证明这批数字换过一双眼睛,所以现在留痕(TOTALS_RESCUED_PREFIX,差异原样带上)并留人。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ocr import page_runner
from services.ocr.layer3_fallback import Layer3FallbackError
from services.ocr.totals_rescue import TOTALS_RESCUED_PREFIX
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
        # A-2(2026-07-20 改判):这里原本断言 needs_manual_review 为 False —— 把「换了双眼睛
        # 重读、算术能对上」当成了「读对了」。可救援的验收条件只有算术自洽,而第一次读错时
        # 它同样成立(本夹具的 _MISREAD 就是 sub+vat=total 自洽却整体错)。钱面四数被整体
        # 替换却无人过目,是本类问题里最靠近钱的一处。
        self.assertTrue(pr.needs_manual_review)
        note = [w for w in pr.validation_warnings if w.startswith(TOTALS_RESCUED_PREFIX)]
        self.assertEqual(len(note), 1, pr.validation_warnings)
        self.assertIn("53129.00→58129.35", note[0])  # 差异原样进证据链,人才知道该核什么

    def test_failed_rescue_still_raises_hand_with_original_numbers(self):
        with (
            mock.patch.object(page_runner.totals_rescue, "rescue_totals", return_value=None),
            mock.patch.object(page_runner.totals_rescue, "apply_rescue", return_value=None),
        ):
            pr = self._run()
        # 数字不比修前更差:救不回来就原样带 L2 的读数举手,绝不硬套一个还不平的数。
        self.assertEqual(pr.invoice.subtotal, "53129.00")
        self.assertEqual(pr.invoice.vat, "4060.05")
        self.assertEqual(pr.layer_chain[-1], "L3_failed")
        self.assertTrue(pr.needs_manual_review)


if __name__ == "__main__":
    unittest.main()
