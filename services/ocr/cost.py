# -*- coding: utf-8 -*-
"""
services/ocr/cost.py · REFACTOR-WA-OCRSPLIT P-A(纯搬家 · 0 逻辑改)

从 pipeline.py 抽出成本核算:Gemini 定价常量 + _compute_total_cost(汇总每页估算成本 → THB)。
pipeline 文件头 re-export 回原命名空间 → 调用方 0 改动 · 对象身份不变。
"""

from __future__ import annotations

import os
from typing import List

from .schemas import PipelinePageResult

THB_PER_USD = float(os.environ.get("OCR_PIPELINE_THB_PER_USD", "35"))


COST_VISION_PER_PAGE_USD = 0.00150


COST_FLASHLITE_INPUT_PER_M_USD = 0.10


COST_FLASHLITE_OUTPUT_PER_M_USD = 0.40


COST_FLASH_INPUT_PER_M_USD = 0.30


COST_FLASH_OUTPUT_PER_M_USD = 2.50


def _compute_total_cost(page_results: List[PipelinePageResult]) -> float:
    """Sum estimated cost across pages, return THB.

    Notes:
        - Vision $0.00150/page applies only when Layer 1 Vision actually
          ran (layer_chain starts with "L1"). When text_path (Layer 0)
          hit and Vision was skipped, layer_chain starts with "text" and
          no Vision cost is added.
        - Flash-Lite cost = (input * 0.10 + output * 0.40) / 1M tokens, USD
        - Flash cost = (input * 0.30 + output * 2.50) / 1M tokens, USD
        - Then * THB_PER_USD (default 35)
    """
    total_usd = 0.0
    for pr in page_results:
        # Vision per-page — only when L1 actually ran (skipped for text_path)
        if "L1" in pr.layer_chain:
            total_usd += COST_VISION_PER_PAGE_USD
        # Flash-Lite (always runs)
        total_usd += (pr.layer2_input_tokens / 1_000_000.0) * COST_FLASHLITE_INPUT_PER_M_USD
        total_usd += (pr.layer2_output_tokens / 1_000_000.0) * COST_FLASHLITE_OUTPUT_PER_M_USD
        # Flash (only if L3 ran successfully — tokens > 0 means it ran)
        if pr.layer3_input_tokens or pr.layer3_output_tokens:
            total_usd += (pr.layer3_input_tokens / 1_000_000.0) * COST_FLASH_INPUT_PER_M_USD
            total_usd += (pr.layer3_output_tokens / 1_000_000.0) * COST_FLASH_OUTPUT_PER_M_USD
    return total_usd * THB_PER_USD
