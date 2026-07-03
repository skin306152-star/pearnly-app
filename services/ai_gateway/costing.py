# -*- coding: utf-8 -*-
"""token → THB 成本估算(轻量·内部观测用·非计费)。

复用 services/ocr/cost.py 的按模型价表(per-million USD × THB_PER_USD),不另起一套价 ——
2.5 与 3.5 单价差 5x/3.6x,按实际 model 计价账本才对得上真账单。
"""

from __future__ import annotations


def estimate_thb(model: str, input_tokens, output_tokens) -> float:
    """token 估算成本(THB),按实际模型单价计。负/空 token 归零。"""
    from services.ocr import cost

    it = max(0, int(input_tokens or 0))
    ot = max(0, int(output_tokens or 0))
    in_usd, out_usd = cost.price_per_m_usd(model)
    usd = it / 1_000_000 * in_usd + ot / 1_000_000 * out_usd
    return round(usd * cost.THB_PER_USD, 6)
