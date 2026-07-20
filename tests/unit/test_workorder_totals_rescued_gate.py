# -*- coding: utf-8 -*-
"""换过眼睛的读数在工单侧要有自己的名字(A-2 · 2026-07-20)。

L3 视觉复读失败后,`totals_rescue` 让第二个模型窄口径重读四个金额并整体替换。修前那条
成功分支是 page_runner 里唯一不设 `needs_manual_review` 的出口,`validation_warnings`
也为空 —— 生产库回放显示工单侧因此拿到 `flag_reason=None`,票根本不进人审队列,钱面
四数换过一双眼睛就直接进 R1 合计(复现见 scratchpad/repro_a2.py 的口径)。

本文件守住读侧:留痕带前缀、工单侧给专属 flag_reason、判据政策不给批量安全默认。
OCR 层「留人」那半边由 tests/unit/test_page_runner_totals_rescue.py 守。
"""

from __future__ import annotations

import unittest

from services.ocr.schemas import ThaiInvoice
from services.ocr.totals_rescue import TOTALS_RESCUED_PREFIX, rescue_note
from services.workorder import verdict
from services.workorder.steps import classify

_BEFORE = ThaiInvoice(
    document_type="tax_invoice", subtotal="53129.00", vat="4060.05", total_amount="57189.05"
)
_AFTER = ThaiInvoice(
    document_type="tax_invoice", subtotal="58129.35", vat="4069.05", total_amount="62198.40"
)


class RescueNoteTests(unittest.TestCase):
    def test_note_spells_out_every_changed_field(self):
        note = rescue_note(_BEFORE, _AFTER)
        self.assertTrue(note.startswith(TOTALS_RESCUED_PREFIX))
        self.assertIn("subtotal 53129.00→58129.35", note)
        self.assertIn("vat 4060.05→4069.05", note)
        self.assertIn("total_amount 57189.05→62198.40", note)

    def test_unchanged_fields_stay_out_of_the_note(self):
        note = rescue_note(_BEFORE, _BEFORE)
        self.assertTrue(note.startswith(TOTALS_RESCUED_PREFIX))
        self.assertNotIn("→", note)


class GateReasonTests(unittest.TestCase):
    def test_rescued_read_gets_its_own_flag_reason(self):
        fields = {
            "_validation_warnings": [rescue_note(_BEFORE, _AFTER)],
            "_needs_review": True,
            "_confidence_band": "needs_review",
        }
        self.assertEqual(classify._gate_reason(fields), "totals_rescued")

    def test_rescue_note_does_not_masquerade_as_a_math_failure(self):
        """留痕文本里带着 subtotal/vat 的新旧值,撞 _MATH_HINTS 会被误标成票面勾稽失败 ——
        那句话是错的:替换后的三数恰恰是自洽的,会计照着核对必然扑空。"""
        fields = {"_validation_warnings": [rescue_note(_BEFORE, _AFTER)], "_needs_review": True}
        self.assertNotEqual(classify._gate_reason(fields), "amount_math_fail")


class VerdictPolicyTests(unittest.TestCase):
    def test_policy_puts_the_three_numbers_on_the_card(self):
        hint = verdict.hint(
            flag_reason="totals_rescued",
            ocr_read={"subtotal": "58129.35", "vat": "4069.05", "total_amount": "62198.40"},
        )
        self.assertEqual(hint["narrative_key"], "verdict_totals_rescued")
        self.assertEqual(hint["params"], {"net": "58129.35", "vat": "4069.05", "total": "62198.40"})
        self.assertEqual(hint["severity"], verdict.SEV_CRIT)
        # 第二个模型读出来的钱,不许被「全部按建议处理」一键认下。
        self.assertIsNone(hint["suggested_decision"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
