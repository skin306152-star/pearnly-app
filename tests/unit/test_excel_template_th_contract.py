# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 泰国销售明细导出模板 excel_template_th.py 行为契约

excel_template_th.py(12 列泰文表头 · 按 items 拆行 · =E*F 公式)此前 0 专属测试。
纯生成函数 · 无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。

锁定 Korn 反馈修过的真实合同(v27.8.1.2):G/H/I 每行 =E*F · J 每行 =I*0.07,
+ 单号列纯文本格式(防 Excel 把 IV69/00271 当日期)+ 12 列泰文表头不漂移。
"""

import io
import unittest

from openpyxl import load_workbook

import excel_template_th as et


class NormDateTests(unittest.TestCase):
    def test_parses_western_formats(self):
        from datetime import datetime

        self.assertEqual(et._norm_date("2026-03-15"), datetime(2026, 3, 15))
        self.assertEqual(et._norm_date("15/03/2026"), datetime(2026, 3, 15))
        self.assertEqual(et._norm_date("15.03.2026"), datetime(2026, 3, 15))

    def test_empty_and_bad(self):
        self.assertIsNone(et._norm_date(None))
        self.assertIsNone(et._norm_date(""))
        self.assertIsNone(et._norm_date("not-a-date"))

    @unittest.expectedFailure
    def test_KNOWN_GAP_buddhist_era_not_converted(self):
        """🐛 文档/代码不一致(待 Zihao 拍板):docstring 声称『含泰国佛历 2569→2026』,
        但 _norm_date 只 strptime · 未做 -543 转换 · 佛历年份会原样落入 Excel。
        若佛历日期会到这(field_comparator.parse_date 已转 · 本模块没转)→ 导出年份错。
        修法:解析后对 year>2400 减 543(复用 field_comparator._thai_to_gregorian)。
        """
        from datetime import datetime

        self.assertEqual(et._norm_date("2569-03-15"), datetime(2026, 3, 15))


class ToFloatStrTests(unittest.TestCase):
    def test_to_float_strips_symbols(self):
        self.assertEqual(et._to_float("1,070.00"), 1070.0)
        self.assertEqual(et._to_float("฿500"), 500.0)
        self.assertEqual(et._to_float("100 THB"), 100.0)

    def test_to_float_none_and_bad(self):
        self.assertIsNone(et._to_float(None))
        self.assertIsNone(et._to_float(""))
        self.assertIsNone(et._to_float("abc"))

    def test_str_cleans_junk(self):
        self.assertEqual(et._str(None), "")
        self.assertEqual(et._str("  X "), "X")
        self.assertEqual(et._str("none"), "")
        self.assertEqual(et._str("NULL"), "")
        self.assertEqual(et._str("nan"), "")


def _load(records):
    raw = et.build_sales_detail_xlsx(records)
    assert isinstance(raw, (bytes, bytearray))
    return load_workbook(io.BytesIO(raw)).active


class HeaderTests(unittest.TestCase):
    def test_header_row_is_thai_12_cols(self):
        ws = _load([])
        headers = [ws.cell(row=1, column=i).value for i in range(1, 13)]
        self.assertEqual(headers, et.HEADERS_TH)
        self.assertEqual(len(et.HEADERS_TH), 12)


class FormulaContractTests(unittest.TestCase):
    def _rec_two_items(self):
        return [
            {
                "filename": "a.pdf",
                "engine": "x",
                "merged_fields": {
                    "date": "2026-03-15",
                    "invoice_number": "IV69/00271",
                    "buyer_name": "ACME",
                    "total_amount": "1070.00",
                    "items": [
                        {"description": "Coffee", "qty": "2", "unit_price": "500"},
                        {"description": "Tea", "amount": "100"},  # 缺 qty/price
                    ],
                },
            }
        ]

    def test_qty_price_row_uses_formulas(self):
        ws = _load(self._rec_two_items())
        # 第 1 个 item(row2):有 qty/price → G/H/I = =E2*F2 · J = =I2*0.07
        self.assertEqual(ws.cell(row=2, column=7).value, "=E2*F2")
        self.assertEqual(ws.cell(row=2, column=8).value, "=E2*F2")
        self.assertEqual(ws.cell(row=2, column=9).value, "=E2*F2")
        self.assertEqual(ws.cell(row=2, column=10).value, "=I2*0.07")
        self.assertEqual(ws.cell(row=2, column=5).value, 2.0)
        self.assertEqual(ws.cell(row=2, column=6).value, 500.0)

    def test_invoice_no_is_text_format(self):
        ws = _load(self._rec_two_items())
        c = ws.cell(row=2, column=2)
        self.assertEqual(c.value, "IV69/00271")
        self.assertEqual(c.number_format, "@")  # 纯文本 · 防被当日期

    def test_customer_and_description(self):
        ws = _load(self._rec_two_items())
        self.assertEqual(ws.cell(row=2, column=3).value, "ACME")
        self.assertEqual(ws.cell(row=2, column=4).value, "Coffee")

    def test_missing_qty_price_uses_line_amount_literal(self):
        ws = _load(self._rec_two_items())
        # 第 2 个 item(row3):缺 qty/price · 用 line_amount=100 死值 · J=round(100*0.07,2)
        self.assertIsNone(ws.cell(row=3, column=5).value)
        self.assertIsNone(ws.cell(row=3, column=6).value)
        self.assertEqual(ws.cell(row=3, column=7).value, 100.0)
        self.assertEqual(ws.cell(row=3, column=8).value, 100.0)
        self.assertEqual(ws.cell(row=3, column=9).value, 100.0)
        self.assertEqual(ws.cell(row=3, column=10).value, 7.0)


class EdgeCaseTests(unittest.TestCase):
    def test_no_items_single_fallback_row(self):
        ws = _load(
            [
                {
                    "merged_fields": {
                        "date": "2026-03-15",
                        "invoice_number": "X",
                        "total_amount": "500",
                    }
                }
            ]
        )
        # 无 items → 单行兜底(空商品 + total 死值)· openpyxl 空串读回为 None
        self.assertIn(ws.cell(row=2, column=4).value, (None, ""))
        self.assertEqual(ws.cell(row=2, column=7).value, 500.0)
        self.assertIsNone(ws.cell(row=3, column=1).value)  # 只有 1 行数据

    def test_non_dict_records_skipped(self):
        ws = _load([None, "junk", {"merged_fields": {"invoice_number": "Y", "total_amount": "10"}}])
        # 前两个非法被跳过 · 只 Y 落第 2 行
        self.assertEqual(ws.cell(row=2, column=2).value, "Y")
        self.assertIsNone(ws.cell(row=3, column=2).value)

    def test_customer_fallback_to_customer_name(self):
        ws = _load([{"merged_fields": {"customer_name": "FALLBACK", "items": [{"amount": "1"}]}}])
        self.assertEqual(ws.cell(row=2, column=3).value, "FALLBACK")


class FilenameTests(unittest.TestCase):
    def test_filename_format(self):
        fn = et.sales_detail_filename()
        self.assertTrue(fn.startswith("Pearnly_SalesDetail_"))
        self.assertTrue(fn.endswith(".xlsx"))

    def test_filename_custom_prefix(self):
        self.assertTrue(et.sales_detail_filename(prefix="X").startswith("X_"))


if __name__ == "__main__":
    unittest.main()
