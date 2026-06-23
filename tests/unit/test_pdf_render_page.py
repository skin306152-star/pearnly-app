# -*- coding: utf-8 -*-
"""复核原图查看器后端 · pdf_utils.render_page_png 渲染契约。

锁定:能把留底 PDF 的一页渲成 PNG 字节;坏路径/坏页号安全降级(None / 钳制)。
"""

import os
import tempfile
import unittest

from services.ocr.pdf_utils import render_page_png


def _make_pdf(path: str, pages: int = 2):
    import fitz

    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=200, height=120)
    doc.save(path)
    doc.close()


class RenderPagePngTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pdf = os.path.join(self.tmp, "doc.pdf")
        _make_pdf(self.pdf, pages=2)

    def test_renders_png_bytes_and_count(self):
        out = render_page_png(self.pdf, page=1)
        self.assertIsNotNone(out)
        png, total = out
        # PNG magic number + 返回总页数(多页 PDF 前端翻页用)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(total, 2)

    def test_page_out_of_range_clamps(self):
        # 第 99 页不存在 → 钳到末页,仍出图(不抛 / 不 None)· 总页数仍报真实值
        self.assertEqual(render_page_png(self.pdf, page=99)[1], 2)
        self.assertIsNotNone(render_page_png(self.pdf, page=0))

    def test_missing_file_returns_none(self):
        self.assertIsNone(render_page_png(os.path.join(self.tmp, "nope.pdf")))


if __name__ == "__main__":
    unittest.main()
