# -*- coding: utf-8 -*-
"""
ADR-006 S6b 守门测试 · GL 总账接入模板学习层(无余额链 · 保守:拿不准交用户确认)。
"""

import io
import unittest
from unittest import mock

import bank_recon_v2 as brv2
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


class InferGlTests(unittest.TestCase):
    def test_clean_gl_high_confidence(self):
        rows = [
            ["Date", "Voucher", "Account", "Description", "Debit", "Credit"],
            ["2025-11-01", "JV001", "4000", "sale", "", "5000"],
            ["2025-11-02", "JV002", "5000", "buy", "2000", ""],
            ["2025-11-03", "JV003", "5100", "fee", "300", ""],
            ["2025-11-04", "JV004", "4000", "sale2", "", "1500"],
        ]
        idx, cm, conf, _ = tl.infer_gl_col_map(rows)
        self.assertEqual(idx, 0)
        self.assertEqual(cm["date"], 0)
        self.assertEqual(cm["debit"], 4)
        self.assertEqual(cm["credit"], 5)
        self.assertEqual(cm.get("account"), 2)
        self.assertEqual(conf, "high")


class GlParseIntegrationTests(unittest.TestCase):
    _HEADERLESS = [
        ["C1", "C2", "C3", "C4", "C5"],
        ["2025-11-01", "JV001", "4000", "", "5000"],
        ["2025-11-02", "JV002", "5000", "2000", ""],
        ["2025-11-03", "JV003", "5100", "300", ""],
        ["2025-11-04", "JV004", "4000", "", "1500"],
    ]

    def test_headerless_gl_needs_mapping_not_dead_error(self):
        # 表头不认识 → 旧 _map_gl_cols 失败 → 学习层 shape 识别但低信心 → needs_mapping(不死错)
        res = brv2.parse_gl_excel(_xlsx(self._HEADERLESS), "gl.xlsx")
        self.assertFalse(res.get("ok"))
        # 关键:不再是 gl_headers_not_found 死错 → 应给 needs_mapping 让用户确认
        self.assertEqual(res.get("error_code"), "needs_mapping")
        self.assertTrue(res.get("needs_mapping"))
        mr = res["mapping_request"]
        self.assertEqual(mr["document_type"], "gl")
        self.assertIn("preview_rows", mr)
        self.assertIn("date", mr["suggested_mapping"])  # 至少日期 · 借贷由用户在面板确认

    def test_gl_saved_mapping_applied(self):
        saved = {"date": 0, "doc_no": 1, "account": 2, "debit": 3, "credit": 4}
        with mock.patch("services.importer.template_store.find_mapping", return_value=saved):
            res = brv2.parse_gl_excel(_xlsx(self._HEADERLESS), "gl.xlsx", tenant_id="t1")
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertGreaterEqual(res.get("row_count", 0), 3)

    def test_gl_regression_standard_headers(self):
        rows = [
            ["วันที่", "เลขที่เอกสาร", "รหัสบัญชี", "คำอธิบาย", "เดบิต", "เครดิต"],
            ["2025-11-01", "JV001", "4000", "ขาย", "", "5000"],
            ["2025-11-02", "JV002", "5000", "ซื้อ", "2000", ""],
            ["2025-11-03", "JV003", "5100", "ค่าธรรมเนียม", "300", ""],
        ]
        res = brv2.parse_gl_excel(_xlsx(rows), "gl.xlsx")
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertGreaterEqual(res.get("row_count", 0), 3)


if __name__ == "__main__":
    unittest.main()
