# -*- coding: utf-8 -*-
"""反馈闭环 ② · diff + fewshot 纯逻辑(无 DB)。"""

import unittest

from services.ocr.feedback import diff, fewshot


class ComputeFieldCorrectionsTests(unittest.TestCase):
    def _pages(self, **fields):
        return [{"fields": fields}]

    def test_changed_field_recorded(self):
        ai = self._pages(invoice_number="IV1", total_amount="100")
        cur = self._pages(invoice_number="IV-001", total_amount="100")
        out = diff.compute_field_corrections(ai, cur)
        self.assertEqual(
            out, [{"field_name": "invoice_number", "ai_value": "IV1", "corrected_value": "IV-001"}]
        )

    def test_unchanged_yields_nothing(self):
        ai = self._pages(invoice_number="IV1", seller_name="A Co")
        self.assertEqual(diff.compute_field_corrections(ai, ai), [])

    def test_whitespace_only_diff_ignored(self):
        ai = self._pages(seller_name="A Co")
        cur = self._pages(seller_name="  A Co  ")
        self.assertEqual(diff.compute_field_corrections(ai, cur), [])

    def test_empty_correction_not_recorded(self):
        # 用户清空字段不算修正(corrected_value 必须非空)
        ai = self._pages(vat="7.00")
        cur = self._pages(vat="")
        self.assertEqual(diff.compute_field_corrections(ai, cur), [])

    def test_filled_from_empty_recorded(self):
        ai = self._pages(buyer_tax="")
        cur = self._pages(buyer_tax="0105556000001")
        out = diff.compute_field_corrections(ai, cur)
        self.assertEqual(out[0]["field_name"], "buyer_tax")
        self.assertIsNone(out[0]["ai_value"])

    def test_internal_keys_ignored(self):
        ai = self._pages(invoice_number="IV1")
        cur = self._pages(invoice_number="IV1", _suggested_client_id=9, _x="y")
        self.assertEqual(diff.compute_field_corrections(ai, cur), [])

    def test_primary_skips_copy_pages(self):
        pages = [
            {"is_copy": True, "fields": {"invoice_number": "COPY"}},
            {"fields": {"invoice_number": "REAL", "seller_tax": "0105556"}},
        ]
        tax, name = diff.primary_seller(pages)
        self.assertEqual(tax, "0105556")

    def test_multipage_diff_uses_primary(self):
        ai = [
            {"is_duplicate": True, "fields": {"total_amount": "9"}},
            {"fields": {"total_amount": "100"}},
        ]
        cur = [
            {"is_duplicate": True, "fields": {"total_amount": "9"}},
            {"fields": {"total_amount": "120"}},
        ]
        out = diff.compute_field_corrections(ai, cur)
        self.assertEqual(
            out, [{"field_name": "total_amount", "ai_value": "100", "corrected_value": "120"}]
        )


class FewshotTests(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertFalse(fewshot.is_enabled())

    def test_empty_examples_no_block(self):
        self.assertEqual(fewshot.build_prompt_block([]), "")

    def test_block_contains_corrections(self):
        block = fewshot.build_prompt_block(
            [{"field_name": "invoice_number", "ai_value": "IV1", "corrected_value": "IV-001"}]
        )
        self.assertIn("invoice_number", block)
        self.assertIn("IV-001", block)
        self.assertTrue(block.endswith("\n\n"))

    def test_block_caps_examples(self):
        many = [{"field_name": f"f{i}", "ai_value": "a", "corrected_value": "b"} for i in range(50)]
        block = fewshot.build_prompt_block(many)
        # 标题 1 行 + 最多 _MAX_EXAMPLES 行
        body_lines = [ln for ln in block.strip().splitlines() if ln.startswith("- ")]
        self.assertEqual(len(body_lines), fewshot._MAX_EXAMPLES)


if __name__ == "__main__":
    unittest.main()
