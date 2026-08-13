# -*- coding: utf-8 -*-
"""计费单位判据单源守门(services/billing/pricing · 2026-08-13 收口)。

此前「扩展名分类 + 遍历估 units」抄了 5 份散在 routes 与 recon_jobs,预检与实扣口径
一漂就是在钱上撒谎。锁定:
  1. EXCEL_BILLING_EXTS 八项字符档判据(与事后 charge_ocr_async 分类逐字一致)
  2. file_ext 归一(大小写/无扩展名)
  3. estimate_recon_units:多页 PDF 按物理页数(B3 · 不再按 1 件 1 页低估)·
     图片/坏件按 1 页 · 字符档按估算字符
  4. billed_units_for_parses:失败件/0 行件不收钱 · PDF 走页/行折算取大
"""

import unittest
from unittest import mock

from core import db  # noqa: F401 - 必须先于 services.billing(dal_reexports 循环导入)
from services.billing import pricing


def _pdf_bytes(pages: int) -> bytes:
    import fitz

    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    return doc.tobytes()


class ExtClassificationTests(unittest.TestCase):
    def test_excel_billing_exts_locked(self):
        # 事后扣费的「字符」档扩展名 · 预检按同一组切分 · 少一项就有入口口径分叉
        self.assertEqual(
            pricing.EXCEL_BILLING_EXTS,
            frozenset({".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}),
        )

    def test_file_ext_normalizes(self):
        self.assertEqual(pricing.file_ext("A.XLSX"), ".xlsx")
        self.assertEqual(pricing.file_ext("stmt.v2.pdf"), ".pdf")
        self.assertEqual(pricing.file_ext("noext"), "")
        self.assertEqual(pricing.file_ext(""), "")
        self.assertEqual(pricing.file_ext(None), "")


class EstimateReconUnitsTests(unittest.TestCase):
    def test_multipage_pdf_counts_physical_pages(self):
        # B3:3 页 PDF → 3 个 pdf_units(旧口径按 1 件 1 页 · 大 PDF 打穿余额)
        self.assertEqual(pricing.estimate_recon_units([(_pdf_bytes(3), "stmt.pdf")]), (3, 0))

    def test_image_and_unreadable_min_one_page(self):
        self.assertEqual(pricing.estimate_recon_units([(b"\xff\xd8jpeg", "scan.jpg")]), (1, 0))
        self.assertEqual(pricing.estimate_recon_units([(b"broken", "x.pdf")]), (1, 0))

    def test_char_files_counted_as_chars(self):
        self.assertEqual(pricing.estimate_recon_units([(b"a" * 500, "gl.csv")]), (0, 500))
        self.assertEqual(pricing.estimate_recon_units([(b"a" * 200, "gl.tsv")]), (0, 200))

    def test_mixed_batch_sums_both_sides(self):
        files = [(_pdf_bytes(2), "a.pdf"), (b"a" * 300, "b.txt"), (b"img", "c.png")]
        self.assertEqual(pricing.estimate_recon_units(files), (3, 300))

    def test_empty_batch(self):
        self.assertEqual(pricing.estimate_recon_units([]), (0, 0))
        self.assertEqual(pricing.estimate_recon_units(None), (0, 0))


class BilledUnitsForParsesTests(unittest.TestCase):
    def test_failed_and_zero_row_files_not_billed(self):
        pairs = [
            ({"ok": False, "rows": [{}]}, (_pdf_bytes(2), "bad.pdf")),
            ({"ok": True, "rows": []}, (_pdf_bytes(2), "empty.pdf")),
        ]
        self.assertEqual(pricing.billed_units_for_parses(pairs), (0, 0))

    def test_pdf_uses_page_row_center_rule(self):
        # 1 页 100 行 → ⌈100/40⌉ = 3(密集账单不被按页低估 · v118.35.0.58 口径)
        pairs = [({"ok": True, "rows": [{}] * 100}, (_pdf_bytes(1), "dense.pdf"))]
        self.assertEqual(pricing.billed_units_for_parses(pairs), (3, 0))

    def test_excel_billed_by_chars(self):
        pairs = [({"ok": True, "rows": [{}]}, (b"a" * 500, "gl.csv"))]
        self.assertEqual(pricing.billed_units_for_parses(pairs), (0, 500))

    def test_mixed_batch(self):
        pairs = [
            ({"ok": True, "rows": [{}] * 10}, (_pdf_bytes(2), "a.pdf")),
            ({"ok": True, "rows": [{}]}, (b"a" * 100, "b.csv")),
            ({"ok": False}, (b"a" * 999, "c.csv")),
        ]
        self.assertEqual(pricing.billed_units_for_parses(pairs), (2, 100))

    def test_count_pages_patchable_at_source(self):
        # 调用方测试 patch services.ocr.pdf_utils.count_pdf_pages 必须能生效(函数内 late import)
        with mock.patch("services.ocr.pdf_utils.count_pdf_pages", return_value=7):
            self.assertEqual(pricing.estimate_recon_units([(b"x", "s.pdf")]), (7, 0))


if __name__ == "__main__":
    unittest.main()
