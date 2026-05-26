# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 销项税报表解析 vat_report_parser.py 行为契约

vat_report_parser.py(Excel/PDF 解析 VAT 报表)此前 0 专属测试。
只测纯/确定性部分(零成本 Excel 路径 + 工具)· 跳过 Gemini 路径。
无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。

锁定:金额解析(括号负数)· 垃圾行过滤(挡页眉/分隔/表头误抓)·
列映射(ref_no 优先于 invoice_no)· parse_excel 全链路 + 合计行进 meta。
"""

import io
import unittest

import openpyxl

import vat_report_parser as vp


class HelperTests(unittest.TestCase):
    def test_hit_case_insensitive_substring(self):
        self.assertTrue(vp._hit("Invoice No", {"invoice no"}))
        self.assertFalse(vp._hit("Date", {"invoice no"}))

    def test_to_float(self):
        self.assertEqual(vp._to_float("1,000.00"), 1000.0)
        self.assertEqual(vp._to_float("(500.00)"), -500.0)  # 括号负数
        self.assertIsNone(vp._to_float("-"))
        self.assertIsNone(vp._to_float(""))
        self.assertIsNone(vp._to_float("abc"))


class FilterGarbageRowsTests(unittest.TestCase):
    def test_keeps_valid_doc_no(self):
        rows = [{"report_invoice_no": "INV001"}]
        self.assertEqual(len(vp._filter_garbage_rows(rows)), 1)

    def test_ref_no_takes_priority_as_key(self):
        rows = [{"report_ref_no": "REF9", "report_invoice_no": "xx"}]
        self.assertEqual(len(vp._filter_garbage_rows(rows)), 1)

    def test_drops_ornament_and_too_short(self):
        self.assertEqual(vp._filter_garbage_rows([{"report_invoice_no": "-----"}]), [])
        self.assertEqual(vp._filter_garbage_rows([{"report_invoice_no": "ab"}]), [])  # <3

    def test_drops_header_keyword_row(self):
        # 含 VAT 表头关键词(误抓的表头)→ 剔除
        rows = [{"report_invoice_no": "AB ใบกำกับภาษี"}]
        self.assertEqual(vp._filter_garbage_rows(rows), [])

    def test_drops_multi_space_row(self):
        # 整行误抓 → 多空格 → 剔除
        self.assertEqual(vp._filter_garbage_rows([{"report_invoice_no": "A B C"}]), [])


class MapColumnsTests(unittest.TestCase):
    def test_basic_mapping(self):
        headers = ["Date", "Invoice No", "Customer", "Tax ID", "Net", "VAT", "Total"]
        cm = vp._map_columns(headers)
        self.assertEqual(cm["date"], 0)
        self.assertEqual(cm["invoice_no"], 1)
        self.assertEqual(cm["buyer_name"], 2)
        self.assertEqual(cm["buyer_tax_id"], 3)
        self.assertEqual(cm["amount_pre_vat"], 4)
        self.assertEqual(cm["vat_amount"], 5)
        self.assertEqual(cm["total_amount"], 6)

    def test_ref_no_detected_separately(self):
        headers = ["Date", "Ref No", "Invoice No"]
        cm = vp._map_columns(headers)
        self.assertEqual(cm["ref_no"], 1)
        self.assertEqual(cm["invoice_no"], 2)


class BuildRowTests(unittest.TestCase):
    def test_full_row(self):
        col_map = {
            "date": 0,
            "invoice_no": 1,
            "buyer_name": 2,
            "buyer_tax_id": 3,
            "amount_pre_vat": 4,
            "vat_amount": 5,
            "total_amount": 6,
        }
        cells = ["2026-03-15", "INV001", "ACME Co", "0-1075-36000-18-8", "1000.00", "70.00", "1070"]
        row = vp._build_row(7, cells, col_map)
        self.assertEqual(row["row_no"], 7)
        self.assertEqual(row["report_invoice_no"], "INV001")
        self.assertEqual(row["report_buyer_tax_id"], "0107536000188")  # 归一化只留数字
        self.assertEqual(row["report_amount_pre_vat"], 1000.0)
        self.assertEqual(row["report_vat_amount"], 70.0)
        self.assertEqual(row["report_amount"], 1070.0)
        self.assertFalse(row["is_individual"])  # 有税号 → 非个人

    def test_individual_when_no_tax_id(self):
        row = vp._build_row(
            1, ["", "INV1", "Walk-in", ""], {"invoice_no": 1, "buyer_name": 2, "buyer_tax_id": 3}
        )
        self.assertTrue(row["is_individual"])


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class ParseExcelTests(unittest.TestCase):
    def test_parses_rows_and_totals(self):
        data = _xlsx(
            [
                ["Date", "Invoice No", "Customer", "Tax ID", "Net", "VAT", "Total"],
                ["2026-03-15", "INV001", "ACME", "0107536000188", "1000.00", "70.00", "1070.00"],
                ["Total", "", "", "", "1000.00", "70.00", ""],  # 合计行 → 进 meta
            ]
        )
        out = vp.parse_excel(data)
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 1)  # 合计行不计入数据行
        self.assertEqual(out["rows"][0]["report_invoice_no"], "INV001")
        self.assertEqual(out["meta"]["total_amount_pre_vat"], 1000.0)
        self.assertEqual(out["meta"]["total_vat"], 70.0)
        self.assertEqual(out["method"], "excel")

    def test_no_header_row(self):
        data = _xlsx([["foo", "bar"], ["1", "2"]])
        out = vp.parse_excel(data)
        self.assertFalse(out["ok"])

    def test_bad_bytes(self):
        out = vp.parse_excel(b"not an xlsx")
        self.assertFalse(out["ok"])


if __name__ == "__main__":
    unittest.main()
