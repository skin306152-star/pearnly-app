# -*- coding: utf-8 -*-
"""POS Google Sheet 表头/付款方式标签(services/pos/sheets_labels)守门测试。

锁定:四语齐全(表头/付款方式都不写死单一语言)+ 未知语言/方式回落安全。
"""

import unittest

from services.pos import sheets_labels as labels


class NormLangTests(unittest.TestCase):
    def test_known_lang_passthrough(self):
        for lg in labels.LANGS:
            self.assertEqual(labels.norm_lang(lg), lg)

    def test_unknown_lang_falls_back_to_th(self):
        self.assertEqual(labels.norm_lang("fr"), "th")
        self.assertEqual(labels.norm_lang(""), "th")
        self.assertEqual(labels.norm_lang(None), "th")


class HeaderRowTests(unittest.TestCase):
    def test_all_four_languages_produce_full_header(self):
        for lg in labels.LANGS:
            row = labels.header_row(lg)
            self.assertEqual(len(row), 13)
            self.assertTrue(all(isinstance(c, str) and c for c in row))

    def test_different_languages_produce_different_text(self):
        self.assertNotEqual(labels.header_row("zh"), labels.header_row("en"))
        self.assertNotEqual(labels.header_row("th"), labels.header_row("ja"))


class MethodLabelTests(unittest.TestCase):
    def test_known_method_localized(self):
        self.assertEqual(labels.method_label("transfer", "zh"), "银行转账")
        self.assertEqual(labels.method_label("transfer", "en"), "Bank Transfer")
        self.assertEqual(labels.method_label("cash", "ja"), "現金")

    def test_unknown_method_passthrough(self):
        self.assertEqual(labels.method_label("bitcoin", "zh"), "bitcoin")
        self.assertEqual(labels.method_label("", "zh"), "")


if __name__ == "__main__":
    unittest.main()
