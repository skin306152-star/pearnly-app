# -*- coding: utf-8 -*-
"""
ADR-006 S6a 守门测试 · CSV 银行账单走学习层(编码 + 分隔符 + 三层识别)。
"""

import unittest

import bank_recon_v2 as brv2


def _csv_bytes(rows, delim=",", encoding="utf-8", bom=False):
    lines = []
    for r in rows:
        cells = []
        for c in r:
            s = str(c)
            if delim in s or '"' in s:
                s = '"' + s.replace('"', '""') + '"'
            cells.append(s)
        lines.append(delim.join(cells))
    text = "\r\n".join(lines)
    data = text.encode(encoding)
    if bom and encoding.startswith("utf-8"):
        data = b"\xef\xbb\xbf" + data
    return data


_THAI_ROWS = [
    ["วันที่", "รายการ", "รายรับ", "รายจ่าย", "คงเหลือ"],
    ["2025-11-01", "ยกยอดมา", "", "", "10000.00"],
    ["2025-11-01", "ซื้อของ", "", "500.00", "9500.00"],
    ["2025-11-02", "รับเงิน", "2000.00", "", "11500.00"],
    ["2025-11-03", "ค่าน้ำมัน", "", "1000.00", "10500.00"],
    ["2025-11-04", "ค่าทางด่วน", "", "300.00", "10200.00"],
]


class CsvStatementTests(unittest.TestCase):
    def test_comma_utf8_bom(self):
        res = brv2.parse_bank_stmt_xlsx_direct(_csv_bytes(_THAI_ROWS, bom=True), "stmt.csv")
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertEqual(res["row_count"], 4)  # ยกยอดมา 期初不计

    def test_semicolon_delimiter(self):
        res = brv2.parse_bank_stmt_xlsx_direct(_csv_bytes(_THAI_ROWS, delim=";"), "stmt.csv")
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertGreaterEqual(res["row_count"], 4)

    def test_tab_delimiter(self):
        res = brv2.parse_bank_stmt_xlsx_direct(_csv_bytes(_THAI_ROWS, delim="\t"), "stmt.tsv")
        self.assertTrue(res.get("ok"), res.get("error_code"))

    def test_quoted_thousands_comma_not_split(self):
        rows = [
            ["Date", "Desc", "Deposit", "Withdrawal", "Balance"],
            ["2025-11-01", "open", "10,620.53", "", "10,620.53"],
            ["2025-11-02", "buy", "", "1,000.00", "9,620.53"],
            ["2025-11-03", "buy2", "", "500.00", "9,120.53"],
            ["2025-11-04", "in", "880.00", "", "10,000.53"],
        ]
        res = brv2.parse_bank_stmt_xlsx_direct(_csv_bytes(rows), "stmt.csv")
        self.assertTrue(res.get("ok"), res.get("error_code"))
        # 千分位逗号在引号字段里 · 不该被切错列 · 余额读对
        self.assertAlmostEqual(res["accounts"][0]["closing"], 10000.53, places=2)

    def test_thai_cp874_encoding(self):
        # 泰文 CSV 常见 cp874(TIS-620)编码 · 不能读成乱码
        res = brv2.parse_bank_stmt_xlsx_direct(
            _csv_bytes(_THAI_ROWS, encoding="cp874"), "stmt.csv"
        )
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertGreaterEqual(res["row_count"], 4)


if __name__ == "__main__":
    unittest.main()
