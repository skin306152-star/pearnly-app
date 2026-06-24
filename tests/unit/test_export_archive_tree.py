# -*- coding: utf-8 -*-
"""Drive 归档树路径/命名(export.archive_tree)· 纯逻辑 · 照逆向 schema(阶段二)。

锁:根 Pearnly · 月份夹 MM_泰文月名 · 单据基名 日期_商户_id(三处串联)· 证据每票一夹 ·
交会计 PDF 扁平 · 名清洗(去 /\ 控制符,空退 fallback)。
"""

import unittest
from datetime import date

from services.export import archive_tree as at


class MonthAndSheetTests(unittest.TestCase):
    def test_month_folder_thai(self):
        self.assertEqual(at.month_folder(6), "06_มิถุนายน")
        self.assertEqual(at.month_folder(1), "01_มกราคม")
        self.assertEqual(at.month_folder(12), "12_ธันวาคม")

    def test_month_folder_follows_language(self):
        self.assertEqual(at.month_folder(6, "zh"), "06_六月")
        self.assertEqual(at.month_folder(6, "en"), "06_June")
        self.assertEqual(at.month_folder(6, "ja"), "06_6月")

    def test_month_folder_out_of_range_falls_back(self):
        self.assertEqual(at.month_folder(13), "13")

    def test_sheet_name(self):
        self.assertEqual(at.sheet_name("บริษัท A", 2026), "บริษัท A - 2026")


class DocBasenameTests(unittest.TestCase):
    def test_basename_with_iso_string(self):
        self.assertEqual(at.doc_basename("2026-06-01", "Cafe", "D1"), "2026-06-01_Cafe_D1")

    def test_basename_with_date_object(self):
        self.assertEqual(at.doc_basename(date(2026, 6, 1), "Cafe", "D1"), "2026-06-01_Cafe_D1")

    def test_basename_sanitizes_slashes(self):
        # 商户名带 / → 清洗成空格,不破坏路径层级
        self.assertEqual(at.doc_basename("2026-06-01", "A/B Co", "D1"), "2026-06-01_A B Co_D1")

    def test_basename_empty_supplier_fallback(self):
        self.assertEqual(at.doc_basename("2026-06-01", "", "D1"), "2026-06-01_ผู้ขาย_D1")
        self.assertEqual(at.doc_basename("2026-06-01", "", "D1", "zh"), "2026-06-01_供应商_D1")


class TreePathTests(unittest.TestCase):
    def test_evidence_folder_path(self):
        p = at.evidence_folder_path("主体X", "2026-06-01", "Cafe", "D1")
        self.assertEqual(
            p, ["Pearnly", "主体X", "2026", "06_มิถุนายน", "หลักฐาน", "2026-06-01_Cafe_D1"]
        )
        zh = at.evidence_folder_path("主体X", "2026-06-01", "Cafe", "D1", "zh")
        self.assertEqual(zh, ["Pearnly", "主体X", "2026", "06_六月", "证据", "2026-06-01_Cafe_D1"])

    def test_accountant_dir_and_pdf(self):
        d = at.accountant_dir_path("主体X", "2026-06-01")
        self.assertEqual(d, ["Pearnly", "主体X", "2026", "06_มิถุนายน", "ส่งบัญชี"])
        self.assertEqual(
            at.accountant_dir_path("主体X", "2026-06-01", "en"),
            ["Pearnly", "主体X", "2026", "06_June", "For accountant"],
        )
        self.assertEqual(
            at.accountant_pdf_name("2026-06-01", "Cafe", "D1"), "2026-06-01_Cafe_D1.pdf"
        )

    def test_subject_year_path(self):
        self.assertEqual(at.subject_year_path("主体X", 2026), ["Pearnly", "主体X", "2026"])

    def test_doc_id_threads_through_evidence_and_pdf(self):
        # doc_id 在证据夹名与 PDF 名两处一致(可追溯)
        ev = at.evidence_folder_path("主体X", "2026-06-01", "Cafe", "DOC-9")[-1]
        pdf = at.accountant_pdf_name("2026-06-01", "Cafe", "DOC-9")
        self.assertIn("DOC-9", ev)
        self.assertIn("DOC-9", pdf)


if __name__ == "__main__":
    unittest.main()
