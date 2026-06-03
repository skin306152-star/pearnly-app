# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 报表引擎后端 i18n 字典 i18n_reports.py 行为契约

i18n_reports.py(后端独立报表 i18n · 模板名/列头/标题/合计)此前 0 专属测试。
纯字典 + 取值函数(无 DB/网络/凭证 · Wave 0 安全网 · 零冲突)。

最大价值:把模块里只「打印警告」的软自检 _self_check 升级成 **硬 CI 守门**——
缺任一语言(zh/th/en/ja)直接红,贴合 CLAUDE.md「4 语 i18n 完整性铁律」。
"""

import unittest

from services.report import i18n_reports as ir

_LANGS = ("zh", "th", "en", "ja")


class FourLangCompletenessTests(unittest.TestCase):
    def test_every_key_has_all_four_langs_nonempty(self):
        missing = []
        for key, entry in ir.REPORTS_I18N.items():
            for lang in _LANGS:
                if not entry.get(lang):
                    missing.append(f"{key}.{lang}")
        self.assertEqual(missing, [], f"报表 i18n 缺译: {missing[:10]}")

    def test_self_check_passes(self):
        self.assertTrue(ir._self_check())

    def test_no_stray_lang_keys(self):
        # 每条只允许 4 语 key · 防混入拼写错的语言码(如 'cn' / 'jp')
        for key, entry in ir.REPORTS_I18N.items():
            extra = set(entry.keys()) - set(_LANGS)
            self.assertEqual(extra, set(), f"{key} 含非法语言码 {extra}")


class I18nGetTests(unittest.TestCase):
    def test_returns_requested_lang(self):
        self.assertEqual(ir.i18n_get("en", "tpl-standard"), "Standard Detail")
        self.assertEqual(ir.i18n_get("zh", "tpl-standard"), "标准明细")

    def test_unknown_lang_falls_back_to_en(self):
        self.assertEqual(ir.i18n_get("fr", "tpl-standard"), "Standard Detail")

    def test_missing_key_returns_key_itself(self):
        self.assertEqual(ir.i18n_get("en", "no-such-key"), "no-such-key")

    def test_missing_key_returns_default_when_given(self):
        self.assertEqual(ir.i18n_get("en", "no-such-key", default="DFLT"), "DFLT")


class I18nFormatTests(unittest.TestCase):
    def test_placeholder_substitution(self):
        out = ir.i18n_format("en", "tpl-input-vat-title", client="ACME", month="2026-05")
        self.assertIn("ACME", out)
        self.assertIn("2026-05", out)
        self.assertNotIn("{client}", out)
        self.assertNotIn("{month}", out)

    def test_missing_placeholder_returns_template_no_crash(self):
        # 少给 kwargs 不应抛 · 返回原模板(含未替换占位符)
        out = ir.i18n_format("en", "tpl-input-vat-title", client="ACME")
        self.assertIn("{month}", out)

    def test_format_on_plain_key_passthrough(self):
        # 无占位符的 key:format 不影响内容
        self.assertEqual(ir.i18n_format("en", "tpl-standard"), "Standard Detail")


if __name__ == "__main__":
    unittest.main()
