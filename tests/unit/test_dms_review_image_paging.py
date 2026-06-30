# -*- coding: utf-8 -*-
"""回归守门:多票复核原图必须能看到每张票所在物理页,不能写死只取 page/1.png。

血泪:一份 3 票 PDF 跨 2 物理页,原图却恒取 page/1.png → 第三张(第 2 页)的图永远
看不到("三票只显示两图")。修法 = 查看器「按发票翻」+ 聚焦自动跟随:翻 / 聚焦哪张票,
据其 page_indices 渲染该张所在物理页。此测试钉住该机制(不写死页码、无人工按钮)。
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
        # 页码必须来自该张发票的 page_indices,不能写死
        self.assertIn("pageOfInvoice", src, "物理页应据发票 page_indices 推导")
        self.assertIn("pageIndices", src, "应读发票 page_indices")
        self.assertIn("pi[0]", src, "取该票首个物理页")

    def test_per_invoice_nav_and_autofollow(self):
        src = _REVIEW.read_text(encoding="utf-8")
        self.assertNotIn("dx-inv-viewpage", src, "不应有人工「看此张原图」按钮(改自动跟随)")
        self.assertIn("dx-page-next", src, "应有按发票翻页控件")
        self.assertIn("gotoInvoice", src, "翻页单位应为发票(gotoInvoice)")
        # 自动跟随:聚焦发票字段组 → 查看器切到该张
        self.assertIn("data-iv-show", src, "发票组应带 data-iv-show 供自动跟随定位")
        self.assertIn("focusin", src, "应监听 focusin 实现聚焦自动跟随")

    def test_page_indices_surfaced(self):
        src = _INVOICE.read_text(encoding="utf-8")
        self.assertIn("pageIndices", src, "IvInvoice 应带 pageIndices")
        self.assertIn("page_indices", src, "应从识别响应 page_indices 透出")


if __name__ == "__main__":
    unittest.main()
