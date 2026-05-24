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

    def test_tiny_weird_headers_sparse_direction_cols_rescued(self):
        # ① 修复(2026-05-24)· 怪表头 F1-F6 + 行数少:存列只 2 值(5000/700)、取列只 2 值(1200/300)·
        # 被 _fill_by_shape『≥3 行有钱』阈值漏掉 → 此前方向列没识别 → 余额链没机会跑 → needs_mapping。
        # 方向列救援搜索:在剩余数字列里枚举存/取两种顺序 · 余额链验证选对 → 自动识别(高信心)且方向正确。
        rows = [
            ["F1", "F2", "F3", "F4", "F5", "F6"],
            ["2026-01-01", "OPENING BALANCE", "", "", "10000.00", "OB"],
            ["2026-01-02", "Customer receipt A", "", "5000.00", "15000.00", "R001"],
            ["2026-01-03", "Supplier payment B", "1200.00", "", "13800.00", "P001"],
            ["2026-01-04", "Bank fee", "300.00", "", "13500.00", "FEE"],
            ["2026-01-05", "Customer receipt C", "", "700.00", "14200.00", "R002"],
        ]
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(rows)
        self.assertEqual(idx, 0)  # 真表头 F1-F6 那行(不是数据行)
        self.assertEqual(cm.get("date"), 0)
        self.assertEqual(cm.get("balance"), 4)
        # 方向必须识别且摆对(F3=取 col2 / F4=存 col3)· 靠余额链验证定向
        self.assertEqual(cm.get("withdrawal"), 2)
        self.assertEqual(cm.get("deposit"), 3)
        self.assertEqual(conf, "high")  # 余额链 100% 命中 → 自动识别不弹映射

    def test_no_balance_picks_real_header_not_data_row(self):
        # 无余额列 + 数据值含同义词(Sale receipt 含 'receipt')· 排序须靠表头词密度选对真表头行,
        # 不能把数据行当表头(否则面板给用户看错表头/错猜测)。
        rows = [
            ["Txn Date", "Particulars", "Amount"],
            ["2025-11-01", "Sale receipt", "5000"],
            ["2025-11-02", "Pay supplier", "-2000"],
            ["2025-11-03", "Utility bill", "-1200"],
            ["2025-11-04", "Customer transfer", "3000"],
            ["2025-11-05", "Office rent", "-1500"],
        ]
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(rows)
        self.assertEqual(idx, 0)  # 真表头在第 0 行
        self.assertEqual(cm.get("date"), 0)
        self.assertEqual(cm.get("description"), 1)
        self.assertEqual(cm.get("amount"), 2)
        self.assertNotIn("deposit", cm)  # 不能把 'Sale receipt' 误判成 deposit 列

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


class HeaderNotDataRowTests(unittest.TestCase):
    """S7 §9 压测发现:真表头无识别词(Column A..)时,描述里含同义词(รายการ)的数据行
    会得 header_signal=1 盖过真表头 → 误把首笔交易当表头 → 静默吞行 + 期初错。
    修:候选表头行若日期列本身是真日期 → 是数据行 · 不盖过真标签表头。"""

    def test_data_row_with_synonym_not_chosen_as_header(self):
        # 真表头 Column A.. 无识别词;数据行描述含 รายการ(=DESC 同义词)· 余额链成立(deposit=C2,withdrawal=C3)
        rows = [
            ["Column A", "Column B", "Column C", "Column D", "Column E"],
            ["2026-01-02", "รายการ 00001 บริษัท", "5000.00", "", "15000.00"],
            ["2026-01-03", "รายการ 00002 ASIA", "", "2000.00", "13000.00"],
            ["2026-01-04", "รายการ 00003 ร้าน", "", "1000.00", "12000.00"],
            ["2026-01-05", "รายการ 00004 CUST", "3000.00", "", "15000.00"],
            ["2026-01-06", "รายการ 00005 SHOP", "", "500.00", "14500.00"],
            ["2026-01-07", "รายการ 00006 FOO", "4000.00", "", "18500.00"],
            ["2026-01-08", "รายการ 00007 BAR", "", "1500.00", "17000.00"],
            ["2026-01-09", "รายการ 00008 BAZ", "2000.00", "", "19000.00"],
        ]
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(rows)
        # 必须选第 0 行(真表头)· 不是第 1 行(数据行碰巧含 รายการ → 修前会被误选)
        self.assertEqual(idx, 0)
        self.assertEqual(cm.get("date"), 0)

    def test_gl_data_row_with_synonym_not_chosen_as_header(self):
        rows = [
            ["Col1", "Col2", "Col3", "Col4", "Col5"],
            ["2026-01-02", "JV001", "รายการ ซื้อของ", "", "5000"],
            ["2026-01-03", "JV002", "รายการ ขายของ", "2000", ""],
            ["2026-01-04", "JV003", "รายการ ค่าน้ำ", "300", ""],
            ["2026-01-05", "JV004", "รายการ ค่าไฟ", "", "1500"],
            ["2026-01-06", "JV005", "รายการ เงินเดือน", "8000", ""],
            ["2026-01-07", "JV006", "รายการ ค่าเช่า", "", "1200"],
        ]
        idx, cm, conf, _ = tl.infer_gl_col_map(rows)
        self.assertEqual(idx, 0)  # 真表头行 · 不被含 รายการ 的数据行盖过


if __name__ == "__main__":
    unittest.main()
