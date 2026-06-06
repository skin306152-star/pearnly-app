# -*- coding: utf-8 -*-
"""销项 §L3 · 报价单转换守门(目标类型 + 原单存在/类型校验 · 不连库)。"""

import unittest

from services.sales import quotation


class QuoteCursor:
    """假游标:对单据 SELECT 回 self.doc,明细 SELECT 回 []。"""

    def __init__(self, doc):
        self.doc = doc
        self._mode = None

    def execute(self, sql, params=None):
        if "sales_document_lines" in sql:
            self._mode = "lines"
        elif sql.strip().startswith("SELECT") and "FROM sales_documents" in sql:
            self._mode = "doc"

    def fetchone(self):
        return self.doc if self._mode == "doc" else None

    def fetchall(self):
        return []


class ConvertQuotationTests(unittest.TestCase):
    def test_bad_target_type_rejected(self):
        _, err = quotation.convert_quotation(
            QuoteCursor(None), tenant_id="t", created_by="u", quote_id="q", target_doc_type="bogus"
        )
        self.assertEqual(err, "bad_target_type")

    def test_original_not_found(self):
        _, err = quotation.convert_quotation(
            QuoteCursor(None),
            tenant_id="t",
            created_by="u",
            quote_id="q",
            target_doc_type="tax_invoice",
        )
        self.assertEqual(err, "original_not_found")

    def test_non_quotation_rejected(self):
        cur = QuoteCursor({"doc_type": "tax_invoice", "id": 1})
        _, err = quotation.convert_quotation(
            cur, tenant_id="t", created_by="u", quote_id="q", target_doc_type="tax_invoice"
        )
        self.assertEqual(err, "not_a_quotation")

    def test_convert_targets_are_invoice_types(self):
        self.assertIn("tax_invoice", quotation.CONVERT_TARGETS)
        self.assertIn("tax_invoice_receipt", quotation.CONVERT_TARGETS)
        self.assertNotIn("quotation", quotation.CONVERT_TARGETS)


if __name__ == "__main__":
    unittest.main()
