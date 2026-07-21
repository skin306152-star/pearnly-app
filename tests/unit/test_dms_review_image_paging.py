# -*- coding: utf-8 -*-
"""回归守门:录入工作台复核原图必须能看到每一页,且复用共享查看器(不再各写一套)。

血泪:一份 3 票 PDF 跨 2 物理页,录入工作台曾自写一套 .dx- 查看器、写死 page/1.png →
第 3 张(第 2 页)永远看不到("三票两图")。修法 = 复用共享 image-viewer.ts(按物理页翻
‹1/N›),一处修复三处生效。M2 步③换成复核台 console 后,逐张遮罩(erp-review-verify.ts)
仍复用共享查看器,步③控制器(dms-intake-review-console.ts)经 mountImageViewer 挂载。
此测试钉死复用,防再各写一套。
"""

import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src" / "home"
# M2:步③复核台 console(替代旧手风琴)+ 逐张遮罩复用共享查看器
_CONSOLE = _SRC / "dms-intake-review-console.ts"
_VERIFY = _SRC / "erp-review-verify.ts"
_INVOICE = _SRC / "dms-intake-invoice.ts"
# 缺口④ 接线后识别机制(含响应→IvResult 映射 ingestResult)抽到此模块
_RECOGNIZE = _SRC / "dms-intake-invoice-recognize.ts"
_VIEWER = _SRC / "image-viewer.ts"


class ImagePagingRegressionTests(unittest.TestCase):
    def test_review_reuses_shared_viewer(self):
        # 步③复用共享查看器,不再自写 → 多页翻页一处修复三处生效。
        console = _CONSOLE.read_text(encoding="utf-8")
        verify = _VERIFY.read_text(encoding="utf-8")
        both = console + verify
        self.assertIn("image-viewer", both, "应 import 共享查看器 image-viewer.ts")
        self.assertIn("mountImageViewer", console, "步③应挂载共享查看器")
        self.assertIn("imageViewerHtml", verify, "遮罩应用共享查看器 HTML")
        # 不应再有自写查看器残留(各写一套正是反复回归的根因)
        for dead in ("dx-rimg", "dx-viewport", "loadImage", "gotoInvoice"):
            self.assertNotIn(dead, both, f"自写查看器残留:{dead}")

    def test_shared_viewer_is_page_parameterized(self):
        # 多页翻页引擎在共享件:按 page 取图 + X-Page-Count 决定翻页,绝不写死第 1 页。
        src = _VIEWER.read_text(encoding="utf-8")
        self.assertNotIn("/page/1.png", src, "不应写死 page/1.png")
        self.assertRegex(src, r"/page/\$\{[^}]+\}\.png", "原图 fetch 应按 page 参数化")
        self.assertIn("X-Page-Count", src, "应读 X-Page-Count 决定能否翻页")

    def test_page_indices_surfaced(self):
        # IvInvoice 接口字段仍在主模块;响应 page_indices 透出随 ingestResult 抽到 recognize 模块
        self.assertIn(
            "pageIndices", _INVOICE.read_text(encoding="utf-8"), "IvInvoice 应带 pageIndices"
        )
        self.assertIn(
            "page_indices", _RECOGNIZE.read_text(encoding="utf-8"), "应从识别响应 page_indices 透出"
        )


if __name__ == "__main__":
    unittest.main()
