# -*- coding: utf-8 -*-
"""销项 PO-3 · 商品 Excel 导入解析守门测试(纯解析 · 不连库)。

锁定:表头别名映射 / 金额与含税解析 / 行级校验(缺名、坏价)/ 空行跳过 /
非 xlsx 与缺名列抛 ValueError。
"""

import io
import unittest
from decimal import Decimal

import openpyxl

from services.sales import product_import as imp


def _xlsx(rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class ProductImportParseTests(unittest.TestCase):
    def test_header_aliases_and_types(self):
        data = _xlsx(
            [
                ["商品名称", "code", "ราคา", "vat", "单位"],
                ["น้ำดื่ม", "P01", "12.50", "yes", "ขวด"],
            ]
        )
        valid, errors = imp.parse_workbook(data)
        self.assertEqual(errors, [])
        self.assertEqual(len(valid), 1)
        rec = valid[0]
        self.assertEqual(rec["name_th"], "น้ำดื่ม")
        self.assertEqual(rec["code"], "P01")
        self.assertEqual(rec["unit_price"], Decimal("12.50"))
        self.assertTrue(rec["vat_applicable"])
        self.assertEqual(rec["unit"], "ขวด")

    def test_blank_rows_skipped(self):
        data = _xlsx([["name_th", "unit_price"], ["A", "1"], [None, None], ["", ""], ["B", "2"]])
        valid, errors = imp.parse_workbook(data)
        self.assertEqual([r["name_th"] for r in valid], ["A", "B"])
        self.assertEqual(errors, [])

    def test_bad_price_is_row_error_not_fatal(self):
        data = _xlsx([["name_th", "unit_price"], ["A", "abc"], ["B", "5"]])
        valid, errors = imp.parse_workbook(data)
        self.assertEqual([r["name_th"] for r in valid], ["B"])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["row"], 2)
        self.assertIn("unit_price", errors[0]["error"])

    def test_negative_price_rejected(self):
        data = _xlsx([["name_th", "unit_price"], ["A", "-3"]])
        valid, errors = imp.parse_workbook(data)
        self.assertEqual(valid, [])
        self.assertEqual(len(errors), 1)

    def test_missing_name_value_is_row_error(self):
        data = _xlsx([["name_th", "code"], ["", "P9"], ["Real", "P1"]])
        valid, errors = imp.parse_workbook(data)
        self.assertEqual([r["name_th"] for r in valid], ["Real"])
        self.assertEqual(len(errors), 1)
        self.assertIn("name_th", errors[0]["error"])

    def test_missing_name_column_raises(self):
        data = _xlsx([["code", "unit_price"], ["P1", "5"]])
        with self.assertRaises(ValueError) as ctx:
            imp.parse_workbook(data)
        self.assertEqual(str(ctx.exception), "missing_name_column")

    def test_non_xlsx_raises(self):
        with self.assertRaises(ValueError) as ctx:
            imp.parse_workbook(b"not an excel file")
        self.assertEqual(str(ctx.exception), "file_not_xlsx")


if __name__ == "__main__":
    unittest.main()
