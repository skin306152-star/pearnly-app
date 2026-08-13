# -*- coding: utf-8 -*-
"""pdf_utils 契约:复核原图渲染(render_page_png)+ 成本归因页数(doc_page_count)。

锁定:能把留底 PDF 的一页渲成 PNG 字节;坏路径/坏页号安全降级(None / 钳制);
归因页数 PDF 按物理页、图片恒 1、表格类 None(按字符计费,页概念不成立)。
"""

import os
import tempfile
import unittest

from services.ocr.pdf_utils import doc_page_count, render_page_png


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


class DocPageCountTests(unittest.TestCase):
    def test_pdf_counts_physical_pages(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "doc.pdf")
            _make_pdf(path, pages=3)
            with open(path, "rb") as f:
                self.assertEqual(doc_page_count(f.read(), "doc.pdf"), 3)

    def test_corrupt_pdf_counts_one(self):
        # 损坏件读不出页数按 1 页:钱已经花了,分母记 0 会把这笔成本从每页成本里蒸发
        self.assertEqual(doc_page_count(b"not a pdf", "broken.pdf"), 1)

    def test_image_is_one_page(self):
        self.assertEqual(doc_page_count(b"\x89PNG", "photo.PNG"), 1)
        self.assertEqual(doc_page_count(b"\xff\xd8", "scan.jpg"), 1)

    def test_table_formats_have_no_page_concept(self):
        for fn in ("book.xlsx", "rows.csv", "doc.docx", "noext"):
            self.assertIsNone(doc_page_count(b"data", fn), fn)


if __name__ == "__main__":
    unittest.main()
