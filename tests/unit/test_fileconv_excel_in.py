# -*- coding: utf-8 -*-
"""K2 · services/fileconv/excel_in.py · Excel/CSV → ConvertResult。

GL 路走真实 openpyxl 合成台账(端到端,不桩 parse_gl_excel)验证守恒过;不平场景桩
parse_gl_excel 直接喂一组内部不自洽的 GlRow——bank_gl_excel.attach_running_balance
按定义把每行 balance 算成 opening+累计借贷,永远自洽,真实 xlsx 走不出"不平"路径,
桩是唯一能触达 validate_ledger 判不平分支的办法(测的是本模块的适配器代码,不是伪造
通过)。generic/xls/CSV/拒绝态各一。
"""

from __future__ import annotations

import io
import unittest
from datetime import date
from unittest import mock

from openpyxl import Workbook

from services.fileconv import excel_in
from services.fileconv.model import (
    GENERIC_TABLE,
    GL_LEDGER,
    ISSUE_GL_BALANCE_CHAIN,
    STATUS_OK,
    STATUS_UNSUPPORTED_FORMAT,
)
from services.recon.bank_recon_types import GlRow


def _xlsx_bytes(rows) -> bytes:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class GlConservedRoundtripTests(unittest.TestCase):
    """真实合成 GL xlsx(期初 + 借贷两行闭合)→ 端到端过守恒,零桩。"""

    def setUp(self):
        data = _xlsx_bytes(
            [
                ["Date", "Doc No", "Description", "Debit", "Credit", "Balance"],
                ["Opening", "", "", "", "", 1000.00],
                ["1/1/2026", "V001", "Sales", 500.00, 0, 1500.00],
                ["2/1/2026", "V002", "Payment", 0, 200.00, 1300.00],
            ]
        )
        self.result = excel_in.convert_excel(data, "gl.xlsx")

    def test_recognized_as_gl_and_conserved(self):
        self.assertEqual(self.result.doc_type, GL_LEDGER)
        self.assertEqual(self.result.status, STATUS_OK)
        self.assertTrue(self.result.conserved)
        self.assertEqual(self.result.issues, [])

    def test_stats_sums_are_faithful(self):
        stats = self.result.stats
        self.assertEqual(stats["engine"], "excel_gl")
        self.assertEqual(stats["row_count"], 2)
        self.assertEqual(stats["sum_debit"], "500.0")
        self.assertEqual(stats["sum_credit"], "200.0")
        self.assertEqual(stats["opening_balance"], "1000.0")
        self.assertEqual(stats["closing_balance"], "1300.0")

    def test_table_rows_carry_ledger_columns(self):
        table = self.result.tables[0]
        self.assertEqual(table.name, "GL Ledger")
        self.assertEqual(len(table.columns), 9)  # LEDGER_COLUMNS 定长契约
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(table.rows[0][3], "V001")  # doc_no 落位不变


class GlUnbalancedTests(unittest.TestCase):
    """桩 parse_gl_excel:直接构造一组余额链不自洽的 GlRow,验 issues 点名。"""

    def test_broken_chain_is_named_with_line_and_expected_actual(self):
        rows = [
            GlRow(
                date=date(2026, 1, 1),
                doc_no="V1",
                account_code="1140-01",
                description="ok",
                debit=100.0,
                credit=0.0,
                balance=1100.0,
            ),
            GlRow(
                date=date(2026, 1, 2),
                doc_no="V2",
                account_code="1140-01",
                description="bad",
                debit=0.0,
                credit=50.0,
                balance=999.0,  # 应为 1050
            ),
        ]
        parsed = {"ok": True, "rows": rows, "opening": 1000.0, "closing": 999.0, "row_count": 2}
        with mock.patch("services.recon.bank_gl_excel.parse_gl_excel", return_value=parsed):
            result = excel_in.convert_excel(b"stubbed-parser-ignores-bytes", "bad.xlsx")

        self.assertFalse(result.conserved)
        self.assertEqual(len(result.issues), 1)
        issue = result.issues[0]
        self.assertEqual(issue.kind, ISSUE_GL_BALANCE_CHAIN)
        self.assertEqual(issue.line_no, 2)
        self.assertEqual(issue.expected, "1050.0")
        self.assertEqual(issue.actual, "999.0")

    def test_true_account_code_still_shown_in_table_despite_single_chain_key(self):
        """链 key 统一单链(见 excel_in._gl_row 注),但显示列必须换回真实科目码。"""
        rows = [
            GlRow(
                date=date(2026, 1, 1),
                doc_no="V1",
                account_code="1140-01",
                description="a",
                debit=100.0,
                credit=0.0,
                balance=1100.0,
            ),
        ]
        parsed = {"ok": True, "rows": rows, "opening": 1000.0, "closing": 1100.0, "row_count": 1}
        with mock.patch("services.recon.bank_gl_excel.parse_gl_excel", return_value=parsed):
            result = excel_in.convert_excel(b"stub", "a.xlsx")
        self.assertEqual(result.tables[0].rows[0][0], "1140-01")
        self.assertEqual(result.stats["accounts"], ["1140-01"])


class GenericFallbackTests(unittest.TestCase):
    """认不出 GL 结构(无日期/借贷表头)→ generic 网格,诚实无守恒。"""

    def test_no_gl_headers_falls_back_to_generic_grid(self):
        data = _xlsx_bytes([["Name", "Amount", "Note"], ["Alice", 100, "hi"], ["Bob", 200, "yo"]])
        result = excel_in.convert_excel(data, "sheet.xlsx")
        self.assertEqual(result.doc_type, GENERIC_TABLE)
        self.assertEqual(result.status, STATUS_OK)
        self.assertEqual(result.issues, [])
        self.assertEqual(result.stats["engine"], "excel_grid")
        self.assertEqual(
            result.tables[0].rows,
            [["Name", "Amount", "Note"], ["Alice", 100, "hi"], ["Bob", 200, "yo"]],
        )

    def test_merged_cell_fills_top_left_value(self):
        wb = Workbook()
        ws = wb.active
        ws.append(["Name", "Amount"])
        ws.append(["merged-a", 5])
        ws.append(["merged-b", 6])
        ws.merge_cells("A2:A3")
        buf = io.BytesIO()
        wb.save(buf)
        # openpyxl 写合并格时只有左上角(A2)有值,A3 为空——写完再手动确认场景合理。
        result = excel_in.convert_excel(buf.getvalue(), "merged.xlsx")
        rows = result.tables[0].rows
        self.assertEqual(rows[1][0], "merged-a")
        self.assertEqual(rows[2][0], "merged-a")  # 合并格左上值回填,非空白

    def test_empty_sheet_is_skipped_not_crashed(self):
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Empty"
        ws2 = wb.create_sheet("Data")
        ws2.append(["A", "B"])
        ws2.append([1, 2])
        buf = io.BytesIO()
        wb.save(buf)
        result = excel_in.convert_excel(buf.getvalue(), "two_sheets.xlsx")
        self.assertEqual(len(result.tables), 1)
        self.assertEqual(result.tables[0].name, "Data")


class CsvFallbackTests(unittest.TestCase):
    def test_generic_csv_grid(self):
        data = "Name,Amount\r\nAlice,100\r\nBob,200\r\n".encode("utf-8")
        result = excel_in.convert_excel(data, "sheet.csv")
        self.assertEqual(result.doc_type, GENERIC_TABLE)
        self.assertEqual(result.stats["engine"], "excel_grid_csv")
        self.assertEqual(result.tables[0].rows[0], ["Name", "Amount"])


class XlsFallbackTests(unittest.TestCase):
    """老式 .xls:openpyxl 打不开,GL 路认不出时落 generic → 单独走 xlrd。"""

    def test_xls_rejected_when_xlrd_not_installed(self):
        real_import = __import__

        def fake_import(name, *a, **k):
            if name == "xlrd":
                raise ImportError("simulated: xlrd not installed")
            return real_import(name, *a, **k)

        with mock.patch("services.recon.bank_gl_excel.parse_gl_excel", return_value={"ok": False}):
            with mock.patch("builtins.__import__", side_effect=fake_import):
                result = excel_in.convert_excel(b"any bytes, xlrd import fails first", "old.xls")

        self.assertEqual(result.status, STATUS_UNSUPPORTED_FORMAT)
        self.assertEqual(result.stats["reason"], "xls_requires_resave")

    def test_xls_grid_read_via_xlrd_when_available(self):
        """xlrd 装了但 GL 认不出结构 → generic 网格,合并格同样左上值回填。"""

        class _FakeSheet:
            name = "Sheet1"
            nrows = 3
            ncols = 2
            merged_cells = [(1, 3, 0, 1)]  # 行 1-2(0-based)、列 0 合并

            def cell_value(self, r, c):
                grid = [["Name", "Amount"], ["merged", 5], ["", 6]]
                return grid[r][c]

        class _FakeWorkbook:
            def sheets(self):
                return [_FakeSheet()]

        with mock.patch("services.recon.bank_gl_excel.parse_gl_excel", return_value={"ok": False}):
            with mock.patch("xlrd.open_workbook", return_value=_FakeWorkbook()):
                result = excel_in.convert_excel(b"fake xls bytes", "old.xls")

        self.assertEqual(result.doc_type, GENERIC_TABLE)
        self.assertEqual(result.stats["engine"], "excel_grid_xls")
        rows = result.tables[0].rows
        self.assertEqual(rows[1][0], "merged")
        self.assertEqual(rows[2][0], "merged")  # 合并格左上值回填


class RejectTests(unittest.TestCase):
    def test_empty_file_is_rejected_honestly(self):
        result = excel_in.convert_excel(b"", "empty.xlsx")
        self.assertEqual(result.status, STATUS_UNSUPPORTED_FORMAT)
        self.assertEqual(result.stats["reason"], "empty_file")

    def test_unsupported_extension_is_rejected(self):
        result = excel_in.convert_excel(b"whatever", "notes.docx")
        self.assertEqual(result.status, STATUS_UNSUPPORTED_FORMAT)
        self.assertIn("unsupported_ext", result.stats["reason"])

    def test_corrupt_xlsx_bytes_do_not_crash(self):
        result = excel_in.convert_excel(b"not a real spreadsheet at all", "corrupt.xlsx")
        self.assertEqual(result.status, STATUS_UNSUPPORTED_FORMAT)
        self.assertEqual(result.tables, [])


if __name__ == "__main__":
    unittest.main()
