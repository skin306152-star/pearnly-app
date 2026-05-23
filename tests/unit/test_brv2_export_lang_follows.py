# -*- coding: utf-8 -*-
"""
BUG-FIX-T3 v118.35.0.44 · 守门测试 · M4 _brv2Export 导出 Excel 传 lang 跟随 UI 当前语言
BUG-FIX-T5 v118.35.0.46 · 扩展锁 M2 / M3 export lang 也跟 UI 走(2026-05-23 audit 4 模块同步)

锁定 4 个契约:
  1. M4 home.js _brv2Export 必须 fetch 时拼 ?lang=window._currentLang(不能 hardcode)
  2. M4 export_bank_recon_excel 4 语 _RECON_TITLE 都齐(zh/th/en/ja)
  3. M2 export URL `/api/recon/export/<tid>` 必须用 _curLang 动态(不能 hardcode)
  4. M3 export URL `/api/recon/gl-vat/<tid>/export` 必须用 _lang() 动态(不能 hardcode)
"""
import io
import os
import re
import unittest

import openpyxl

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ExportLangFollowsUiTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "home.js"), "r", encoding="utf-8") as f:
            cls.home_js = f.read()

    def test_brv2_export_passes_window_current_lang(self):
        """契约 1 · _brv2Export 必须用 window._currentLang 拼 URL · 不能 hardcode"""
        # 找 _brv2Export 函数体
        m = re.search(
            r'async function _brv2Export\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
            self.home_js, re.DOTALL,
        )
        # 容错:函数体可能含嵌套 {} · 用更宽匹配 · 找到调用点即可
        self.assertIn("async function _brv2Export", self.home_js,
            "_brv2Export function definition missing in home.js")
        # 必须含 window._currentLang(直接) 或 _currentLang(变量赋值后用)
        # 检查 _brv2Export 内 fetch 调用拼 ?lang=
        # 先取 _brv2Export 函数体后约 600 字符(应该够覆盖 fetch 调用)
        idx = self.home_js.find("async function _brv2Export")
        self.assertGreater(idx, 0)
        body = self.home_js[idx:idx + 800]
        # 必须 fetch /api/recon/bank-v2/.*/export?lang=
        self.assertIn("/api/recon/bank-v2/", body)
        self.assertIn("/export?lang=", body)
        # lang 必须来自 window._currentLang(允许 || 'zh' fallback)
        self.assertRegex(body, r"window\._currentLang\s*\|\|\s*['\"]",
            "_brv2Export 必须用 window._currentLang || 'fallback' 取 lang · 不能 hardcode 单一语言")
        # 防 hardcode 单一语言(grep 不能有 lang=th / lang=en / lang=zh / lang=ja 在 fetch URL)
        for bad in ["?lang=th'", "?lang=th\"", "?lang=en'", "?lang=zh'", "?lang=ja'"]:
            self.assertNotIn(bad, body,
                f"_brv2Export 不能 hardcode {bad} · 必须用 window._currentLang")

    def test_export_bank_recon_excel_lang_4_languages_complete(self):
        """契约 2 · export_bank_recon_excel 4 语 _RECON_TITLE 全到 · 调用时跟 lang 走"""
        from bank_recon_v2 import (
            BankReconSummary, BankReconRow,
            export_bank_recon_excel,
        )
        from datetime import date

        summary = BankReconSummary(
            bank_code="kbank", gl_account_code="113001",
            stmt_opening=1000.0, gl_opening=1010.0,
            stmt_closing=2000.0, gl_closing=2010.0,
            opening_diff=-10.0, formula_stmt_closing=2000.0, formula_diff=0.0,
        )
        rows = [BankReconRow(
            match_status="matched", match_layer="L1",
            stmt_date=None, stmt_desc="t", stmt_withdrawal=0.0, stmt_deposit=100.0,
            gl_date=None, gl_doc_no="V1", gl_desc="t", gl_debit=100.0, gl_credit=0.0,
        )]

        # 4 语 title 都应该不同 · 证明 lang 参数生效
        titles = {}
        for lang in ("zh", "th", "en", "ja"):
            b = export_bank_recon_excel(rows, summary, lang=lang)
            wb = openpyxl.load_workbook(io.BytesIO(b))
            ws1 = wb.worksheets[0]
            # Sheet 1 标题在 A1(merged · 含 _RECON_TITLE + bank_code)
            title = ws1["A1"].value or ""
            titles[lang] = title
        # 4 语标题必须各不同(不能全部输出同一种语言)
        unique_titles = set(titles.values())
        self.assertEqual(len(unique_titles), 4,
            f"4 语应该输出 4 种不同的 title · 实际 {len(unique_titles)} 种: {titles}")
        # 验证关键关键词在各自语言里
        self.assertIn("银行对账", titles["zh"])
        self.assertIn("Bank Reconciliation", titles["en"])
        self.assertIn("กระทบยอด", titles["th"])
        self.assertIn("銀行照合", titles["ja"])

    def test_m2_export_uses_dynamic_lang_not_hardcoded(self):
        """BUG-FIX-T5 契约 3 · M2 (销售税对账) export URL 必须用 _curLang · 不能 hardcode 单一语言
        触发场景: home.js L30720 附近的 M2 export 函数
        """
        # M2 export URL 关键模式: '/api/recon/export/' + taskId + '?lang=' + _curLang
        m2_pattern = re.search(
            r"/api/recon/export/['\"]?\s*\+\s*[\w.()\[\]]+\s*\+\s*['\"]\?lang=['\"]\s*\+\s*([\w()._]+)",
            self.home_js,
        )
        self.assertIsNotNone(m2_pattern,
            "M2 export URL pattern not found in home.js · 可能被改成 hardcode lang=xxx")
        lang_expr = m2_pattern.group(1)
        # lang 表达式必须含 _curLang 或 currentLang 等动态变量 · 不能是字面 'th'/'en' 等
        self.assertRegex(lang_expr, r"(?:_curLang|currentLang|_lang)",
            f"M2 export lang 表达式应该动态({lang_expr})· 不能 hardcode")

    def test_m3_export_uses_dynamic_lang_not_hardcoded(self):
        """BUG-FIX-T5 契约 4 · M3 (收入对账) export URL 必须用 _lang() · 不能 hardcode
        触发场景: home.js L32737 / L32845 附近的 M3 gl-vat export 函数
        """
        # M3 export URL 关键模式: '/api/recon/gl-vat/' + taskId + '/export?lang=' + _lang()
        m3_pattern = re.findall(
            r"/api/recon/gl-vat/[^?]+\?lang=['\"]?\s*\+\s*[^,)]+",
            self.home_js,
        )
        self.assertGreater(len(m3_pattern), 0,
            "M3 gl-vat export URL pattern not found in home.js")
        # 至少 1 处含动态 lang
        any_dynamic = False
        for snippet in m3_pattern:
            if re.search(r"(?:_lang\(\)|_curLang|currentLang|encodeURIComponent\(_lang)", snippet):
                any_dynamic = True
                break
        self.assertTrue(any_dynamic,
            f"M3 gl-vat export lang 必须用 _lang() 动态 · 实际 patterns: {m3_pattern}")


if __name__ == "__main__":
    unittest.main()
