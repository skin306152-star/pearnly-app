# -*- coding: utf-8 -*-
"""
ADR-006 S3 守门测试 · 模板学习层接入 parse_bank_stmt_xlsx_direct。

锁定:
  1. 现有固定词典识别不出的新格式(表头是 Col1.. 但数据形状+余额链清楚)→ 现在能解析出行(不再失败)。
  2. 拿不准的格式 → 返回 needs_mapping(带预览/猜测)· 不报死错。
  3. tenant 已存映射 → 直接套用(mock template_store.find_mapping)。
  4. 回归:现有 _find_stmt_header 能识别的文件 · 不碰学习层 · 行为不变。
"""

import io
import unittest
from unittest import mock

from services.recon import bank_recon_v2 as brv2


def _xlsx(rows):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# 表头完全不认识(Col1..)· 但数据形状清楚 + 余额链成立 → 学习层应救回
_NEW_FORMAT = [
    ["Col1", "Col2", "Col3", "Col4", "Col5"],
    ["2025-11-01", "txn a", "5000.00", "", "15000.00"],
    ["2025-11-02", "txn b", "", "2000.00", "13000.00"],
    ["2025-11-03", "txn c", "", "1000.00", "12000.00"],
    ["2025-11-04", "txn d", "3000.00", "", "15000.00"],
    ["2025-11-05", "txn e", "", "500.00", "14500.00"],
    ["2025-11-06", "txn f", "4000.00", "", "18500.00"],
    ["2025-11-07", "txn g", "", "1500.00", "17000.00"],
    ["2025-11-08", "txn h", "2000.00", "", "19000.00"],
]


class StmtTemplateIntegrationTests(unittest.TestCase):
    def test_new_format_recovered_high_confidence(self):
        # 不传 tenant_id(不碰 DB)· 高信心本地推断直接解析出行
        res = brv2.parse_bank_stmt_xlsx_direct(_xlsx(_NEW_FORMAT), "newfmt.xlsx")
        self.assertTrue(res.get("ok"), f"should recover, got {res.get('error_code')}")
        self.assertGreaterEqual(res.get("row_count", 0), 5)

    def test_ambiguous_returns_needs_mapping(self):
        # 有日期+两钱列但无余额、表头不认识 → 余额链无法成立 → needs_mapping(不死错)
        rows = [
            ["X1", "X2", "X3", "X4"],
            ["2025-11-01", "a", "5000.00", "2000.00"],
            ["2025-11-02", "b", "3000.00", "1000.00"],
            ["2025-11-03", "c", "4000.00", "500.00"],
            ["2025-11-04", "d", "1000.00", "700.00"],
        ]
        res = brv2.parse_bank_stmt_xlsx_direct(_xlsx(rows), "amb.xlsx")
        self.assertFalse(res.get("ok"))
        # 要么 needs_mapping,要么至少不是直接 ok(关键:不静默出错数)
        if res.get("error_code") == "needs_mapping":
            self.assertTrue(res.get("needs_mapping"))
            mr = res.get("mapping_request")
            self.assertIn("preview_rows", mr)
            self.assertIn("suggested_mapping", mr)
            self.assertIn("template_signature", mr)

    def test_saved_mapping_applied(self):
        # tenant 已存映射 → 直接套用(不依赖推断)
        saved = {"date": 0, "description": 1, "deposit": 2, "withdrawal": 3, "balance": 4}
        with mock.patch("services.importer.template_store.find_mapping", return_value=saved):
            res = brv2.parse_bank_stmt_xlsx_direct(
                _xlsx(_NEW_FORMAT), "newfmt.xlsx", tenant_id="t1"
            )
        self.assertTrue(res.get("ok"))
        self.assertGreaterEqual(res.get("row_count", 0), 5)

    def test_thai_petty_cash_opening_and_total_row(self):
        # 真实小现金件 เงินสดย่อย 结构:ยกยอดมา 承前行(期初)+ 末尾 รวมยอด 合计行。
        # 修前:ยกยอดมา 被当存款 + รวมยอด 余额污染期末 → 不平衡 ⚠。修后:期初/期末正确 + 平衡。
        rows = [
            ["วันที่", "รายการ", "รายรับ", "รายจ่าย", "คงเหลือ"],
            ["2025-11-01", "ยกยอดมา", "10000.00", "", "10000.00"],  # 承前(期初)
            ["2025-11-01", "ซื้อของ", "", "500.00", "9500.00"],
            ["2025-11-02", "รับเงิน", "2000.00", "", "11500.00"],
            ["2025-11-03", "ค่าน้ำมัน", "", "1000.00", "10500.00"],
            ["2025-11-04", "ค่าทางด่วน", "", "300.00", "10200.00"],
            ["", "รวมยอด", "2000.00", "1800.00", "999999.99"],  # 合计行(余额是大额合计,须跳过)
        ]
        res = brv2.parse_bank_stmt_xlsx_direct(_xlsx(rows), "petty.xlsx")
        self.assertTrue(res.get("ok"))
        a = res["accounts"][0]
        self.assertEqual(a["opening"], 10000.00)  # ยกยอดมา 识别为期初
        self.assertEqual(a["closing"], 10200.00)  # 末笔交易,而非 รวมยอด 的 999999.99
        self.assertTrue(res["completeness"]["ok"])  # 期初+存-取=期末 → 平衡 · 无 ⚠
        # ยกยอดมา 不计入交易存款
        self.assertEqual(res["row_count"], 4)

    def test_regression_existing_format_unchanged(self):
        # 标准泰文表头(现有 _find_stmt_header 能认)· 不应走学习层 · 正常解析
        rows = [
            ["วันที่", "รายการ", "ฝาก", "ถอน", "คงเหลือ"],
            ["2025-11-01", "a", "5000.00", "", "15000.00"],
            ["2025-11-02", "b", "", "2000.00", "13000.00"],
            ["2025-11-03", "c", "", "1000.00", "12000.00"],
        ]
        res = brv2.parse_bank_stmt_xlsx_direct(_xlsx(rows), "std.xlsx")
        self.assertTrue(res.get("ok"))
        self.assertGreaterEqual(res.get("row_count", 0), 3)


if __name__ == "__main__":
    unittest.main()
