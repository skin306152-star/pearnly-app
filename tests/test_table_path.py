# -*- coding: utf-8 -*-
"""
tests/test_table_path.py

Locks down the Excel/CSV/Word direct-read path (no OCR) added in the
2026-05-21 multi-schema refactor. The contract: structured table_rows +
table_headers preserved so Layer 2's GL prompt can identify the Debit /
Credit columns by header — Excel/CSV must NEVER be sent through Vision OCR.
"""
import csv
import io
import unittest

from services.ocr.table_path import (
    SUPPORTED_TABLE_EXTENSIONS,
    extract_from_table_file,
)


class TablePathExcelTests(unittest.TestCase):

    def setUp(self):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "GL"
        ws.append(["Date", "Voucher No.", "Account Code", "Description",
                   "Debit", "Credit", "Balance"])
        ws.append(["2026-05-21", "JV681130.1", "1112-07",
                   "6091 - Sales revenue", 1500.00, None, 10000.00])
        ws.append(["2026-05-22", "JV681130.2", "5001-01",
                   "Office supplies", None, 250.00, 9750.00])
        buf = io.BytesIO()
        wb.save(buf)
        self.xlsx_bytes = buf.getvalue()

    def test_excel_returns_one_page_per_sheet(self):
        res = extract_from_table_file(self.xlsx_bytes, "gl.xlsx")
        self.assertEqual(res.page_count, 1)
        self.assertEqual(res.engine, "table_path_excel")

    def test_excel_preserves_column_headers(self):
        res = extract_from_table_file(self.xlsx_bytes, "gl.xlsx")
        page = res.pages[0]
        self.assertEqual(
            page.table_headers,
            ["Date", "Voucher No.", "Account Code", "Description",
             "Debit", "Credit", "Balance"],
        )

    def test_excel_6091_stays_in_description_row(self):
        """The critical contract: 6091 in the Description cell stays
        attached to the Description column header — Layer 2's prompt then
        knows it's NOT an amount."""
        res = extract_from_table_file(self.xlsx_bytes, "gl.xlsx")
        page = res.pages[0]
        row0 = page.table_rows[0]
        self.assertEqual(row0["Description"], "6091 - Sales revenue")
        self.assertEqual(row0["Debit"], "1500")
        self.assertEqual(row0["Credit"], "")

    def test_excel_full_text_renders_pipe_grid(self):
        res = extract_from_table_file(self.xlsx_bytes, "gl.xlsx")
        page = res.pages[0]
        self.assertIn("Debit", page.full_text)
        self.assertIn("6091 - Sales revenue", page.full_text)

    def test_avg_confidence_is_one(self):
        """Direct read — no OCR uncertainty."""
        res = extract_from_table_file(self.xlsx_bytes, "gl.xlsx")
        self.assertEqual(res.pages[0].avg_confidence, 1.0)


class TablePathCSVTests(unittest.TestCase):

    def test_csv_with_utf8_bom_and_thai_content(self):
        rows = [
            ["วันที่", "ใบสำคัญ", "รายการ", "เดบิต", "เครดิต"],
            ["2026-05-21", "JV001", "6091 ขายสินค้า", "1500.00", ""],
            ["2026-05-22", "JV002", "ค่าน้ำ", "", "250.00"],
        ]
        buf = io.StringIO()
        writer = csv.writer(buf)
        for r in rows:
            writer.writerow(r)
        # UTF-8 BOM
        csv_bytes = ("﻿" + buf.getvalue()).encode("utf-8")

        res = extract_from_table_file(csv_bytes, "gl.csv")
        self.assertEqual(res.engine, "table_path_csv")
        page = res.pages[0]
        self.assertEqual(page.table_headers,
                         ["วันที่", "ใบสำคัญ", "รายการ", "เดบิต", "เครดิต"])
        self.assertEqual(page.table_rows[0]["รายการ"], "6091 ขายสินค้า")
        self.assertEqual(page.table_rows[0]["เดบิต"], "1500.00")

    def test_csv_skips_blank_rows(self):
        text = "h1,h2\n,\nA,B\n,,\n"
        res = extract_from_table_file(text.encode("utf-8"), "x.csv")
        self.assertEqual(len(res.pages[0].table_rows), 1)


class TablePathDispatchTests(unittest.TestCase):

    def test_supported_extensions_cover_user_request(self):
        for required in (".xlsx", ".xls", ".csv", ".tsv", ".docx", ".doc", ".txt"):
            self.assertIn(required, SUPPORTED_TABLE_EXTENSIONS,
                          f"{required} must be in SUPPORTED_TABLE_EXTENSIONS")

    def test_unsupported_extension_raises(self):
        with self.assertRaises(ValueError):
            extract_from_table_file(b"x", "weird.png")

    def test_empty_bytes_raises(self):
        with self.assertRaises(ValueError):
            extract_from_table_file(b"", "gl.csv")


if __name__ == "__main__":
    unittest.main()
