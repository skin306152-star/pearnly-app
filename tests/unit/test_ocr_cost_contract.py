#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_cost_contract.py · REFACTOR-WA-OCRSPLIT P-A

锁成本核算契约:
  1. pipeline re-export 的成本常量 + _compute_total_cost 与 cost 是【同一对象】(assertIs)。
  2. cost 不 import pipeline(无环)。
  3. 计算口径:Vision 仅 L1 计 / L2 恒计 / L3 仅升级臂跑过才计 / ×THB_PER_USD;
     2026-07-03 起 L2/L3 按当前 env 档位模型的官方单价计(price_per_m_usd 按模型分价)。

纯逻辑 · 无 DB/genai。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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


# 三档互异的梯子:让 L2(lite 档)与 L3(escalate=fallback 档)可分别验价
_LADDER = {
    "OCR_FLASH_MODEL": "gemini-2.5-flash",
    "OCR_FLASHLITE_MODEL": "gemini-2.5-flash-lite",
    "OCR_FALLBACK_MODEL": "gemini-3.5-flash",
    "OCR_ESCALATE_MODEL": "",
}


class CostContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        for n in _NAMES:
            self.assertIs(getattr(p, n), getattr(c, n), f"{n} re-export 漂移")

    def test_cost_module_is_leaf(self) -> None:
        self.assertIsNone(getattr(c, "pipeline", None))

    def test_price_per_m_usd_by_model(self) -> None:
        self.assertEqual(c.price_per_m_usd("gemini-3.5-flash"), (1.50, 9.00))
        self.assertEqual(c.price_per_m_usd("gemini-2.5-flash"), (0.30, 2.50))
        self.assertEqual(c.price_per_m_usd("gemini-2.5-flash-lite"), (0.10, 0.40))
        # 3.6 试过又退回,价留在表里:历史行/日后重试都算得对
        self.assertEqual(c.price_per_m_usd("gemini-3.5-flash"), (1.50, 9.00))
        # 未知模型按主力高精档计(观测宁高勿低)
        self.assertEqual(c.price_per_m_usd("mystery-model"), (1.50, 9.00))

    def test_compute_prices_l2_by_flashlite_tier(self) -> None:
        # L1+L2 页:1M in + 1M out · lite 档=2.5-flash-lite → (vision 0.0015 + 0.10 + 0.40)*35
        with mock.patch.dict("os.environ", _LADDER):
            cost = c._compute_total_cost([_page(["L1", "L2"], l2i=1_000_000, l2o=1_000_000)])
        self.assertAlmostEqual(cost, (0.00150 + 0.10 + 0.40) * 35.0, places=4)

    def test_text_path_skips_vision_cost(self) -> None:
        # text_path(chain 起 "text")不计 Vision per-page
        with mock.patch.dict("os.environ", _LADDER):
            cost = c._compute_total_cost([_page(["text", "L2"], l2i=1_000_000, l2o=0)])
        self.assertAlmostEqual(cost, (0.10) * 35.0, places=4)

    def test_l3_cost_only_when_l3_ran_and_priced_by_escalate_tier(self) -> None:
        with mock.patch.dict("os.environ", _LADDER):
            no_l3 = c._compute_total_cost([_page(["L1", "L2"], l2i=0, l2o=0)])
            with_l3 = c._compute_total_cost(
                [_page(["L1", "L2", "L3"], l2i=0, l2o=0, l3i=1_000_000, l3o=1_000_000)]
            )
        self.assertAlmostEqual(no_l3, 0.00150 * 35.0, places=4)  # 仅 vision
        # L3 按升级档(3.5-flash)单价计
        self.assertAlmostEqual(with_l3, (0.00150 + 1.50 + 9.00) * 35.0, places=4)

    def test_default_env_all_35(self) -> None:
        # 默认档(全 3.5)下 L2 也按 3.5 单价计——账本跟着档位走
        cleared = {k: "" for k in _LADDER}
        with mock.patch.dict("os.environ", cleared):
            cost = c._compute_total_cost([_page(["text", "L2"], l2i=1_000_000, l2o=1_000_000)])
        self.assertAlmostEqual(cost, (1.50 + 9.00) * 35.0, places=4)

    def test_empty_pages_zero(self) -> None:
        self.assertEqual(c._compute_total_cost([]), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
