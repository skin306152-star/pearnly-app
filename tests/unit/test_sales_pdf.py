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

    def test_wht_label_shows_rate(self):
        """§L2:WHT 行标签带档率,如 'หัก ณ ที่จ่าย 3%'。"""
        doc = dict(_DOC, wht_amount="27.00", wht_rate="3")
        wht_row = [r for r in pdf._total_rows(doc) if "หัก ณ ที่จ่าย" in r[0]]
        self.assertEqual(len(wht_row), 1)
        self.assertIn("3%", wht_row[0][0])

    def test_credit_note_label(self):
        self.assertIn("credit_note", pdf._DOC_LABEL)
        self.assertIn("ใบลดหนี้", pdf._DOC_LABEL["credit_note"])

    def test_combined_doc_label_present(self):
        self.assertIn("tax_invoice_receipt", pdf._DOC_LABEL)
        label = pdf._doc_label("tax_invoice_receipt", pdf._label_fn("th_en"))
        self.assertIn("ใบเสร็จรับเงิน", label)

    def test_doc_language_switches_secondary_label(self):
        # 泰文恒在;次语随 doc_language:th=仅泰 / th_en=泰+英 / th_zh=泰+中。
        self.assertEqual(pdf._doc_label("tax_invoice", pdf._label_fn("th")), "ใบกำกับภาษี")
        self.assertIn("Tax Invoice", pdf._doc_label("tax_invoice", pdf._label_fn("th_en")))
        self.assertIn("税务发票", pdf._doc_label("tax_invoice", pdf._label_fn("th_zh")))
        rows_zh = pdf._total_rows(dict(_DOC), "th_zh")
        joined = " ".join(r[0] for r in rows_zh)
        self.assertIn("增值税", joined)
        self.assertIn("合计", joined)
        for lang in ("th", "th_en", "th_zh"):
            self.assertTrue(
                pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, lang=lang).startswith(b"%PDF")
            )

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
        L = pdf._label_fn("th_en")
        self.assertIn("Head Office", pdf._buyer_branch_text({"branch_type": "hq"}, L))
        self.assertIn(
            "Branch 00001",
            pdf._buyer_branch_text({"branch_type": "branch", "branch_no": "00001"}, L),
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

    def test_two_up_renders_single_page_pdf(self):
        """§E2 省纸:正副本同页,返回有效 PDF。"""
        data = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, copies_layout="two_up")
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 800)

    def test_two_up_a5_renders(self):
        data = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, page="A5", copies_layout="two_up")
        self.assertTrue(data.startswith(b"%PDF"))

    def test_separate_layout_is_default(self):
        data = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, copies_layout="separate")
        self.assertTrue(data.startswith(b"%PDF"))

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

    def test_thermal_80_and_58_render(self):
        """§E1 热敏窄版:80/58mm 走单列布局,返回有效 PDF。"""
        for pg in ("thermal_80", "thermal_58"):
            data = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, page=pg)
            self.assertTrue(data.startswith(b"%PDF"), pg)

    def test_thermal_receipt_with_payment_renders(self):
        doc = dict(
            _DOC,
            doc_type="tax_invoice_receipt",
            payment_status="paid",
            paid_amount="107.00",
            payment_method="cash",
            payment_date="2026-06-06",
        )
        b = dict(_BUYER, type="anonymous")
        self.assertTrue(
            pdf.render_invoice_pdf(doc, _SELLER, b, page="thermal_80").startswith(b"%PDF")
        )

    def test_thermal_two_up_falls_back(self):
        """热敏不支持 two_up:回落单联,仍出有效 PDF(§E2)。"""
        data = pdf.render_invoice_pdf(
            _DOC, _SELLER, _BUYER, page="thermal_80", copies_layout="two_up"
        )
        self.assertTrue(data.startswith(b"%PDF"))

    def test_archival_sha256_deterministic(self):
        """§E3 留底:确定性渲染同输入同哈希,可复算核验未篡改。"""
        h1 = pdf.archival_sha256(_DOC, _SELLER, _BUYER)
        h2 = pdf.archival_sha256(_DOC, _SELLER, _BUYER)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_archival_sha256_changes_with_content(self):
        h1 = pdf.archival_sha256(_DOC, _SELLER, _BUYER)
        h2 = pdf.archival_sha256(dict(_DOC, grand_total="999.00"), _SELLER, _BUYER)
        self.assertNotEqual(h1, h2)

    def test_deterministic_flag_reproduces_bytes(self):
        a = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, deterministic=True)
        b = pdf.render_invoice_pdf(_DOC, _SELLER, _BUYER, deterministic=True)
        self.assertEqual(a, b)

    def test_brand_template_and_footer_render(self):
        """§L4:品牌色模板 + 页脚文字渲染为有效 PDF。"""
        seller = dict(
            _SELLER, template_id="brand", brand_color="#10b981", footer_text="ขอบคุณที่ใช้บริการ"
        )
        for tid in ("classic", "minimal", "brand", "compact", "thai_official", "mono"):
            s = dict(seller, template_id=tid)
            self.assertTrue(pdf.render_invoice_pdf(_DOC, s, _BUYER).startswith(b"%PDF"), tid)

    def test_invalid_brand_color_does_not_crash(self):
        seller = dict(_SELLER, template_id="brand", brand_color="garbage")
        self.assertTrue(pdf.render_invoice_pdf(_DOC, seller, _BUYER).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
