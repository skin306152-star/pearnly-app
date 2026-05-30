#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_layer2_gemini_contract.py · REFACTOR-WA-OCRSPLIT L2-A

锁定 L2-A 纯搬家(Gemini 传输 helper layer2_structure → layer2_gemini)0 逻辑改:
  1. layer2_structure re-export 的名与 layer2_gemini 是【同一对象】(assertIs·调用方 0 改动)。
  2. layer2_gemini 是 leaf(不 import layer2_structure → 无循环)。
  3. _call_gemini_with_retry(prompt-coupled)仍留 layer2_structure(L2-A 不动它)。

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
    "_get_model",
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

    def test_call_gemini_with_retry_stays_in_structure(self) -> None:
        # prompt-coupled · L2-A 不动它(留 layer2_structure)
        self.assertTrue(callable(getattr(l2, "_call_gemini_with_retry", None)))
        self.assertIsNone(getattr(g, "_call_gemini_with_retry", None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
