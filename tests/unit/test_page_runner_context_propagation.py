# -*- coding: utf-8 -*-
"""反馈闭环 ② · 多页 PDF 页工作线程继承 OCR 请求级上下文(防回归)。

page_runner 并发分支用 copy_context 把当前 contextvar 复制进 worker 线程,否则多页 PDF
的 few-shot 注入会漏掉。"""

import unittest
from unittest import mock

from services.ocr import page_runner
from services.ocr.feedback import context


class PageRunnerContextPropagationTests(unittest.TestCase):
    def test_parallel_workers_see_context(self):
        seen = []

        def _fake_one_page(image_bytes, page_number, **kw):
            seen.append((page_number, context.current()))
            return f"page{page_number}"

        with (
            mock.patch.object(page_runner, "_process_one_page", _fake_one_page),
            mock.patch.object(page_runner, "OCR_PDF_PAGE_WORKERS", 4),
        ):
            with context.ocr_request_context("u1", "t1"):
                out = page_runner._process_pages(
                    [b"a", b"b", b"c"],
                    None,
                    api_key=None,
                    enable_layer3=False,
                    fallback_to_layer2_on_layer3_error=True,
                    pattern_memory=None,
                    document_type="auto",
                )
        # 页序还原正确
        self.assertEqual(out, ["page1", "page2", "page3"])
        # 每个 worker 线程都读到了请求级上下文
        self.assertEqual(len(seen), 3)
        for _pno, ctx in seen:
            self.assertEqual(ctx, {"user_id": "u1", "tenant_id": "t1"})


if __name__ == "__main__":
    unittest.main()
