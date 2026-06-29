# -*- coding: utf-8 -*-
"""消费侧:把按主体的历史修正例拼成 few-shot 提示块,回喂 L2。

藏在 OCR_FEWSHOT_ENABLED 后,默认关。它会改变 L2 抽取结果(钱路),开启前须先攒到真实修正
数据 + 跑独立 eval;目前捕获侧持续沉淀例库,本函数只在显式开关下生效。"""

import os

_MAX_EXAMPLES = 12


def is_enabled() -> bool:
    return os.environ.get("OCR_FEWSHOT_ENABLED", "0").lower() in ("1", "true", "yes")


def build_prompt_block(examples: list) -> str:
    """examples = store.fetch_examples 输出。空 → 空串(不污染原 prompt)。"""
    if not examples:
        return ""
    lines = [
        "已知该商户历史人工修正(同字段优先按修正后口径输出,除非本张确实不同):",
    ]
    for e in examples[:_MAX_EXAMPLES]:
        ai_v = e.get("ai_value") or "(空)"
        fixed = e.get("corrected_value") or ""
        lines.append(f"- {e.get('field_name')}: AI 曾输出「{ai_v}」→ 正确「{fixed}」")
    return "\n".join(lines) + "\n\n"
