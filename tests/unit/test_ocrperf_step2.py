#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocrperf_step2.py · REFACTOR-WA-OCRPERF Step2(多页 PDF 页面并行)

锁 services/ocr/pipeline._process_pages 的【调度等价 + 守卫】(单页 _process_one_page 一字不改):
  - 并行(pattern_memory is None · 多页)输出与串行【逐项一致 + 页序一致】(完成顺序乱也按
    page_number 还原)· 且返回的就是 _process_one_page 原对象(身份不变)。
  - 真的并发了(max 并发 > 1)· 而 pattern_memory 不为 None → 串行(并发==1·守卫)· 单页 → 串行。
  - layer1_pages_override 按 i-1 正确分发 · 其余 kwargs 透传。

纯逻辑 · mock _process_one_page(不调 Gemini/不渲染 PDF)· CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import pipeline  # noqa: E402

_KW = dict(
    api_key="k",
    enable_layer3=True,
    fallback_to_layer2_on_layer3_error=True,
    document_type="auto",
)


class _Tracker:
    """记录并发峰值 + 每页 kwargs · 用反向 sleep 让完成顺序与页序相反。"""

    def __init__(self, n):
        self.cur = 0
        self.max = 0
        self.lock = threading.Lock()
        self.n = n
        self.captured = {}

    def fake(self, image_bytes, *, page_number, **kw):
        with self.lock:
            self.cur += 1
            self.max = max(self.max, self.cur)
            self.captured[page_number] = {"image": image_bytes, **kw}
        # 反向 sleep:page 1 睡最久 → page n 先完成 → 检验结果仍按页序还原
        time.sleep(0.02 * (self.n - page_number + 1))
        with self.lock:
            self.cur -= 1
        return SimpleNamespace(page_number=page_number, tag=f"p{page_number}")


def _call(images, overrides, pattern_memory):
    return pipeline._process_pages(images, overrides, pattern_memory=pattern_memory, **_KW)


class ProcessPagesTest(unittest.TestCase):
    def test_parallel_preserves_page_order_despite_completion_order(self) -> None:
        imgs = [b"a", b"b", b"c", b"d"]
        tr = _Tracker(len(imgs))
        with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
            res = _call(imgs, None, None)  # pattern_memory None → 并行
        self.assertEqual([r.page_number for r in res], [1, 2, 3, 4])
        self.assertEqual([r.tag for r in res], ["p1", "p2", "p3", "p4"])
        self.assertGreater(tr.max, 1, "并行分支应真的并发(max>1)")

    def test_parallel_equals_serial_output(self) -> None:
        imgs = [b"a", b"b", b"c"]

        def det(image_bytes, *, page_number, **kw):
            return SimpleNamespace(page_number=page_number, tag=f"p{page_number}")

        with patch.object(pipeline, "_process_one_page", side_effect=det):
            par = _call(imgs, None, None)  # 并行
            ser = _call(imgs, None, object())  # pattern_memory 非 None → 串行
        self.assertEqual(
            [(r.page_number, r.tag) for r in par], [(r.page_number, r.tag) for r in ser]
        )

    def test_pattern_memory_forces_serial(self) -> None:
        imgs = [b"a", b"b", b"c", b"d"]
        tr = _Tracker(len(imgs))
        with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
            res = _call(imgs, None, object())  # 非 None → 串行守卫
        self.assertEqual([r.page_number for r in res], [1, 2, 3, 4])
        self.assertEqual(tr.max, 1, "pattern_memory 不为 None 必须串行(并发==1)")

    def test_single_page_serial(self) -> None:
        tr = _Tracker(1)
        with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
            res = _call([b"only"], None, None)
        self.assertEqual([r.page_number for r in res], [1])
        self.assertEqual(tr.max, 1)

    def test_workers_one_forces_serial(self) -> None:
        imgs = [b"a", b"b", b"c"]
        tr = _Tracker(len(imgs))
        with patch.object(pipeline, "OCR_PDF_PAGE_WORKERS", 1):
            with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
                res = _call(imgs, None, None)
        self.assertEqual([r.page_number for r in res], [1, 2, 3])
        self.assertEqual(tr.max, 1, "OCR_PDF_PAGE_WORKERS=1 应退回串行")

    def test_layer1_overrides_dispatched_by_index(self) -> None:
        imgs = [b"a", b"b", b"c"]
        overrides = ["ov1", "ov2", "ov3"]
        tr = _Tracker(len(imgs))
        with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
            _call(imgs, overrides, None)
        # page i 收到 overrides[i-1]
        self.assertEqual(tr.captured[1]["layer1_page_override"], "ov1")
        self.assertEqual(tr.captured[2]["layer1_page_override"], "ov2")
        self.assertEqual(tr.captured[3]["layer1_page_override"], "ov3")

    def test_none_overrides_passes_none(self) -> None:
        imgs = [b"a", b"b"]
        tr = _Tracker(len(imgs))
        with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
            _call(imgs, None, None)
        self.assertIsNone(tr.captured[1]["layer1_page_override"])
        self.assertIsNone(tr.captured[2]["layer1_page_override"])

    def test_kwargs_passthrough(self) -> None:
        imgs = [b"a", b"b"]
        tr = _Tracker(len(imgs))
        with patch.object(pipeline, "_process_one_page", side_effect=tr.fake):
            _call(imgs, None, None)
        c = tr.captured[1]
        self.assertEqual(c["api_key"], "k")
        self.assertTrue(c["enable_layer3"])
        self.assertTrue(c["fallback_to_layer2_on_layer3_error"])
        self.assertEqual(c["document_type"], "auto")
        self.assertIsNone(c["pattern_memory"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
