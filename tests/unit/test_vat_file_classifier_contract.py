# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 屏 B 文件智能分类 vat_file_classifier.py 行为契约

vat_file_classifier.py 的「零成本快路径」此前 0 专属测试。
只测纯/确定性部分(不碰需要 Gemini key + 网络的 classify_with_gemini):
  - _filename_guess:文件名正则判 invoice / vat_report / None
  - _excel_quick_meta:Excel 头部轻量扫税号 / 期间(含佛历)/ 卖方名 · 不走 Gemini

这条快路径每命中一次 = 省一次 Gemini 调用(成本)· 值得守门。
"""

import io
import unittest

import openpyxl

import vat_file_classifier as vfc


class FilenameGuessTests(unittest.TestCase):
    def test_invoice_hints(self):
        self.assertEqual(vfc._filename_guess("invoice.pdf"), "invoice")
        self.assertEqual(vfc._filename_guess("INV001.pdf"), "invoice")  # \bINV\d
        self.assertEqual(vfc._filename_guess("ใบกำกับภาษี.pdf"), "invoice")
        self.assertEqual(vfc._filename_guess("tax-invoice.jpg"), "invoice")
        self.assertEqual(vfc._filename_guess("receipt.jpg"), "invoice")

    def test_report_hints(self):
        self.assertEqual(vfc._filename_guess("รายงานภาษีขาย.xlsx"), "vat_report")
        self.assertEqual(vfc._filename_guess("PP30_march.xlsx"), "vat_report")  # pp30 子串
        self.assertEqual(vfc._filename_guess("sales_tax_2026.xlsx"), "vat_report")  # sales_tax

    def test_no_hint_returns_none(self):
        self.assertIsNone(vfc._filename_guess("random_scan.jpg"))
        self.assertIsNone(vfc._filename_guess(""))
        self.assertIsNone(vfc._filename_guess(None))

    def test_invoice_checked_before_report(self):
        # 同时含 invoice 与 vat 关键词 → invoice 优先(先判 invoice hints)
        self.assertEqual(vfc._filename_guess("vat-invoice.pdf"), "invoice")

    @unittest.expectedFailure
    def test_KNOWN_GAP_underscore_breaks_word_boundary_hints(self):
        r"""🐛 已知缺口(待 Zihao 拍板):\binvoice\b / \binv\b / \bvat\b 用 \b 词边界,
        但 '_' 是正则单词字符 → 'invoice_2026.pdf' 在 invoice 与 _ 间无边界 → 匹配不上,
        这种超常见文件名落不到零成本快路径 · 白白多调一次 Gemini(成本)。
        修法:hint 改用 [\W_] 边界(把下划线也视作分隔)或先把 _ 归一成空格再匹配。
        """
        self.assertEqual(vfc._filename_guess("invoice_2026.pdf"), "invoice")


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class ExcelQuickMetaTests(unittest.TestCase):
    def test_extracts_taxid_buddhist_period_and_name(self):
        data = _xlsx(
            [
                ["รายงานภาษีขาย"],  # row1 标题(不算卖方名)
                ["บริษัท เทสต์ จำกัด เลขประจำตัวผู้เสียภาษี 0107536000188"],  # row2 卖方+税号
                ["ประจำเดือน 03/2569"],  # row3 佛历期间
            ]
        )
        tax_id, year, month, name = vfc._excel_quick_meta(data)
        self.assertEqual(tax_id, "0107536000188")
        self.assertEqual(year, 2026)  # 佛历 2569 → 西历 2026
        self.assertEqual(month, 3)
        self.assertIn("บริษัท เทสต์ จำกัด", name)

    def test_western_period(self):
        data = _xlsx(
            [
                ["title"],
                ["Co., Ltd.  0107536000188"],
                ["Period 3/2026"],
            ]
        )
        tax_id, year, month, name = vfc._excel_quick_meta(data)
        self.assertEqual(tax_id, "0107536000188")
        self.assertEqual(year, 2026)
        self.assertEqual(month, 3)

    def test_title_row_not_taken_as_name(self):
        # row1 含公司关键词也不算 name(i>=2 才取)
        data = _xlsx(
            [
                ["บริษัท หัวเรื่อง จำกัด"],  # row1
                ["รายการ"],
            ]
        )
        _, _, _, name = vfc._excel_quick_meta(data)
        self.assertEqual(name, "")

    def test_bad_bytes_return_all_empty(self):
        self.assertEqual(vfc._excel_quick_meta(b"not an xlsx file"), ("", None, None, ""))


if __name__ == "__main__":
    unittest.main()
