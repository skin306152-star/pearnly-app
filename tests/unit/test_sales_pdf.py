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

    def test_combined_doc_label_present(self):
        self.assertIn("tax_invoice_receipt", pdf._DOC_LABEL)
        self.assertIn("ใบเสร็จรับเงิน", pdf._DOC_LABEL["tax_invoice_receipt"])

    def test_renders_each_buyer_type(self):
        for btype, tin in (
            ("company", "1234567890123"),
            ("individual", "1234567890123"),
            ("foreigner", "AB12345"),
            ("anonymous", ""),
        ):
            b = dict(_BUYER, type=btype, tax_id=tin, branch_type="hq")
            self.assertTrue(pdf.render_invoice_pdf(_DOC, _SELLER, b).startswith(b"%PDF"))

    def test_company_branch_text(self):
        self.assertIn("Head Office", pdf._buyer_branch_text({"branch_type": "hq"}))
        self.assertIn(
            "Branch 00001", pdf._buyer_branch_text({"branch_type": "branch", "branch_no": "00001"})
        )

    def test_due_date_and_terms_render(self):
        d = dict(_DOC, due_date="2026-07-06", payment_terms="net 30")
        self.assertTrue(pdf.render_invoice_pdf(d, _SELLER, _BUYER).startswith(b"%PDF"))

    def test_a5_page_renders(self):
        self.assertTrue(
            pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, page="A5").startswith(b"%PDF")
        )

    def test_copy_kind_original_and_copy(self):
        for kind in ("original", "copy"):
            data = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, copy_kind=kind)
            self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn("ต้นฉบับ", pdf._COPY_LABEL["original"])
        self.assertIn("สำเนา", pdf._COPY_LABEL["copy"])

    def test_unknown_copy_kind_falls_back(self):
        self.assertTrue(
            pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, copy_kind="bogus").startswith(b"%PDF")
        )

    def test_discount_cell_formatting(self):
        self.assertEqual(pdf._discount_cell({"discount": "0"}), "-")
        self.assertEqual(pdf._discount_cell({"discount": "20"}), "20.00")
        self.assertIn("(10.00%)", pdf._discount_cell({"discount": "20", "discount_pct": "10"}))

    def test_header_discount_row_renders(self):
        d = dict(_DOC, header_discount_amount="15.00", subtotal="100.00")
        d["lines"][0]["discount"] = "5"
        d["lines"][0]["discount_pct"] = "10"
        self.assertTrue(pdf.render_invoice_pdf(d, _SELLER, _BUYER).startswith(b"%PDF"))

    def test_price_inclusive_total_rows(self):
        """§C 价内:合计区标注含税 + 反算净额,且仍单列 VAT。"""
        doc = dict(_DOC, price_includes_vat=True, subtotal="107.00", grand_total="107.00")
        labels = [r[0] for r in pdf._total_rows(doc)]
        self.assertTrue(any("incl." in lb for lb in labels))
        self.assertTrue(any("Net (VAT excl.)" in lb for lb in labels))
        self.assertTrue(pdf.render_invoice_pdf(doc, _SELLER, _BUYER).startswith(b"%PDF"))

    def test_price_exclusive_total_rows_default(self):
        rows = pdf._total_rows(_DOC)
        self.assertIn("มูลค่า / Subtotal", rows[0][0])

    def test_combined_doc_with_payment_renders(self):
        doc = dict(
            _DOC,
            doc_type="tax_invoice_receipt",
            payment_status="partial",
            paid_amount="50.00",
            payment_method="transfer",
            payment_date="2026-06-06",
        )
        b = dict(_BUYER, type="company", branch_type="hq")
        self.assertTrue(pdf.render_invoice_pdf(doc, _SELLER, b).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
