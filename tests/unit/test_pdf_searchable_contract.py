# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 可搜索文本提取 pdf_searchable.py 行为契约

pdf_searchable.extract_searchable_text_from_pages(从 OCR 结果聚合每页搜索文本)
此前 0 专属测试。纯函数 · 无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。
跳过 make_searchable_pdf(PyMuPDF 重依赖)· health_check 只验返回结构。
"""

import unittest

import pdf_searchable as ps


class ExtractSearchableTextTests(unittest.TestCase):
    def test_empty_returns_empty_list(self):
        self.assertEqual(ps.extract_searchable_text_from_pages([]), [])
        self.assertEqual(ps.extract_searchable_text_from_pages(None), [])

    def test_length_matches_pages(self):
        pages = [{"raw_text": "a"}, {}, {"raw_text": "b"}]
        out = ps.extract_searchable_text_from_pages(pages)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[1], "")  # 空页 → 空串

    def test_raw_text_included(self):
        out = ps.extract_searchable_text_from_pages([{"raw_text": "  hello world  "}])
        self.assertEqual(out[0], "hello world")

    def test_fields_included(self):
        pages = [
            {"fields": {"invoice_number": "INV1", "total_amount": "1070", "buyer_name": "ACME"}}
        ]
        text = ps.extract_searchable_text_from_pages(pages)[0]
        self.assertIn("INV1", text)
        self.assertIn("1070", text)
        self.assertIn("ACME", text)

    def test_items_included(self):
        pages = [{"fields": {"items": [{"description": "Coffee", "qty": 2, "amount": 1000}]}}]
        text = ps.extract_searchable_text_from_pages(pages)[0]
        self.assertIn("Coffee", text)
        self.assertIn("2", text)
        self.assertIn("1000", text)

    def test_none_values_skipped(self):
        pages = [{"fields": {"invoice_number": "INV1", "total_amount": None, "vat_amount": ""}}]
        text = ps.extract_searchable_text_from_pages(pages)[0]
        self.assertEqual(text, "INV1")  # None / 空串都不进

    def test_combines_raw_fields_items(self):
        pages = [
            {
                "raw_text": "RAW",
                "fields": {"invoice_number": "INV1", "items": [{"name": "X"}]},
            }
        ]
        text = ps.extract_searchable_text_from_pages(pages)[0]
        self.assertIn("RAW", text)
        self.assertIn("INV1", text)
        self.assertIn("X", text)


class HealthCheckTests(unittest.TestCase):
    def test_returns_structure(self):
        info = ps.health_check()
        self.assertIn("pymupdf_available", info)
        self.assertIsInstance(info["pymupdf_available"], bool)


if __name__ == "__main__":
    unittest.main()
