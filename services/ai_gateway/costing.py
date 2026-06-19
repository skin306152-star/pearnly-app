# -*- coding: utf-8 -*-
"""token → THB 成本估算(轻量·内部观测用·非计费)。

P2E-1 先给统一档估算;后续可按 model 细分并与 ocr_cost_log 口径对齐(见 docs/line-platform/03 §6)。
"""

from __future__ import annotations

# 粗略单价(THB / 1k tokens)· 内部成本观测,不用于向用户计费。
_IN_PER_1K_THB = 0.012
_OUT_PER_1K_THB = 0.05


def estimate_thb(model: str, input_tokens, output_tokens) -> float:
    """token 估算成本(THB)。model 预留按档细分;当前统一档。负/空 token 归零。"""
    it = max(0, int(input_tokens or 0))
    ot = max(0, int(output_tokens or 0))
    return round(it / 1000 * _IN_PER_1K_THB + ot / 1000 * _OUT_PER_1K_THB, 6)
