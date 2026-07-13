# -*- coding: utf-8 -*-
"""PDF 泰文字体注册守门(usage_report_pdf_text._register_fonts)。

prod 实锤(2026-07-13 K2 金标验收):系统泰文字体路径一个都不在(fc-list thai=0,
wqy 泰文字形为零),泰文 PDF(销项发票/报税材料/K2)全线渲染 notdef 方块——修法 =
查找列表末位兜底仓库捆绑 Sarabun(proof_pdf 同源,OFL)。本测试钉住:不管系统字体
在不在,注册完 _HAS_THAI 必须为 True,泰文段落绝不落到无泰文字形的字体上。
"""

from __future__ import annotations

import os
import unittest

from services.usage import usage_report_pdf_text as fonts


def _reset_registration():
    fonts._FONTS_REGISTERED = False
    fonts._BASE_FONT = "Helvetica"
    fonts._BOLD_FONT = "Helvetica-Bold"
    fonts._HAS_CJK = False
    fonts._HAS_THAI = False
    fonts._HAS_THAI_BOLD = False


class BundledThaiFontTests(unittest.TestCase):
    def setUp(self):
        self._saved = (
            fonts._FONTS_REGISTERED,
            fonts._BASE_FONT,
            fonts._BOLD_FONT,
            fonts._HAS_CJK,
            fonts._HAS_THAI,
            fonts._HAS_THAI_BOLD,
        )
        _reset_registration()

    def tearDown(self):
        (
            fonts._FONTS_REGISTERED,
            fonts._BASE_FONT,
            fonts._BOLD_FONT,
            fonts._HAS_CJK,
            fonts._HAS_THAI,
            fonts._HAS_THAI_BOLD,
        ) = self._saved

    def test_bundled_sarabun_exists_in_repo(self):
        base = os.path.join(os.path.dirname(fonts.__file__), "..", "export", "fonts")
        self.assertTrue(os.path.exists(os.path.join(base, "Sarabun-Regular.ttf")))
        self.assertTrue(os.path.exists(os.path.join(base, "Sarabun-Bold.ttf")))

    def test_thai_font_registered_even_without_system_fonts(self):
        fonts._register_fonts()
        self.assertTrue(fonts._HAS_THAI)
        self.assertTrue(fonts._HAS_THAI_BOLD)

    def test_thai_runs_never_fall_back_to_glyphless_font(self):
        fonts._register_fonts()
        markup = fonts._build_paragraph_text("ใบกำกับภาษี INV-001")
        self.assertIn('name="PR-Thai"', markup)
        self.assertNotIn('Helvetica">ใบ', markup)

    def test_bold_thai_uses_registered_bold_only(self):
        fonts._register_fonts()
        fonts._HAS_THAI_BOLD = False  # 模拟 bold 注册失败:绝不引用没注册的字体名
        markup = fonts._build_paragraph_text("ภาษี", bold=True)
        self.assertNotIn("PR-ThaiBold", markup)
        self.assertIn('name="PR-Thai"', markup)


if __name__ == "__main__":
    unittest.main()
