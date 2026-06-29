# -*- coding: utf-8 -*-
"""回归守门:多票复核原图必须能翻到每张票所在物理页,不能写死只取 page/1.png。

血泪:一份 3 票 PDF 跨 2 物理页,原图却恒取 page/1.png → 第三张(第 2 页)的图永远
看不到("三票只显示两图")。此测试钉住:原图 fetch 按页参数化 + 每张票有跳页入口 +
page_indices 已从识别响应透出。
"""

import re
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src" / "home"
_REVIEW = _SRC / "dms-intake-review.ts"
_INVOICE = _SRC / "dms-intake-invoice.ts"


class ImagePagingRegressionTests(unittest.TestCase):
    def test_loadimage_is_page_parameterized(self):
        src = _REVIEW.read_text(encoding="utf-8")
        self.assertNotIn("/page/1.png", src, "原图不应写死 page/1.png(治三票两图)")
        self.assertRegex(src, r"/page/\$\{page\}\.png", "原图 fetch 应按 page 参数化")
        self.assertIn("X-Page-Count", src, "应读 X-Page-Count 决定能否翻页")

    def test_per_invoice_jump_and_nav(self):
        src = _REVIEW.read_text(encoding="utf-8")
        self.assertIn("dx-inv-viewpage", src, "每张票应有'看此张原图'跳页入口")
        self.assertIn("dx-page-next", src, "应有翻页控件")
        self.assertIn("gotoViewerPage", src, "应有跳页函数")

    def test_page_indices_surfaced(self):
        src = _INVOICE.read_text(encoding="utf-8")
        self.assertIn("pageIndices", src, "IvInvoice 应带 pageIndices")
        self.assertIn("page_indices", src, "应从识别响应 page_indices 透出")


if __name__ == "__main__":
    unittest.main()
