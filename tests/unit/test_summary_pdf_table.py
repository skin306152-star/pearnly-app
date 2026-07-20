# -*- coding: utf-8 -*-
"""PDF 汇总表适配器守门测试(services/summary_import/pdf_table.py)。

真 PDF 端到端(reportlab 现造 → pdfplumber 抽 → pdf_grid 切 → R2 聚合),不靠 mock 自证;
泰文表头与降级线用注入的文字层覆盖。仓内没有 7-11 PDF 语料,故用合成 PDF(见 §报告)。

此前 classify 把 PDF 字节直丢 parse_table,CSV 引擎的 latin-1 兜底会把它解成逐行垃圾
(实测 121 行、status=ok)一路静默进销项。这里锁住:读不出就返空 + reason,绝不返半真。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.fileconv import pdf_grid
from services.summary_import import pdf_table
from services.workorder.steps import reconcile_gates as gates
from tests.unit.test_fileconv_pdf_grid import BODY, HEADER, _bordered_pdf, _borderless_pdf


class RealPdfTests(unittest.TestCase):
    def test_bordered_pdf_yields_parse_table_contract(self):
        out = pdf_table.parse_pdf_table(_bordered_pdf(), filename="sales.pdf")
        self.assertIsNone(out["reason"])
        self.assertEqual(out["source"], pdf_table.SOURCE)
        self.assertEqual(out["level"], pdf_grid.LEVEL_TABLE)
        self.assertFalse(out["degraded"])
        self.assertEqual(out["headers"], HEADER)
        self.assertEqual(out["row_count"], len(BODY))
        self.assertEqual(set(out["rows"][0]), {"index", "cells", "is_summary"})
        self.assertTrue(out["rows"][-1]["is_summary"])

    def test_r2_aggregation_from_real_pdf(self):
        out = pdf_table.parse_pdf_table(_bordered_pdf(), filename="sales.pdf")
        agg = gates.aggregate_sales({"p1": out})
        self.assertTrue(agg["used"])
        self.assertEqual(agg["sales_amount"], Decimal("239279.40"))
        self.assertEqual(agg["output_vat"], Decimal("16749.56"))
        self.assertEqual(agg["total_check"], gates.TOTAL_CHECK_MATCHED)

    def test_borderless_pdf_still_reads_but_marks_degraded(self):
        """列位是坐标推断出来的 → 数字照样对,但 degraded 留痕,上层别当同等可靠。"""
        out = pdf_table.parse_pdf_table(_borderless_pdf(), filename="sales.pdf")
        self.assertEqual(out["level"], pdf_grid.LEVEL_CLUSTER)
        self.assertTrue(out["degraded"])
        agg = gates.aggregate_sales({"p1": out})
        self.assertEqual(agg["sales_amount"], Decimal("239279.40"))
        self.assertEqual(agg["total_check"], gates.TOTAL_CHECK_MATCHED)

    def test_garbage_and_empty_bytes_produce_nothing(self):
        for raw in (b"", b"%PDF-1.4 not really a pdf", b"\x00\x01\x02"):
            out = pdf_table.parse_pdf_table(raw, filename="x.pdf")
            self.assertEqual(out["reason"], pdf_table.REASON_NO_TEXT_LAYER)
            self.assertEqual(out["rows"], [])
            self.assertEqual(out["headers"], [])
            self.assertFalse(gates.aggregate_sales({"p1": out})["used"])


def _with_pages(pages):
    return mock.patch.object(pdf_table, "extract_pages", return_value=pages)


class TextLayerBranchTests(unittest.TestCase):
    def test_scanned_pdf_degrades_honestly(self):
        """无文字层(扫描件)→ no_text_layer,交 OCR 路/人工,不臆造一行。"""
        with _with_pages(["", "  ", ""]):
            out = pdf_table.parse_pdf_table(b"x", filename="scan.pdf")
        self.assertEqual(out["reason"], pdf_table.REASON_NO_TEXT_LAYER)
        self.assertEqual(out["row_count"], 0)

    def test_extract_failure_degrades_honestly(self):
        with _with_pages(None):
            out = pdf_table.parse_pdf_table(b"x", filename="scan.pdf")
        self.assertEqual(out["reason"], pdf_table.REASON_NO_TEXT_LAYER)

    def test_text_without_column_structure_is_refused(self):
        """有字但切不出列(整行一格)→ unstructured,不返一张 N×1 的假表。"""
        page = "\n".join(["1 19,220.00 6.07 116,665.40 8,166.58 124,831.98"] * 4)
        with _with_pages([page]):
            out = pdf_table.parse_pdf_table(b"x", filename="flat.pdf")
        self.assertEqual(out["reason"], pdf_table.REASON_UNSTRUCTURED)
        self.assertEqual(out["rows"], [])

    def test_thai_columnar_text_layer(self):
        page = "\n".join(
            [
                "สรุปยอดขาย เดือน กรกฎาคม 2569",
                "วันที่      ยอด        ราคา      ยอดเงินก่อน vat    ยอดเงิน vat    ยอดเงินรวม",
                "1           19220      6.07      116665.40          8166.58        124831.98",
                "2           20200      6.07      122614.00          8582.98        131196.98",
                "ยอดรวมทั้งหมด                     239279.40          16749.56       256028.96",
            ]
        )
        with _with_pages([page]):
            out = pdf_table.parse_pdf_table(b"x", filename="ice.pdf")
        self.assertIsNone(out["reason"])
        self.assertEqual(out["level"], pdf_grid.LEVEL_SPLIT)
        self.assertEqual(out["headers"][3], "ยอดเงินก่อน vat")
        agg = gates.aggregate_sales({"p1": out})
        self.assertEqual(agg["sales_amount"], Decimal("239279.40"))
        self.assertEqual(agg["output_vat"], Decimal("16749.56"))
        self.assertEqual(agg["total_check"], gates.TOTAL_CHECK_MATCHED)

    def test_preamble_feeds_period_detection(self):
        page = "\n".join(
            [
                "สรุปยอดขาย เดือน กรกฎาคม 2569",
                "วันที่      ยอดขาย       ภาษีขาย",
                "1           100.00       7.00",
                "2           200.00       14.00",
            ]
        )
        with _with_pages([page]):
            out = pdf_table.parse_pdf_table(b"x", filename="ice.pdf")
        self.assertIn("สรุปยอดขาย", out["preamble"])
        self.assertEqual(out["suggested_period"], [2026, 7])


if __name__ == "__main__":
    unittest.main()
