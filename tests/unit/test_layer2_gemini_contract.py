#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_layer2_gemini_contract.py · REFACTOR-WA-OCRSPLIT L2-A

锁定 L2-A/L2-B 纯搬家(Gemini 传输 helper layer2_structure → layer2_gemini)0 逻辑改:
  1. layer2_structure re-export 的名与 layer2_gemini 是【同一对象】(assertIs·调用方 0 改动)。
  2. layer2_gemini 是 leaf(只 import layer2_prompts 叶子·不 import layer2_structure → 无循环)。
  3. L2-B:_call_gemini_with_retry 已并入 layer2_gemini(prompt 常量改从 layer2_prompts 引)·
     layer2_structure / id_card_extract re-export 同一对象(调用方 0 改动)。

纯 import 契约 · 无 DB/genai。CI 必跑不 skip。行为由 COV4 test_ocr_gemini_helpers 经 facade 覆盖。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import layer2_structure as l2  # noqa: E402
from services.ocr import layer2_gemini as g  # noqa: E402

_REEXPORTED = (
    "Layer2Error",
    "Layer2AuthError",
    "Layer2QuotaError",
    "Layer2TransientError",
    "_parse_json",
    "_classify_gemini_exception",
    "_call_gemini_with_retry",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_OUTPUT_TOKENS",
)


class Layer2GeminiContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        for name in _REEXPORTED:
            self.assertIs(getattr(l2, name), getattr(g, name), f"{name} re-export 漂移(非同一对象)")

    def test_exception_hierarchy_preserved(self) -> None:
        self.assertTrue(issubclass(g.Layer2AuthError, g.Layer2Error))
        self.assertTrue(issubclass(g.Layer2QuotaError, g.Layer2Error))
        self.assertTrue(issubclass(g.Layer2TransientError, g.Layer2Error))

    def test_gemini_module_is_leaf(self) -> None:
        # 不 back-import layer2_structure → 无循环
        self.assertIsNone(getattr(g, "layer2_structure", None))

    def test_call_gemini_with_retry_moved_to_gemini(self) -> None:
        # L2-B:函数已并入 layer2_gemini · layer2_structure re-export 同一对象
        self.assertTrue(callable(getattr(g, "_call_gemini_with_retry", None)))
        self.assertIs(l2._call_gemini_with_retry, g._call_gemini_with_retry)

    def test_call_gemini_uses_prompts_from_leaf(self) -> None:
        # _call_gemini_with_retry 默认 prompt 来自 layer2_prompts 叶子(同一对象)
        from services.ocr import layer2_prompts as p

        self.assertIs(g._SYSTEM_PROMPT, p._SYSTEM_PROMPT)
        self.assertIs(g._USER_PROMPT_PREFIX, p._USER_PROMPT_PREFIX)
        self.assertIs(g._RETRY_TRIM_HINT, p._RETRY_TRIM_HINT)

    def test_parse_json_extracts_object_from_surrounding_prose(self) -> None:
        # 批二·容错:模型偶尔在 JSON 前后夹散文 → 抠出首个完整 {...}(严格路先行·干净 JSON 零影响)。
        self.assertEqual(g._parse_json('Here is the result: {"a": 1} thanks'), {"a": 1})
        self.assertEqual(g._parse_json('x {"a": {"b": 2}} y'), {"a": {"b": 2}})
        self.assertEqual(g._parse_json('p {"a": "has } brace"} q'), {"a": "has } brace"})

    def test_parse_json_no_object_still_raises(self) -> None:
        import json

        with self.assertRaises(json.JSONDecodeError):
            g._parse_json("not json at all")


if __name__ == "__main__":
    unittest.main(verbosity=2)
