# -*- coding: utf-8 -*-
"""OCR 闸报警 → flag_reason 政策(从 classify 抽出后的单一事实源)。

重点守判据顺序:凡「系统改写过票面」的专属前缀必须排在关键词表 _MATH_HINTS 之前 ——
那些留痕文本里带着 subtotal/vat/折扣的字样,撞进词表会被误标成「票面自身勾稽失败」,
而被改写后的数字恰恰是自洽的,会计照着「数字不自洽」去核对必然扑空。
"""

from __future__ import annotations

import unittest

from services.ocr.sanity import DISCOUNT_INFERRED_PREFIX
from services.ocr.totals_rescue import TOTALS_RESCUED_PREFIX
from services.workorder.steps import gate_reason


class GateReasonTests(unittest.TestCase):
    def test_no_warning_no_review_is_none(self):
        self.assertIsNone(gate_reason.of({}))

    def test_math_hint_maps_to_amount_math_fail(self):
        fields = {"_validation_warnings": ["总额 100 != 小计 90 + VAT 7"]}
        self.assertEqual(gate_reason.of(fields), "amount_math_fail")

    def test_unrecognised_warning_falls_back_to_validation(self):
        fields = {"_validation_warnings": ["something odd about this page"]}
        self.assertEqual(gate_reason.of(fields), "ocr_validation_warning")

    def test_needs_review_without_warning_carries_band(self):
        fields = {"_needs_review": True, "_confidence_band": "yellow_confirm"}
        self.assertEqual(gate_reason.of(fields), "ocr_low_confidence:yellow_confirm")

    def test_discount_prefix_wins_over_math_hint(self):
        # 回填留痕带「折扣」字样,会撞 _MATH_HINTS 的「折」——前缀必须先判。
        fields = {"_validation_warnings": [f"{DISCOUNT_INFERRED_PREFIX} 票面折扣 140.00 …"]}
        self.assertEqual(gate_reason.of(fields), "discount_inferred")

    def test_rescue_prefix_wins_over_math_hint(self):
        # 救援留痕带 subtotal/vat 新旧值,会撞 _MATH_HINTS 的「vat」——前缀必须先判。
        fields = {"_validation_warnings": [f"{TOTALS_RESCUED_PREFIX} vat 4060.05→4069.05"]}
        self.assertEqual(gate_reason.of(fields), "totals_rescued")


if __name__ == "__main__":
    unittest.main(verbosity=2)
