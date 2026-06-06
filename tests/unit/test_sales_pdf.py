# -*- coding: utf-8 -*-
"""销项 PO-6 · 发票 PDF 渲染守门(返回有效 PDF · 卖买方/明细容错)。"""

import unittest

from services.sales import pdf

_DOC = {
    "doc_type": "tax_invoice",
    "doc_number": "INV2026-00001",
    "issue_date": "2026-06-06",
    "currency": "THB",
    "subtotal": "100.00",
    "vat_rate": "7.00",
    "vat_amount": "7.00",
    "wht_amount": "0.00",
    "grand_total": "107.00",
    "lines": [
        {
            "line_no": 1,
            "description": "น้ำดื่ม",
            "qty": "2",
            "unit_price": "50",
            "line_total": "100.00",
        }
    ],
}
_SELLER = {
    "name": "บริษัท เอ จำกัด",
    "tax_id": "0105551234567",
    "address": "123 ถนนสุขุมวิท กรุงเทพฯ",
    "branch": "สำนักงานใหญ่",
    "phone": "021234567",
}
_BUYER = {"name": "ลูกค้า บี", "tax_id": "0105557654321", "address": "456 เชียงใหม่"}


class PdfRenderTests(unittest.TestCase):
    def test_renders_valid_pdf(self):
        data = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER)
        self.assertTrue(data.startswith(b"%PDF"), "应为有效 PDF 字节")
        self.assertGreater(len(data), 800)

    def test_tolerates_missing_seller_and_buyer(self):
        data = pdf.render_invoice_pdf(_DOC, None, None)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_wht_line_only_when_nonzero(self):
        doc = dict(_DOC, wht_amount="9.00")
        self.assertTrue(pdf.render_invoice_pdf(doc, _SELLER, _BUYER).startswith(b"%PDF"))

    def test_credit_note_label(self):
        self.assertIn("credit_note", pdf._DOC_LABEL)
        self.assertIn("ใบลดหนี้", pdf._DOC_LABEL["credit_note"])


if __name__ == "__main__":
    unittest.main()
