#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocrperf_step3.py · REFACTOR-WA-OCRPERF Step3(图片压缩)

锁:
  A. downscale_image_bytes —— 大图按最长边 cap 缩(只缩不放·解码后 longest≤cap·字节更小)·
     小图/cap=0/空/坏字节 → 原样返回(绝不抛·压缩绝不破坏识别)。
  B. run_on_image_bytes 接线 —— Layer1 收【压缩版】(layer1_image_bytes_override),
     image_bytes 仍传【原图】(→ L3 视觉兜底用全分辨率原图)。PDF 路径不经此。

纯逻辑 · mock _process_one_page/_compute_total_cost · 无 Gemini/无网络。CI 必跑不 skip。
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import pipeline  # noqa: E402


def _noise_png(w, h):
    """内容丰富(随机噪声)的 PNG · 保证 resize 后字节确实更小。"""
    im = Image.frombytes("RGB", (w, h), os.urandom(w * h * 3))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


class DownscaleTest(unittest.TestCase):
    def test_large_image_resized_to_cap(self) -> None:
        big = _noise_png(2800, 1200)  # longest 2800 > 2400
        out = pipeline.downscale_image_bytes(big, 2400)
        self.assertLess(len(out), len(big), "应更小")
        w, h = Image.open(io.BytesIO(out)).size
        self.assertEqual(max(w, h), 2400, "最长边缩到 cap")
        self.assertEqual((w, h), (2400, 1029))  # 2800→2400, 1200*2400/2800≈1029

    def test_small_image_unchanged(self) -> None:
        small = _noise_png(1000, 800)  # longest 1000 <= 2400
        out = pipeline.downscale_image_bytes(small, 2400)
        self.assertIs(out, small, "小图原样返回(同一对象)")

    def test_cap_zero_disables(self) -> None:
        big = _noise_png(2800, 1200)
        self.assertIs(pipeline.downscale_image_bytes(big, 0), big)

    def test_empty_bytes_unchanged(self) -> None:
        self.assertEqual(pipeline.downscale_image_bytes(b"", 2400), b"")

    def test_garbage_bytes_never_raises(self) -> None:
        garbage = b"not an image at all \x00\x01\x02"
        self.assertEqual(pipeline.downscale_image_bytes(garbage, 2400), garbage)

    def test_preserves_jpeg_format(self) -> None:
        im = Image.frombytes("RGB", (3000, 1500), os.urandom(3000 * 1500 * 3))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=95)
        big = buf.getvalue()
        out = pipeline.downscale_image_bytes(big, 2400)
        self.assertEqual(Image.open(io.BytesIO(out)).format, "JPEG")
        self.assertEqual(max(Image.open(io.BytesIO(out)).size), 2400)


class RunOnImageWiringTest(unittest.TestCase):
    def test_layer1_gets_compressed_l3_source_gets_original(self) -> None:
        orig = _noise_png(2800, 1200)  # 会被压缩
        captured = {}

        def fake_pop(image_bytes, **kw):
            captured["image_bytes"] = image_bytes
            captured["override"] = kw.get("layer1_image_bytes_override")
            return SimpleNamespace()  # _compute_total_cost 被 mock·不读属性

        with patch.object(pipeline, "_process_one_page", side_effect=fake_pop):
            with patch.object(pipeline, "_compute_total_cost", return_value=0.0):
                with patch.object(pipeline, "PipelineResult", lambda **kw: SimpleNamespace(**kw)):
                    pipeline.run_on_image_bytes(orig, api_key="k")

        # image_bytes(→L3 用)= 原图;override(→L1 用)= 压缩版(更小·解码 longest≤2400)
        self.assertIs(captured["image_bytes"], orig, "L3 源必须是原图(同一对象)")
        self.assertIsNotNone(captured["override"])
        self.assertLess(len(captured["override"]), len(orig))
        self.assertEqual(max(Image.open(io.BytesIO(captured["override"])).size), 2400)

    def test_small_image_override_equals_original(self) -> None:
        small = _noise_png(1000, 800)  # 不压
        captured = {}

        def fake_pop(image_bytes, **kw):
            captured["image_bytes"] = image_bytes
            captured["override"] = kw.get("layer1_image_bytes_override")
            return SimpleNamespace()

        with patch.object(pipeline, "_process_one_page", side_effect=fake_pop):
            with patch.object(pipeline, "_compute_total_cost", return_value=0.0):
                with patch.object(pipeline, "PipelineResult", lambda **kw: SimpleNamespace(**kw)):
                    pipeline.run_on_image_bytes(small, api_key="k")
        # 小图:override 即原图(downscale 原样返回)
        self.assertIs(captured["override"], small)
        self.assertIs(captured["image_bytes"], small)


if __name__ == "__main__":
    unittest.main(verbosity=2)
