# -*- coding: utf-8 -*-
"""前门盘点纯函数(services/front_desk/inventory.py · FD-0a 验收断言③ ≥8 例)。

覆盖:图片(jpg/png/heic)/ 银行流水(PDF 文件名 / xlsx 文件名)/ Excel 表格(销售汇总)/
GL 台账 / 待识别 PDF / 不认识文件(不支持格式/无扩展)。归组口径委托 sort._bin_by_file,
本测试锁「盘点卡分组映射」正确 + 摘要计数诚实(recognized/unrecognized)。
"""

import unittest

from services.front_desk import inventory


class ClassifyTests(unittest.TestCase):
    def test_image_jpg(self):
        self.assertEqual(inventory.classify("IMG_2647.JPG"), inventory.IMAGE)

    def test_image_png(self):
        self.assertEqual(inventory.classify("receipt.png"), inventory.IMAGE)

    def test_image_heic(self):
        self.assertEqual(inventory.classify("photo.heic"), inventory.IMAGE)

    def test_bank_pdf_by_filename(self):
        self.assertEqual(inventory.classify("kbank_statement_202505.pdf"), inventory.BANK_STATEMENT)

    def test_bank_xlsx_by_filename(self):
        self.assertEqual(inventory.classify("KBANK_may.xlsx"), inventory.BANK_STATEMENT)

    def test_sales_summary_xlsx(self):
        self.assertEqual(inventory.classify("sales_summary.xlsx"), inventory.SPREADSHEET)

    def test_gl_ledger_pdf(self):
        self.assertEqual(inventory.classify("GL_2025.pdf"), inventory.GL_LEDGER)

    def test_gl_ledger_thai_name(self):
        self.assertEqual(inventory.classify("สมุดแยกประเภท.pdf"), inventory.GL_LEDGER)

    def test_unnamed_pdf_needs_identification(self):
        self.assertEqual(inventory.classify("scan001.pdf"), inventory.PDF_UNIDENTIFIED)

    def test_unsupported_extension_unrecognized(self):
        self.assertEqual(inventory.classify("notes.txt"), inventory.UNRECOGNIZED)

    def test_no_extension_unrecognized(self):
        self.assertEqual(inventory.classify("mysteryfile"), inventory.UNRECOGNIZED)


class SummarizeTests(unittest.TestCase):
    def test_mixed_batch_counts_and_grouping(self):
        out = inventory.summarize(
            [
                "IMG_1.jpg",
                "IMG_2.png",
                "kbank_statement.pdf",
                "sales.xlsx",
                "notes.txt",  # 不认识
            ]
        )
        self.assertEqual(out["total"], 5)
        self.assertEqual(out["unrecognized"], 1)
        self.assertEqual(out["recognized"], 4)
        groups = {g["group"]: g["count"] for g in out["groups"]}
        self.assertEqual(groups.get(inventory.IMAGE), 2)
        self.assertEqual(groups.get(inventory.BANK_STATEMENT), 1)
        self.assertEqual(groups.get(inventory.SPREADSHEET), 1)
        self.assertEqual(groups.get(inventory.UNRECOGNIZED), 1)

    def test_groups_follow_display_order(self):
        out = inventory.summarize(["notes.txt", "IMG.jpg"])  # 乱序进,盘点卡按 GROUP_ORDER 出
        order = [g["group"] for g in out["groups"]]
        self.assertEqual(order, [inventory.IMAGE, inventory.UNRECOGNIZED])

    def test_empty_batch_returns_zeroed_structure_not_none(self):
        out = inventory.summarize([])
        self.assertEqual(out, {"groups": [], "total": 0, "recognized": 0, "unrecognized": 0})


if __name__ == "__main__":
    unittest.main()
