# -*- coding: utf-8 -*-
"""管家万能口 · 认料层(services/steward/attach_kinds.py)。

锁的是「判不准就说判不准」这条红线:确定性信号全落空时必须落 unknown + 两个候选动作
(= 出卡问人),绝不回落成一个像样的类型名;以及 VAT 报告 vs 销项汇总的判据先后
——sort 那份 _head_is_sales 词表含 ภาษีขาย,报表判据排后面会把 ภ.พ.30 附表判成 POS 汇总。
"""

from __future__ import annotations

import io
import unittest
from unittest import mock

from services.steward import attach_kinds as ak
from services.steward.attachments import SOURCE_RULE, SOURCE_UNKNOWN

_USER = {"id": "u1", "tenant_id": "t-1"}
_QUOTE_OK = {"allowed": True, "error_code": None, "kind": "pdf", "units": 1, "page_count": 1}


def _xlsx(header_cells) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active.append(list(header_cells))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _quote(**over):
    raw = {**_QUOTE_OK, "is_exempt": False, **over}
    return mock.patch("services.ocr.entrypoints.billing_quote", return_value=raw)


class FormatGateTests(unittest.TestCase):
    def test_extension_outside_whitelist_is_refused_not_guessed(self):
        with _quote():
            out = ak.detect(b"MZ\x00", "installer.exe", user=_USER)
        self.assertEqual(out.kind, ak.UNSUPPORTED)
        self.assertEqual(out.actions, ())
        self.assertIn("unsupported_format", out.kind_reason)
        self.assertFalse(out.auto_runnable)

    def test_broken_pdf_is_refused_by_the_quote_gate(self):
        with _quote(allowed=False, error_code="ocr.invalid_pdf", page_count=0):
            out = ak.detect(b"%PDF-broken", "x.pdf", user=_USER)
        self.assertEqual(out.kind, ak.UNSUPPORTED)
        self.assertEqual(out.kind_reason, "ocr.invalid_pdf")

    def test_quote_failure_does_not_sink_the_upload(self):
        """报价炸了是「报不出价」,不是「这份料进不来」——料照收,页数如实缺。"""
        with mock.patch(
            "services.ocr.entrypoints.billing_quote", side_effect=RuntimeError("db down")
        ):
            out = ak.detect(_xlsx(["สมุดแยกประเภท"]), "ledger.xlsx", user=_USER)
        self.assertEqual(out.kind, ak.GL_LEDGER)
        self.assertEqual(out.quote["error_code"], "quote_unavailable")


class SheetTests(unittest.TestCase):
    def test_gl_by_filename(self):
        with _quote(kind="excel"):
            out = ak.detect(_xlsx(["a", "b"]), "2569-06 GL.xlsx", user=_USER)
        self.assertEqual(out.kind, ak.GL_LEDGER)
        self.assertEqual(out.kind_source, SOURCE_RULE)
        self.assertTrue(out.auto_runnable)

    def test_bank_by_header(self):
        with _quote(kind="excel"):
            out = ak.detect(_xlsx(["วันที่", "ถอน", "ฝาก"]), "export.xlsx", user=_USER)
        self.assertEqual(out.kind, ak.BANK_STATEMENT)

    def test_vat_report_wins_over_sales_summary_on_the_shared_keyword(self):
        """ภาษีขาย 同时命中 sort._head_is_sales —— 报表判据必须排在汇总表之前。"""
        with _quote(kind="excel"):
            out = ak.detect(_xlsx(["เลขที่", "ยอดขาย", "ภาษีขาย"]), "export.xlsx", user=_USER)
        self.assertEqual(out.kind, ak.VAT_REPORT)
        self.assertEqual(out.actions, ("vat_report_check",))

    def test_sales_summary_by_filename(self):
        with _quote(kind="excel"):
            out = ak.detect(_xlsx(["a"]), "สรุปยอดขาย 06.xlsx", user=_USER)
        self.assertEqual(out.kind, ak.SALES_SUMMARY)

    def test_unrecognisable_sheet_is_unknown_and_never_auto_runs(self):
        with _quote(kind="excel"):
            out = ak.detect(_xlsx(["col1", "col2"]), "export.xlsx", user=_USER)
        self.assertEqual(out.kind, ak.UNKNOWN)
        self.assertEqual(out.kind_source, SOURCE_UNKNOWN)
        self.assertIn("table_kind_unclear", out.kind_reason)
        self.assertEqual(len(out.actions), 2)  # 两条路都可能 → 必须问
        self.assertFalse(out.auto_runnable)


class PdfTests(unittest.TestCase):
    def _detect(self, name, pages, doc_type="generic_table"):
        with (
            _quote(page_count=3),
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=pages),
            mock.patch("services.fileconv.classify.classify", return_value=doc_type),
        ):
            return ak.detect(b"%PDF-1.4", name, user=_USER)

    def test_text_layer_gl_runs_straight_through(self):
        out = self._detect("report.pdf", ["x" * 200], doc_type="gl_ledger")
        self.assertEqual(out.kind, ak.GL_LEDGER)
        self.assertFalse(out.needs_model)
        self.assertTrue(out.auto_runnable)

    def test_scanned_pdf_is_unknown_and_flagged_as_model_spend(self):
        out = self._detect("scan.pdf", ["", ""])
        self.assertEqual(out.kind, ak.UNKNOWN)
        self.assertTrue(out.needs_model)
        self.assertFalse(out.auto_runnable)
        self.assertEqual(out.kind_reason, "pdf_no_text_layer")

    def test_generic_table_is_not_dressed_up_as_a_recognised_kind(self):
        out = self._detect("something.pdf", ["x" * 200], doc_type="generic_table")
        self.assertEqual(out.kind, ak.UNKNOWN)
        self.assertEqual(out.kind_reason, "pdf_kind_unclear")


class VatModelSpendTests(unittest.TestCase):
    """销项报告的 needs_model 必须把 parse_vat_report 的模型回退算进去 —— 那是「按钮说不
    过模型、执行侧却调了一次」的成因,而按钮上的 cost.model_call 直接读这个字段。"""

    def _rows(self, n):
        return [
            {"report_invoice_no": f"IV69/{i:05d}", "report_ref_no": ""} for i in range(1, n + 1)
        ]

    def _probe(self, table_rows, regex_rows):
        return (
            mock.patch(
                "services.vat.vat_parser_pdf.parse_pdf_text",
                return_value={"rows": self._rows(table_rows)},
            ),
            mock.patch(
                "services.vat.vat_parser_pdf._parse_vat_pdf_text_lines",
                return_value=self._rows(regex_rows),
            ),
        )

    def test_excel_report_reads_locally_and_stays_zero_click(self):
        self.assertFalse(ak.vat_check_needs_model(b"", "รายงานภาษีขาย 06.xlsx"))

    def test_csv_report_goes_through_the_ocr_pipeline_so_it_costs_a_model_call(self):
        """csv/docx/txt/tiff 在 parse_vat_report 里一律走 pipeline —— 那就是过模型。"""
        self.assertTrue(ak.vat_check_needs_model(b"a,b\n", "รายงานภาษีขาย 06.csv"))

    def test_pdf_whose_tables_extract_needs_no_model(self):
        p1, p2 = self._probe(table_rows=5, regex_rows=0)
        with p1, p2:
            self.assertFalse(ak.vat_check_needs_model(b"%PDF", "vat.pdf"))

    def test_pdf_falls_back_to_the_line_regex_before_calling_it_a_spend(self):
        p1, p2 = self._probe(table_rows=1, regex_rows=4)
        with p1, p2:
            self.assertFalse(ak.vat_check_needs_model(b"%PDF", "vat.pdf"))

    def test_text_layer_pdf_whose_tables_come_out_empty_is_a_model_spend(self):
        """泰文声调错位的电子版 PDF:有文字层但两条确定性路都出不到 3 行 → 回退 Gemini。"""
        p1, p2 = self._probe(table_rows=1, regex_rows=1)
        with p1, p2:
            self.assertTrue(ak.vat_check_needs_model(b"%PDF", "vat.pdf"))

    def test_probe_failure_counts_as_a_spend_rather_than_deciding_for_her(self):
        with mock.patch(
            "services.vat.vat_parser_pdf.parse_pdf_text", side_effect=RuntimeError("pdfplumber")
        ):
            self.assertTrue(ak.vat_check_needs_model(b"%PDF", "vat.pdf"))

    def test_detect_marks_the_garbled_report_pdf_as_needing_a_model(self):
        p1, p2 = self._probe(table_rows=0, regex_rows=0)
        with (
            _quote(page_count=3),
            mock.patch("services.fileconv.text_layer.extract_pages", return_value=["x" * 200]),
            mock.patch("services.fileconv.classify.classify", return_value="vat_report"),
            p1,
            p2,
        ):
            out = ak.detect(b"%PDF-1.4", "รายงานภาษีขาย.pdf", user=_USER)
        self.assertEqual(out.kind, ak.VAT_REPORT)
        self.assertTrue(out.needs_model)
        self.assertFalse(out.auto_runnable)  # 出确认卡,不静默开跑


class ImageTests(unittest.TestCase):
    def test_image_is_a_receipt_that_costs_a_model_call(self):
        with _quote():
            out = ak.detect(b"\xff\xd8\xff", "IMG_2647.jpg", user=_USER)
        self.assertEqual(out.kind, ak.INVOICE)
        self.assertTrue(out.needs_model)
        self.assertEqual(out.actions, ())  # F1 对话里还没有识别入库,不摆假按钮
        self.assertFalse(out.auto_runnable)


class DetectPayloadTests(unittest.TestCase):
    def test_to_detect_carries_everything_the_frontend_contract_needs(self):
        with _quote(page_count=7):
            payload = ak.detect(b"\xff\xd8\xff", "a.jpg", user=_USER).to_detect()
        self.assertEqual(sorted(payload), ["actions", "needs_model", "page_count", "quote"])
        self.assertEqual(payload["page_count"], 7)


if __name__ == "__main__":
    unittest.main()
