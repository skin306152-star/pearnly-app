# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 销项税对账字段级对比引擎 field_comparator.py 行为契约

field_comparator.py(P0-VAT 核对表「逐字段对照」核心)此前 0 专属测试。
纯函数 · 无 DB / 无网络 / 无凭证(Wave 0 安全网 · 零冲突)。

锁定产品哲学铁律(CLAUDE.md P0-VAT):
  - 「核对表生成器 · 不替用户做决定」→ INV/IV 前缀不剥离、买方名不 fuzzy 自动判定
  - 系统只如实展示差异 + 标分类 · 不模糊匹配
覆盖:7 个 normalize_* / parse_date(佛历)/ levenshtein / mod11 / compare_field 9 字段 /
      compare_all_fields(skip_buyer)。
"""

import unittest
from datetime import date

from services.recon import field_comparator as fc


class NormalizeTests(unittest.TestCase):
    def test_normalize_str_nfkc_strip_lower(self):
        self.assertEqual(fc.normalize_str("  ABC  "), "abc")
        self.assertEqual(fc.normalize_str("ＡＢＣ"), "abc")  # 全角→半角
        self.assertEqual(fc.normalize_str(None), "")
        self.assertEqual(fc.normalize_str(""), "")

    def test_normalize_name_drops_all_whitespace(self):
        # 泰/中/日 OCR 排版差:名字内部空格全去
        self.assertEqual(fc.normalize_name("บริษัท  เอ บี ซี"), "บริษัทเอบีซี")
        self.assertEqual(fc.normalize_name("A C M E"), "acme")
        self.assertEqual(fc.normalize_name(None), "")

    def test_normalize_invoice_no_keeps_prefix(self):
        # 铁律:不剥 INV/IV/TAX 前缀(那是替用户判定同一笔)
        self.assertEqual(fc.normalize_invoice_no("INV-001/2026"), "inv0012026")
        self.assertEqual(fc.normalize_invoice_no("INV 001"), "inv001")
        # INV ≠ IV:归一化后仍不同
        self.assertNotEqual(fc.normalize_invoice_no("INV001"), fc.normalize_invoice_no("IV001"))

    def test_normalize_tax_id_digits_only(self):
        self.assertEqual(fc.normalize_tax_id("0-1075-36000-18-8"), "0107536000188")
        self.assertEqual(fc.normalize_tax_id(None), "")
        self.assertEqual(fc.normalize_tax_id("abc"), "")

    def test_normalize_branch_hq_aliases(self):
        # 能匹配的别名(无空格 / NFKC 不变的单 token)
        self.assertEqual(fc.normalize_branch("HQ"), "00000")
        self.assertEqual(fc.normalize_branch("สนญ"), "00000")
        self.assertEqual(fc.normalize_branch(""), "00000")
        self.assertEqual(fc.normalize_branch(None), "00000")
        self.assertEqual(fc.normalize_branch("123"), "00123")  # 数字补零到 5 位
        self.assertEqual(fc.normalize_branch("00000"), "00000")

    def test_multiword_and_thai_hq_aliases_matched(self):
        """已修(REFACTOR-D2):别名集合走同款归一化(NFKC+lower+去空格)后,
        带空格的 "head office" 和泰文 "สำนักงานใหญ่"(NFKC 拆 ำ)都能归一为总部。"""
        self.assertEqual(fc.normalize_branch("Head Office"), "00000")
        self.assertEqual(fc.normalize_branch("สำนักงานใหญ่"), "00000")
        self.assertEqual(fc.normalize_branch("สำนักงานหลัก"), "00000")


class DateParseTests(unittest.TestCase):
    def test_thai_to_gregorian(self):
        self.assertEqual(fc._thai_to_gregorian(2569), 2026)  # 佛历→西历
        self.assertEqual(fc._thai_to_gregorian(2026), 2026)  # 已是西历不变

    def test_parse_date_formats_and_buddhist(self):
        self.assertEqual(fc.parse_date("15/03/2026"), date(2026, 3, 15))
        self.assertEqual(fc.parse_date("2026-03-15"), date(2026, 3, 15))
        self.assertEqual(fc.parse_date("15/03/2569"), date(2026, 3, 15))  # 佛历自动转
        self.assertIsNone(fc.parse_date(""))
        self.assertIsNone(fc.parse_date("not-a-date"))


class LevenshteinTests(unittest.TestCase):
    def test_levenshtein_basic(self):
        self.assertEqual(fc.levenshtein("abc", "abc"), 0)
        self.assertEqual(fc.levenshtein("abc", "abd"), 1)
        self.assertEqual(fc.levenshtein("", "abc"), 3)
        self.assertEqual(fc.levenshtein("abc", ""), 3)
        self.assertEqual(fc.levenshtein("kitten", "sitting"), 3)

    def test_tax_id_fuzzy_distance(self):
        # 归一化后比编辑距离
        self.assertEqual(fc.tax_id_fuzzy_distance("0-1075-36000-18-8", "0107536000188"), 0)
        self.assertEqual(fc.tax_id_fuzzy_distance("0107536000188", "0107536000189"), 1)
        self.assertEqual(fc.tax_id_fuzzy_distance("", "0107536000188"), 99)  # 空 → 99


class FuzzyRatioTests(unittest.TestCase):
    def test_fuzzy_ratio_edges(self):
        self.assertEqual(fc.fuzzy_ratio("", ""), 1.0)
        self.assertEqual(fc.fuzzy_ratio("abc", ""), 0.0)
        self.assertEqual(fc.fuzzy_ratio("", "abc"), 0.0)
        self.assertEqual(fc.fuzzy_ratio("abc", "abc"), 1.0)


class Mod11CheckTests(unittest.TestCase):
    def test_valid_thai_tax_id(self):
        # 0107536000188:check digit 由 Mod-11 算出为 8(见模块公式)
        self.assertTrue(fc.mod11_check("0107536000188"))
        self.assertTrue(fc.mod11_check("0-1075-36000-18-8"))  # 带分隔符也行

    def test_invalid(self):
        self.assertFalse(fc.mod11_check("0107536000189"))  # 末位错
        self.assertFalse(fc.mod11_check("123"))  # 长度不对
        self.assertFalse(fc.mod11_check(""))


class CompareFieldDateTests(unittest.TestCase):
    def test_same_date_matched(self):
        r = fc.compare_field("date", "15/03/2026", "15/03/2026")
        self.assertTrue(r["matched"])

    def test_one_day_diff(self):
        r = fc.compare_field("date", "15/03/2026", "16/03/2026")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "date_diff")

    def test_cross_period_diff(self):
        r = fc.compare_field("invoice_date", "01/01/2026", "01/03/2026")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "date_period_mismatch")

    def test_unparseable_date(self):
        r = fc.compare_field("date", "xx", "15/03/2026")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "date_parse_error")


class CompareFieldInvoiceNoTests(unittest.TestCase):
    def test_visual_normalize_matched(self):
        r = fc.compare_field("invoice_no", "INV-001", "INV001")
        self.assertTrue(r["matched"])

    def test_prefix_not_stripped_mismatch(self):
        # 铁律:INV ≠ IV · 不替用户判定同一笔
        r = fc.compare_field("invoice_no", "INV001", "IV001")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "invoice_no_mismatch")


class CompareFieldNameTests(unittest.TestCase):
    def test_whitespace_diff_matched(self):
        r = fc.compare_field("buyer_name", "A C M E", "ACME")
        self.assertTrue(r["matched"])

    def test_real_diff_mismatch(self):
        r = fc.compare_field("customer_name", "ACME", "BETA")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "name_mismatch")


class CompareFieldTaxIdTests(unittest.TestCase):
    def test_both_empty_matched(self):
        r = fc.compare_field("buyer_tax_id", "", "")
        self.assertTrue(r["matched"])  # 个人买家双空

    def test_same_with_separators_matched(self):
        r = fc.compare_field("buyer_tax_id", "0-1075-36000-18-8", "0107536000188")
        self.assertTrue(r["matched"])

    def test_diff_mismatch(self):
        r = fc.compare_field("buyer_tax_id", "0107536000188", "9999999999999")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "tax_id_mismatch")


class CompareFieldBranchTests(unittest.TestCase):
    def test_hq_aliases_matched(self):
        # "HQ" 与 "00000" 都归一为 00000 → 视为同一总部
        r = fc.compare_field("buyer_branch", "HQ", "00000")
        self.assertTrue(r["matched"])

    def test_diff_mismatch(self):
        r = fc.compare_field("buyer_branch", "00001", "00002")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "branch_mismatch")


class CompareFieldAmountTests(unittest.TestCase):
    def test_within_tolerance_matched(self):
        r = fc.compare_field("amount_pre_vat", "1,000.00", "1000.005")
        self.assertTrue(r["matched"])

    def test_amount_diff(self):
        r = fc.compare_field("net_amount", "1000", "1100")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "amount_diff")

    def test_amount_parse_error(self):
        r = fc.compare_field("amount_pre_vat", "abc", "1000")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "amount_parse_error")

    def test_vat_amount_diff_category(self):
        r = fc.compare_field("vat_amount", "70", "77")
        self.assertFalse(r["matched"])
        self.assertEqual(r["category"], "vat_diff")


class CompareAllFieldsTests(unittest.TestCase):
    def _full_invoice(self):
        return {
            "invoice_date": "15/03/2026",
            "invoice_no": "INV-001",
            "buyer_name": "ACME",
            "buyer_tax_id": "0107536000188",
            "buyer_branch": "00000",
            "amount_pre_vat": "1000.00",
            "vat_amount": "70.00",
        }

    def _full_report(self):
        return {
            "report_date": "15/03/2026",
            "report_invoice_no": "INV001",
            "report_buyer_name": "A C M E",
            "report_buyer_tax_id": "0-1075-36000-18-8",
            "report_buyer_branch": "HQ",
            "report_amount_pre_vat": "1,000.00",
            "report_vat_amount": "70.00",
        }

    def test_all_matched_no_diff(self):
        res = fc.compare_all_fields(self._full_invoice(), self._full_report())
        self.assertFalse(res["has_diff"])
        self.assertEqual(res["categories"], [])
        self.assertEqual(len(res["fields"]), 7)

    def test_one_diff_flagged(self):
        report = self._full_report()
        report["report_vat_amount"] = "99.00"  # 制造差异
        res = fc.compare_all_fields(self._full_invoice(), report)
        self.assertTrue(res["has_diff"])
        self.assertIn("vat_diff", res["categories"])

    def test_skip_buyer_omits_tax_and_branch(self):
        res = fc.compare_all_fields(self._full_invoice(), self._full_report(), skip_buyer=True)
        self.assertNotIn("buyer_tax_id", res["fields"])
        self.assertNotIn("buyer_branch", res["fields"])
        self.assertEqual(len(res["fields"]), 5)


if __name__ == "__main__":
    unittest.main()
