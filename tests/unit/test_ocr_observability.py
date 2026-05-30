#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_observability.py · REFACTOR-WA-OCRPERF Step0

域:services/ocr/observability.py(per-page 计时观测 · 纯观测 0 逻辑改)

锁:format_pipeline_timing 从 PipelineResult.pages 抽每页计时字段(page/chain/triggers/
l1_l2_l3_ms/total_ms/tokens/l3 bool)· 且【绝不抛】(观测崩了绝不能影响识别热路径)——
None / 缺属性 / pages 非可迭代 全部安全返回。log_pipeline_timing 同样不抛。

纯逻辑 · 无 DB / 无 genai · 用 SimpleNamespace 造假 PipelinePageResult。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import observability as obs  # noqa: E402


def _page(**kw):
    base = dict(
        page_number=1,
        layer_chain=["L1", "L2"],
        trigger_reasons=[],
        layer1_ms=10,
        layer2_ms=20,
        layer3_ms=0,
        total_ms=30,
        layer2_input_tokens=100,
        layer2_output_tokens=50,
        layer3_input_tokens=0,
        layer3_output_tokens=0,
    )
    base.update(kw)
    return SimpleNamespace(**base)


class FormatTimingTest(unittest.TestCase):
    def test_basic_l2_only_page(self) -> None:
        res = SimpleNamespace(pages=[_page()])
        rows = obs.format_pipeline_timing(res)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["page"], 1)
        self.assertEqual(r["chain"], ["L1", "L2"])
        self.assertEqual(r["l1_ms"], 10)
        self.assertEqual(r["l2_ms"], 20)
        self.assertEqual(r["total_ms"], 30)
        self.assertEqual(r["l2_in"], 100)
        self.assertFalse(r["l3"])  # chain 无 L3

    def test_l3_detected_from_chain(self) -> None:
        res = SimpleNamespace(pages=[_page(layer_chain=["L1", "L2", "L3"], layer3_ms=500)])
        r = obs.format_pipeline_timing(res)[0]
        self.assertTrue(r["l3"])
        self.assertEqual(r["l3_ms"], 500)

    def test_l3_variants_count_as_l3(self) -> None:
        # L3_failed / L3_quota / L3_transient 也算走过 L3(链里出现 L3*)
        for variant in ("L3_failed", "L3_quota", "L3_transient"):
            res = SimpleNamespace(pages=[_page(layer_chain=["L1", "L2", variant])])
            self.assertTrue(obs.format_pipeline_timing(res)[0]["l3"], msg=variant)

    def test_text_path_chain_no_l3(self) -> None:
        res = SimpleNamespace(pages=[_page(layer_chain=["text", "L2"])])
        self.assertFalse(obs.format_pipeline_timing(res)[0]["l3"])

    def test_multiple_pages_preserved(self) -> None:
        res = SimpleNamespace(pages=[_page(page_number=1), _page(page_number=2)])
        rows = obs.format_pipeline_timing(res)
        self.assertEqual([r["page"] for r in rows], [1, 2])

    # ── 绝不抛(观测不影响识别)─────────────────────────────
    def test_none_pages_returns_empty(self) -> None:
        self.assertEqual(obs.format_pipeline_timing(SimpleNamespace(pages=None)), [])

    def test_no_pages_attr_returns_empty(self) -> None:
        self.assertEqual(obs.format_pipeline_timing(SimpleNamespace()), [])
        self.assertEqual(obs.format_pipeline_timing(None), [])

    def test_page_missing_attrs_does_not_raise(self) -> None:
        # 缺属性的页 → getattr 默认 None · 不抛
        rows = obs.format_pipeline_timing(SimpleNamespace(pages=[SimpleNamespace()]))
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["page"])
        self.assertEqual(rows[0]["chain"], [])
        self.assertFalse(rows[0]["l3"])


class LogTimingTest(unittest.TestCase):
    def test_log_never_raises(self) -> None:
        # 正常 + 垃圾输入都不抛
        obs.log_pipeline_timing(SimpleNamespace(pages=[_page()]), source="recognize", filename="x")
        obs.log_pipeline_timing(None)
        obs.log_pipeline_timing(SimpleNamespace(pages="not-iterable-but-str"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
