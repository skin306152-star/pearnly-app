# -*- coding: utf-8 -*-
"""
services/ocr/cost.py

成本核算(内部观测账本,非用户计费——用户按页/字符扣积分,见 core.db 计费口径):
按模型分价的 Google 官方单价表 + _compute_total_cost(按当前 env 档位模型计价)。
pipeline 文件头 re-export 回原命名空间 → 调用方 0 改动。
"""

from __future__ import annotations

import os
from typing import List, Tuple

from .schemas import PipelinePageResult

THB_PER_USD = float(os.environ.get("OCR_PIPELINE_THB_PER_USD", "35"))


COST_VISION_PER_PAGE_USD = 0.00150

# Google 官方单价(USD / 百万 token · 2026-05 价表)。前缀匹配,lite 排在 2.5-flash 前防误吞;
# 换/加模型先补这行,内部账本才对得上真账单。3.5-flash 单价 ≈ 2.5 的 5x/3.6x——
# 换模型省不省钱要按这里重算,别拿 token 数当钱数(2026-07-03 血泪)。
MODEL_PRICES_PER_M_USD = {
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash": (0.30, 2.50),
}

# 旧常量名保留(pipeline re-export 契约):按历史档位口径取值的别名。
COST_FLASHLITE_INPUT_PER_M_USD, COST_FLASHLITE_OUTPUT_PER_M_USD = MODEL_PRICES_PER_M_USD[
    "gemini-2.5-flash-lite"
]
COST_FLASH_INPUT_PER_M_USD, COST_FLASH_OUTPUT_PER_M_USD = MODEL_PRICES_PER_M_USD["gemini-2.5-flash"]


def price_per_m_usd(model: str) -> Tuple[float, float]:
    """模型名 → (输入, 输出) USD/百万token。未知模型按 3.5-flash 计(观测宁高勿低)。"""
    name = (model or "").strip()
    for prefix, price in MODEL_PRICES_PER_M_USD.items():
        if name.startswith(prefix):
            return price
    return MODEL_PRICES_PER_M_USD["gemini-3.5-flash"]


def _compute_total_cost(page_results: List[PipelinePageResult]) -> float:
    """Sum estimated cost across pages, return THB.

    Notes:
        - Vision $0.00150/page applies only when Layer 1 Vision actually
          ran (layer_chain starts with "L1"). When text_path (Layer 0)
          hit and Vision was skipped, layer_chain starts with "text" and
          no Vision cost is added.
        - 逐页按【实际用过的模型】计价(PageResult.layer2_model/layer3_model,
          page_runner 调用时记录);页上没记(旧结果/直调层函数)才回落当前档位。
          OCR_MODE 混跑 2.5/3.5 时账本仍然对得上真账单。
        - Then * THB_PER_USD (default 35)
    """
    from services.ocr import gemini_models

    total_usd = 0.0
    for pr in page_results:
        # Vision per-page — only when L1 actually ran (skipped for text_path)
        if "L1" in pr.layer_chain:
            total_usd += COST_VISION_PER_PAGE_USD
        l2_model = getattr(pr, "layer2_model", "") or gemini_models.flash_lite()
        l2_in, l2_out = price_per_m_usd(l2_model)
        total_usd += (pr.layer2_input_tokens / 1_000_000.0) * l2_in
        total_usd += (pr.layer2_output_tokens / 1_000_000.0) * l2_out
        # L3 tokens > 0 means the escalation arm ran
        if pr.layer3_input_tokens or pr.layer3_output_tokens:
            l3_model = (
                getattr(pr, "layer3_model", "") or gemini_models.escalate() or gemini_models.flash()
            )
            l3_in, l3_out = price_per_m_usd(l3_model)
            total_usd += (pr.layer3_input_tokens / 1_000_000.0) * l3_in
            total_usd += (pr.layer3_output_tokens / 1_000_000.0) * l3_out
    return total_usd * THB_PER_USD
