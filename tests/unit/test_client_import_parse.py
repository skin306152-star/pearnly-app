# -*- coding: utf-8 -*-
"""IN-0d · services/workspace/client_import.py 纯函数解析测试(零 DB 依赖)。

覆盖:泰/英/中表头各命中、表头猜不中诚实报、8MB/500 行超限拒、空文件/坏文件诚实报、
结构性三态(缺 name / 税号格式错 / 合法通过)各有例。
"""

from __future__ import annotations

import io
import unittest

import openpyxl

from services.workspace import client_import as svc


def _xlsx_bytes(headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class HeaderSynonymTests(unittest.TestCase):
    def test_english_headers_matched(self):
        raw = _xlsx_bytes(
            ["Client Name", "Tax ID", "Branch", "Phone", "Address"],
            [["ACME Co Ltd", "0105546015062", "Head Office", "022221111", "Bangkok"]],
        )
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertTrue(out["name_column_found"])
        self.assertEqual(out["matched"]["name"], 0)
        self.assertEqual(out["matched"]["tax_id"], 1)
        self.assertEqual(out["rows"][0]["name"], "ACME Co Ltd")

    def test_thai_headers_matched(self):
        raw = _xlsx_bytes(
            ["ชื่อลูกค้า", "เลขประจำตัวผู้เสียภาษี", "สาขา", "โทรศัพท์", "ที่อยู่"],
            [["บริษัท ปิยะนุช จำกัด", "0105546015062", "สำนักงานใหญ่", "022221111", "กรุงเทพ"]],
        )
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertTrue(out["name_column_found"])
        self.assertEqual(out["rows"][0]["name"], "บริษัท ปิยะนุช จำกัด")
        self.assertEqual(out["rows"][0]["tax_id"], "0105546015062")

    def test_chinese_headers_matched(self):
        raw = _xlsx_bytes(
            ["客户名称", "税号", "分公司", "电话", "地址"],
            [["示例公司", "0105546015062", "总公司", "022221111", "曼谷"]],
        )
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertTrue(out["name_column_found"])
        self.assertEqual(out["rows"][0]["name"], "示例公司")

    def test_optional_columns_missing_left_blank(self):
        # 只有 name 列,其余可选列缺失不算失败,整批留空。
        raw = _xlsx_bytes(["Client Name"], [["ACME Co Ltd"]])
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertTrue(out["name_column_found"])
        self.assertEqual(out["rows"][0]["tax_id"], "")
        self.assertEqual(out["rows"][0]["address"], "")

    def test_header_not_recognized_when_no_name_column(self):
        # 表头全不认识(没有任何列能猜成 name)→ 诚实报告,不瞎猜硬导。
        raw = _xlsx_bytes(["Foo", "Bar"], [["x", "y"]])
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertFalse(out["name_column_found"])
        self.assertEqual(out["rows"], [])


class LimitsTests(unittest.TestCase):
    def test_empty_file_reports_no_headers(self):
        out = svc.parse_client_rows(b"", "clients.xlsx")
        self.assertFalse(out["name_column_found"])
        self.assertEqual(out["headers"], [])

    def test_garbage_bytes_reports_honestly_not_crash(self):
        out = svc.parse_client_rows(b"\x00\x01not-a-real-file", "clients.xlsx")
        self.assertFalse(out["name_column_found"])
        self.assertEqual(out["rows"], [])

    def test_8mb_upper_bound_constant(self):
        self.assertEqual(svc.MAX_BYTES, 8 * 1024 * 1024)

    def test_over_500_rows_truncated(self):
        rows = [[f"Client {i}"] for i in range(600)]
        raw = _xlsx_bytes(["Client Name"], rows)
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertTrue(out["truncated"])
        self.assertEqual(out["row_count"], svc.MAX_ROWS)

    def test_under_500_rows_not_truncated(self):
        rows = [[f"Client {i}"] for i in range(10)]
        raw = _xlsx_bytes(["Client Name"], rows)
        out = svc.parse_client_rows(raw, "clients.xlsx")
        self.assertFalse(out["truncated"])
        self.assertEqual(out["row_count"], 10)


class StructuralErrorTests(unittest.TestCase):
    def test_missing_name_is_error(self):
        self.assertEqual(svc.structural_error("", "0105546015062"), svc.ERR_MISSING_NAME)
        self.assertEqual(svc.structural_error("   ", ""), svc.ERR_MISSING_NAME)

    def test_bad_tax_id_format_is_error(self):
        self.assertEqual(svc.structural_error("ACME", "12345"), svc.ERR_BAD_TAX_ID)
        self.assertEqual(svc.structural_error("ACME", "abc-not-a-number"), svc.ERR_BAD_TAX_ID)

    def test_valid_row_passes_structural_check(self):
        self.assertIsNone(svc.structural_error("ACME Co Ltd", "0105546015062"))

    def test_blank_tax_id_is_optional_not_error(self):
        # tax_id 是可选字段,空值不算格式错。
        self.assertIsNone(svc.structural_error("ACME Co Ltd", ""))
        self.assertIsNone(svc.structural_error("ACME Co Ltd", "   "))


if __name__ == "__main__":
    unittest.main()
