# -*- coding: utf-8 -*-
"""
ADR-006 S1 守门测试 · 本地模板推断引擎(services/importer/template_learning)。

锁定:对"现有 _find_stmt_header 会漏"的新格式,引擎能靠同义词+数据形状+余额链推断出正确 col_map,
并据余额链给高信心;真模糊的给低信心(交用户确认)。col_map 键必须与 _parse_stmt_sheet 兼容。
"""

import io
import unittest

from services.importer import template_learning as tl


def _xlsx(rows):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class HelperTests(unittest.TestCase):
    def test_to_float(self):
        self.assertEqual(tl.to_float("1,234.56"), 1234.56)
        self.assertEqual(tl.to_float("(500.00)"), -500.0)
        self.assertEqual(tl.to_float("-12"), -12.0)
        self.assertEqual(tl.to_float(""), 0.0)
        self.assertEqual(tl.to_float("—"), 0.0)

    def test_parse_date_buddhist(self):
        self.assertEqual(str(tl.parse_date("01/11/2568")), "2025-11-01")  # 泰历
        self.assertEqual(str(tl.parse_date("2025-11-01")), "2025-11-01")

    def test_signature_stable(self):
        s1 = tl.build_header_signature(["วันที่", "รายการ", "คงเหลือ"])
        s2 = tl.build_header_signature([" วันที่ ", "รายการ", "คงเหลือ"])  # 空格归一
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, tl.build_header_signature(["date", "desc", "balance"]))


class InferStatementTests(unittest.TestCase):
    def test_thai_two_direction_columns(self):
        # 新格式:表头在第 3 行 · 泰文存/取/余额 · 现有词典可能漏 รายรับ/รายจ่าย
        rows = [
            ["บัญชีเงินสดย่อย", "", "", "", ""],
            ["ยอดยกมา", "", "", "", "10000.00"],
            ["วันที่", "รายละเอียด", "รายรับ", "รายจ่าย", "คงเหลือ"],
            ["01/11/2025", "รับเงินสด", "5000.00", "", "15000.00"],
            ["02/11/2025", "จ่ายค่าน้ำ", "", "2000.00", "13000.00"],
            ["03/11/2025", "จ่ายค่าไฟ", "", "1000.00", "12000.00"],
            ["04/11/2025", "รับโอน", "3000.00", "", "15000.00"],
            ["05/11/2025", "จ่ายของ", "", "500.00", "14500.00"],
        ]
        sheets = tl.load_tabular_sheets(_xlsx(rows), "petty_cash.xlsx")
        self.assertEqual(len(sheets), 1)
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(sheets[0][1])
        self.assertEqual(idx, 2)
        self.assertEqual(cm["date"], 0)
        self.assertEqual(cm["deposit"], 2)
        self.assertEqual(cm["withdrawal"], 3)
        self.assertEqual(cm["balance"], 4)
        self.assertEqual(conf, "high")  # 余额链对得上
        # 与 _parse_stmt_sheet 兼容:至少含 date + balance
        self.assertIn("date", cm)
        self.assertIn("balance", cm)

    def test_signed_amount_single_column(self):
        # 单列带符号金额(正=存 负=取)· 英文表头
        rows = [
            ["Date", "Description", "Amount", "Balance"],
            ["2025-11-01", "opening txn", "5000.00", "15000.00"],
            ["2025-11-02", "pay water", "-2000.00", "13000.00"],
            ["2025-11-03", "pay power", "-1000.00", "12000.00"],
            ["2025-11-04", "transfer in", "3000.00", "15000.00"],
            ["2025-11-05", "buy goods", "-500.00", "14500.00"],
        ]
        sheets = tl.load_tabular_sheets(_xlsx(rows), "stmt.xlsx")
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(sheets[0][1])
        self.assertEqual(cm["date"], 0)
        self.assertEqual(cm["amount"], 2)
        self.assertEqual(cm["balance"], 3)
        self.assertEqual(conf, "high")

    def test_no_recognizable_headers_but_clear_shape(self):
        # 表头是 Col1/Col2... 完全不认识 · 但数据形状清楚 + 余额链成立 → 形状推断救回
        rows = [
            ["Col1", "Col2", "Col3", "Col4", "Col5"],
            ["2025-11-01", "txn a", "5000.00", "", "15000.00"],
            ["2025-11-02", "txn b", "", "2000.00", "13000.00"],
            ["2025-11-03", "txn c", "", "1000.00", "12000.00"],
            ["2025-11-04", "txn d", "3000.00", "", "15000.00"],
            ["2025-11-05", "txn e", "", "500.00", "14500.00"],
            ["2025-11-06", "txn f", "4000.00", "", "18500.00"],
            ["2025-11-07", "txn g", "", "1500.00", "17000.00"],
            ["2025-11-08", "txn h", "2000.00", "", "19000.00"],
            ["2025-11-09", "txn i", "", "800.00", "18200.00"],
        ]
        sheets = tl.load_tabular_sheets(_xlsx(rows), "weird.xlsx")
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(sheets[0][1])
        self.assertIn("date", cm)
        self.assertIn("balance", cm)
        self.assertTrue(any(k in cm for k in ("deposit", "withdrawal", "amount")))
        # 形状能推出列且余额链成立 → 至少 medium,通常 high
        self.assertIn(conf, ("high", "medium"))

    def test_garbage_low_confidence(self):
        rows = [
            ["a", "b", "c"],
            ["x", "y", "z"],
            ["foo", "bar", "baz"],
            ["1", "2", "3"],
        ]
        sheets = tl.load_tabular_sheets(_xlsx(rows), "garbage.xlsx")
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(sheets[0][1])
        # 没有日期列/余额链 → 不该高信心(交用户确认)
        self.assertNotEqual(conf, "high")

    def test_validate_by_balance_catches_swapped_direction(self):
        # 存取列读反 → 余额链对不上 → 校验不过(促使走用户确认而非出错数)
        rows = [
            ["Date", "Desc", "Deposit", "Withdrawal", "Balance"],
            ["2025-11-01", "a", "5000.00", "", "15000.00"],
            ["2025-11-02", "b", "", "2000.00", "13000.00"],
            ["2025-11-03", "c", "", "1000.00", "12000.00"],
            ["2025-11-04", "d", "3000.00", "", "15000.00"],
        ]
        sheets = tl.load_tabular_sheets(_xlsx(rows), "s.xlsx")[0][1]
        good = {"date": 0, "description": 1, "deposit": 2, "withdrawal": 3, "balance": 4}
        swapped = {"date": 0, "description": 1, "deposit": 3, "withdrawal": 2, "balance": 4}
        ok_good, _ = tl.validate_by_balance(sheets, 0, good)
        ok_swap, _ = tl.validate_by_balance(sheets, 0, swapped)
        self.assertTrue(ok_good)
        self.assertFalse(ok_swap)


if __name__ == "__main__":
    unittest.main()
