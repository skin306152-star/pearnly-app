#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_cost_contract.py · REFACTOR-WA-OCRSPLIT P-A

锁 P-A 纯搬家(成本核算 pipeline → cost)0 逻辑改:
  1. pipeline re-export 的成本常量 + _compute_total_cost 与 cost 是【同一对象】(assertIs)。
  2. cost 是 leaf(不 import pipeline)。
  3. _compute_total_cost 计算口径不变(功能锁:Vision 仅 L1 计 / Flash-Lite 恒计 / Flash 仅 L3 计 / ×THB_PER_USD)。

纯逻辑 · 无 DB/genai。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import pipeline as p  # noqa: E402
from services.ocr import cost as c  # noqa: E402

_NAMES = (
    "THB_PER_USD",
    "COST_VISION_PER_PAGE_USD",
    "COST_FLASHLITE_INPUT_PER_M_USD",
    "COST_FLASHLITE_OUTPUT_PER_M_USD",
    "COST_FLASH_INPUT_PER_M_USD",
    "COST_FLASH_OUTPUT_PER_M_USD",
    "_compute_total_cost",
)


def _page(chain, l2i=0, l2o=0, l3i=0, l3o=0):
    return SimpleNamespace(
        layer_chain=chain,
        layer2_input_tokens=l2i,
        layer2_output_tokens=l2o,
        layer3_input_tokens=l3i,
        layer3_output_tokens=l3o,
    )


class CostContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        for n in _NAMES:
            self.assertIs(getattr(p, n), getattr(c, n), f"{n} re-export 漂移")

    def test_cost_module_is_leaf(self) -> None:
        self.assertIsNone(getattr(c, "pipeline", None))

    def test_compute_math_unchanged(self) -> None:
        # L1+L2 页:1M in + 1M out flash-lite → (vision 0.0015 + 0.10 + 0.40)*35
        cost = c._compute_total_cost([_page(["L1", "L2"], l2i=1_000_000, l2o=1_000_000)])
        self.assertAlmostEqual(cost, (0.00150 + 0.10 + 0.40) * 35.0, places=4)

    def test_text_path_skips_vision_cost(self) -> None:
        # text_path(chain 起 "text")不计 Vision per-page
        cost = c._compute_total_cost([_page(["text", "L2"], l2i=1_000_000, l2o=0)])
        self.assertAlmostEqual(cost, (0.10) * 35.0, places=4)

    def test_l3_cost_only_when_l3_ran(self) -> None:
        no_l3 = c._compute_total_cost([_page(["L1", "L2"], l2i=0, l2o=0)])
        with_l3 = c._compute_total_cost(
            [_page(["L1", "L2", "L3"], l2i=0, l2o=0, l3i=1_000_000, l3o=1_000_000)]
        )
        self.assertAlmostEqual(no_l3, 0.00150 * 35.0, places=4)  # 仅 vision
        self.assertAlmostEqual(with_l3, (0.00150 + 0.30 + 2.50) * 35.0, places=4)

    def test_empty_pages_zero(self) -> None:
        self.assertEqual(c._compute_total_cost([]), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
