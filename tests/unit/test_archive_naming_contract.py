# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 智能归档命名 archive.py 行为契约

archive.py(按模板 + 一条 OCR 历史生成合法归档文件名)此前 0 专属测试。
纯函数 · 无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。

锁定:非法字符清洗(跨 Win/Linux/mac)· 供应商简称去后缀 · 日期/金额格式化 ·
模板拼接 + 空字段不留双分隔符 + 兜底 + 限长。
"""

import unittest

import archive


class SanitizeTests(unittest.TestCase):
    def test_illegal_chars_to_underscore(self):
        self.assertEqual(archive._sanitize("a/b:c*d?"), "a_b_c_d")

    def test_spaces_to_underscore(self):
        self.assertEqual(archive._sanitize("a   b"), "a_b")

    def test_fold_repeats_and_strip(self):
        self.assertEqual(archive._sanitize("__a___b__"), "a_b")
        self.assertEqual(archive._sanitize(""), "")


class ShortSellerTests(unittest.TestCase):
    def test_strips_thai_company_affixes(self):
        self.assertEqual(archive._short_seller("บริษัท DHL จำกัด"), "DHL")

    def test_strips_english_suffix(self):
        self.assertEqual(archive._short_seller("Acme Co., Ltd."), "Acme")

    def test_strips_chinese_suffix(self):
        self.assertEqual(archive._short_seller("顺丰有限公司"), "顺丰")

    def test_ascii_length_cap_30(self):
        out = archive._short_seller("A" * 50)
        self.assertEqual(len(out), 30)


class FormatDateTests(unittest.TestCase):
    def test_iso_passthrough(self):
        self.assertEqual(archive._format_date("2026-04-15", "YYYY-MM-DD"), "2026-04-15")

    def test_reformat_to_custom(self):
        self.assertEqual(archive._format_date("15/04/2026", "DD-MM-YYYY"), "15-04-2026")

    def test_unparseable_returns_sanitized_head(self):
        self.assertEqual(archive._format_date("garbage", "YYYY-MM-DD"), "garbage")

    def test_empty(self):
        self.assertEqual(archive._format_date("", "YYYY-MM-DD"), "")


class FormatAmountTests(unittest.TestCase):
    def test_with_currency_rounds_int(self):
        self.assertEqual(archive._format_amount("1234.6", True), "THB1235")

    def test_without_currency(self):
        self.assertEqual(archive._format_amount("1250.00", False), "1250")

    def test_comma_and_empty_and_bad(self):
        self.assertEqual(archive._format_amount("1,250", True), "THB1250")
        self.assertEqual(archive._format_amount("", True), "")
        self.assertEqual(archive._format_amount(None, True), "")
        self.assertEqual(archive._format_amount("abc", True), "")


class BuildArchiveNameTests(unittest.TestCase):
    def test_default_template_full_record(self):
        rec = {
            "date": "2026-04-15",
            "seller_name": "บริษัท DHL จำกัด",
            "category_tag": "运费",
            "total_amount": "1250.00",
        }
        self.assertEqual(archive.build_archive_name(rec), "2026-04-15_DHL_运费_THB1250")

    def test_empty_fields_collapse_separators(self):
        # 只有日期 · 其余空 → 不留尾部双下划线
        self.assertEqual(archive.build_archive_name({"date": "2026-04-15"}), "2026-04-15")

    def test_fallback_to_unknown_when_all_empty(self):
        self.assertEqual(archive.build_archive_name({}), "unknown")

    def test_fallback_to_filename(self):
        self.assertEqual(archive.build_archive_name({"filename": "scan001"}), "scan001")

    def test_length_capped(self):
        rec = {"seller_name": "X" * 400}
        out = archive.build_archive_name(rec, template=[{"type": "seller", "short": False}])
        self.assertLessEqual(len(out), archive.MAX_FILENAME_LEN)

    def test_reads_merged_fields_nested(self):
        rec = {"merged_fields": {"date": "2026-04-15", "total_amount": "100"}}
        out = archive.build_archive_name(rec)
        self.assertIn("2026-04-15", out)
        self.assertIn("THB100", out)


class PreviewNameTests(unittest.TestCase):
    def test_preview_wraps_merged_fields(self):
        out = archive.preview_name({"date": "2026-04-15", "total_amount": "100"})
        self.assertIn("2026-04-15", out)
        self.assertIn("THB100", out)


if __name__ == "__main__":
    unittest.main()
