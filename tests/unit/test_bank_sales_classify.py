# -*- coding: utf-8 -*-
"""银行销项判断题构造 + 回复解析硬闸守门(services/workorder/steps/bank_sales_classify.py)。

从 test_bank_sales_brain 迁来:引用必真、无据必认怂、实分类必带引用、题面外/重复行不落。
纯函数,零真调网关。"""

from __future__ import annotations

import unittest

from services.workorder.steps import bank_sales_classify as classify


class ParseSuggestionTests(unittest.TestCase):
    FP = "2569-05-01|1000|0"

    def test_valid_sales_with_citation(self):
        rec = classify.parse_suggestion(
            {
                "suggestion": "sales",
                "confidence": 0.9,
                "reason_zh": "客户转账",
                "cited_row_fingerprints": [self.FP],
            },
            {self.FP},
        )
        self.assertTrue(rec["valid"])
        self.assertEqual(rec["suggestion"], "sales")

    def test_cannot_judge_without_citation_is_valid(self):
        rec = classify.parse_suggestion(
            {
                "suggestion": "cannot_judge",
                "confidence": 0.2,
                "reason_zh": "看不出",
                "cited_row_fingerprints": [],
            },
            {self.FP},
        )
        self.assertTrue(rec["valid"])
        self.assertEqual(rec["suggestion"], "cannot_judge")

    def test_fake_citation_rejected(self):
        rec = classify.parse_suggestion(
            {"suggestion": "sales", "confidence": 0.9, "cited_row_fingerprints": ["9999|0|0"]},
            {self.FP},
        )
        self.assertFalse(rec["valid"])
        self.assertEqual(rec["invalid_reason"], classify.INVALID_CITED_MISSING)

    def test_real_verdict_without_citation_rejected(self):
        rec = classify.parse_suggestion(
            {"suggestion": "sales", "confidence": 0.9, "cited_row_fingerprints": []}, {self.FP}
        )
        self.assertFalse(rec["valid"])
        self.assertEqual(rec["invalid_reason"], classify.INVALID_CITATION_REQUIRED)

    def test_unknown_suggestion_rejected(self):
        rec = classify.parse_suggestion({"suggestion": "maybe", "confidence": 0.5}, {self.FP})
        self.assertEqual(rec["invalid_reason"], classify.INVALID_SUGGESTION_UNKNOWN)

    def test_confidence_out_of_range_rejected(self):
        rec = classify.parse_suggestion(
            {"suggestion": "sales", "confidence": 5, "cited_row_fingerprints": [self.FP]}, {self.FP}
        )
        self.assertEqual(rec["invalid_reason"], classify.INVALID_CONFIDENCE)


class BatchAndPromptTests(unittest.TestCase):
    def _row(self, fp="a"):
        return {
            "fingerprint": fp,
            "date": "2569-05-01",
            "deposit": 100,
            "description": "รับโอนเงิน",
        }

    def test_batch_question_caps_at_batch_size(self):
        rows = [self._row(str(i)) for i in range(classify.BATCH_SIZE + 5)]
        q = classify.build_batch_question(rows)
        self.assertEqual(len(q["rows"]), classify.BATCH_SIZE)

    def test_prompt_embeds_all_suggestions(self):
        prompt = classify.build_batch_prompt({"rows": []})
        for label in classify.SUGGESTIONS:
            self.assertIn(label, prompt)

    def test_batch_drops_foreign_and_duplicate_fingerprints(self):
        def ans(fp):
            return {
                "row_fingerprint": fp,
                "suggestion": "sales",
                "confidence": 0.9,
                "cited_row_fingerprints": [fp],
            }

        out = classify.parse_batch_suggestions(
            {"suggestions": [ans("a"), ans("a"), ans("foreign")]}, {"a", "b"}
        )
        self.assertEqual([r["row_fingerprint"] for r in out], ["a"])


if __name__ == "__main__":
    unittest.main()
