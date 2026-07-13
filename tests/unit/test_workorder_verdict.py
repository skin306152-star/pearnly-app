# -*- coding: utf-8 -*-
"""判据人话 + 置信度只读投影守门(services/workorder/verdict.py · MC1-b1)。

纯函数,脱库脱框架。锁三件:①每个已知 flag_reason 前缀映射到对的 narrative_key + 置信度;
②amount_math_fail 的 params 差额算术正确(净+税 vs 票面);③未知原因诚实降级(key=None,
confidence=low,不淡化不编造)。
"""

import unittest

from services.workorder import verdict


class MathFailTests(unittest.TestCase):
    def test_narrative_key_confidence_and_diff_params(self):
        h = verdict.hint(
            flag_reason="amount_math_fail",
            ocr_read={"subtotal": "100.00", "vat": "7.00", "total_amount": "110.00"},
        )
        self.assertEqual(h["narrative_key"], "verdict_amount_math_fail")
        self.assertEqual(h["confidence"], verdict.LOW)  # 票面自身冲突 → low
        self.assertEqual(h["params"]["net"], "100.00")
        self.assertEqual(h["params"]["vat"], "7.00")
        self.assertEqual(h["params"]["sum"], "107.00")
        self.assertEqual(h["params"]["total"], "110.00")
        self.assertEqual(h["params"]["diff"], "3.00")  # |110 - (100+7)|

    def test_thousands_separator_and_missing_fields_default_zero(self):
        h = verdict.hint(
            flag_reason="amount_math_fail", ocr_read={"subtotal": "1,000.00", "vat": "70.00"}
        )
        # total 缺 → 0;diff = |0 - 1070| = 1070.00
        self.assertEqual(h["params"]["sum"], "1070.00")
        self.assertEqual(h["params"]["diff"], "1070.00")


class DirectionAndConfidenceTests(unittest.TestCase):
    def test_sales_direction_is_high_with_seller_tax(self):
        h = verdict.hint(
            flag_reason="sales_direction_unhandled",
            ocr_read={"seller_tax": "0105551234567", "vendor": "ร้านเรา"},
        )
        self.assertEqual(h["narrative_key"], "verdict_sales_direction")
        self.assertEqual(h["confidence"], verdict.HIGH)  # 税号精确判本方销项
        self.assertEqual(h["params"]["seller_tax"], "0105551234567")

    def test_sales_doc_review_is_mid(self):
        h = verdict.hint(flag_reason="sales_doc_review", ocr_read={"seller_tax": "x"})
        self.assertEqual(h["narrative_key"], "verdict_sales_doc")
        self.assertEqual(h["confidence"], verdict.MID)  # 名称/税号锚 → mid

    def test_direction_ambiguous_is_low(self):
        h = verdict.hint(flag_reason="direction_ambiguous", ocr_read={})
        self.assertEqual(h["narrative_key"], "verdict_direction_ambiguous")
        self.assertEqual(h["confidence"], verdict.LOW)
        self.assertIsNone(h["params"]["seller_tax"])  # 缺锚诚实给 None


class ColonSuffixTests(unittest.TestCase):
    def test_low_confidence_band_extracted_from_suffix(self):
        h = verdict.hint(flag_reason="ocr_low_confidence:high_variance")
        self.assertEqual(h["narrative_key"], "verdict_ocr_low_conf")
        self.assertEqual(h["confidence"], verdict.LOW)
        self.assertEqual(h["params"]["band"], "high_variance")

    def test_duplicate_of_is_high_with_ref(self):
        h = verdict.hint(flag_reason="duplicate_of:IMG_2640.jpg")
        self.assertEqual(h["narrative_key"], "verdict_duplicate")
        self.assertEqual(h["confidence"], verdict.HIGH)  # 指纹精确命中
        self.assertEqual(h["params"]["of"], "IMG_2640.jpg")

    def test_ocr_error_carries_exception_name(self):
        h = verdict.hint(flag_reason="ocr_error:TimeoutError")
        self.assertEqual(h["narrative_key"], "verdict_ocr_error")
        self.assertEqual(h["params"]["error"], "TimeoutError")


class SeverityPolicyTests(unittest.TestCase):
    """severity 政策单一事实源(F5):前端 flagSeverity 副本已删,红/黄口径归此。"""

    def test_crit_and_warn_split_matches_legacy_frontend(self):
        crit = ["amount_math_fail", "ocr_error:X", "direction_ambiguous", "duplicate_of:a"]
        warn = ["ocr_low_confidence:hi", "ocr_validation_warning", "sales_doc_review"]
        for r in crit:
            self.assertEqual(verdict.severity_of(r), verdict.SEV_CRIT, r)
        for r in warn:
            self.assertEqual(verdict.severity_of(r), verdict.SEV_WARN, r)

    def test_unknown_and_empty_are_crit(self):
        for r in ("some_future_reason", "", None):
            self.assertEqual(verdict.severity_of(r), verdict.SEV_CRIT)

    def test_hint_carries_severity(self):
        self.assertEqual(verdict.hint(flag_reason="sales_doc_review")["severity"], verdict.SEV_WARN)
        self.assertEqual(verdict.hint(flag_reason="amount_math_fail")["severity"], verdict.SEV_CRIT)


class SuggestedDecisionPolicyTests(unittest.TestCase):
    """批量建议裁决政策单一事实源(F5):前端 _BULK_TEMPLATES 副本已删。"""

    def test_direction_and_duplicate_carry_safe_default(self):
        self.assertEqual(
            verdict.hint(flag_reason="sales_direction_unhandled")["suggested_decision"],
            {"decision": "assign_kind", "kind": "sales_doc"},
        )
        self.assertEqual(
            verdict.hint(flag_reason="sales_doc_review")["suggested_decision"],
            {"decision": "assign_kind", "kind": "sales_doc"},
        )
        self.assertEqual(
            verdict.hint(flag_reason="duplicate_of:IMG.jpg")["suggested_decision"],
            {"decision": "exclude"},
        )

    def test_low_confidence_and_conflict_have_no_default(self):
        for r in ("amount_math_fail", "direction_ambiguous", "ocr_low_confidence:x", "ocr_error"):
            self.assertIsNone(verdict.hint(flag_reason=r)["suggested_decision"], r)

    def test_unknown_reason_has_no_default(self):
        self.assertIsNone(verdict.hint(flag_reason="future")["suggested_decision"])


class DegradeTests(unittest.TestCase):
    def test_unknown_reason_is_null_key_low_conf(self):
        h = verdict.hint(flag_reason="some_future_reason")
        self.assertIsNone(h["narrative_key"])  # 前端据此回退原文
        self.assertEqual(h["params"], {})
        self.assertEqual(h["confidence"], verdict.LOW)  # 未知不淡化

    def test_none_reason_is_null_key(self):
        self.assertIsNone(verdict.hint(flag_reason=None)["narrative_key"])


if __name__ == "__main__":
    unittest.main()
