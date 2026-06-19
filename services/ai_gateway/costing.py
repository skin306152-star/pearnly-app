# -*- coding: utf-8 -*-
"""token → THB 成本估算(轻量·内部观测用·非计费)。

复用 services/ocr/cost.py 的单价口径(per-million USD × THB_PER_USD),不另起一套价表 —— gateway 两个
task 都走 flash 档,与 OCR 成本口径一致(见 docs/line-platform/03 §6)。
"""

from __future__ import annotations


def estimate_thb(model: str, input_tokens, output_tokens) -> float:
    """token 估算成本(THB),复用 OCR flash 档单价。负/空 token 归零。"""
    from services.ocr import cost

    it = max(0, int(input_tokens or 0))
    ot = max(0, int(output_tokens or 0))
    usd = (
        it / 1_000_000 * cost.COST_FLASH_INPUT_PER_M_USD
        + ot / 1_000_000 * cost.COST_FLASH_OUTPUT_PER_M_USD
    )
    return round(usd * cost.THB_PER_USD, 6)
