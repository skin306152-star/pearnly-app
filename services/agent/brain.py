# -*- coding: utf-8 -*-
"""大脑决策的共享 helper —— 后端选择 + 提示词工具表/历史块。

真正的决策循环在 loop.py(它拼提示词、调网关、解析动作)。这里只留三个被复用的纯函数:
后端覆盖(_brain_backend)、工具表渲染(_tool_table)、历史块渲染(_history_block)。
后端按 OCR_LLM_BACKEND 自动切(vertex/gemini),网关一行不改。

注:旧的一击式 decide()/build_prompt()/_parse_action()(kind=tool/ask/out_of_scope/chat)
是 M1 骨架,已被 loop.py 的真 agent 循环(kind=tool/reply/defer)取代并删除。
"""

from __future__ import annotations

import os
from typing import Optional

from services.agent import contracts


def _brain_backend() -> Optional[str]:
    """Agent 大脑的后端覆盖(env AGENT_BRAIN_BACKEND)。

    未设 → None → 跟随全局 OCR_LLM_BACKEND(现状 = Vertex Gemini,零变化)。设 selfhost +
    SELFHOST_* 端点就绪 → 只有 Agent 路由走便宜 qwen,OCR 不受影响。端点不可用时 provider
    收敛为错误 → loop 归 crash → defer 回旧路,不炸用户(fail-safe)。
    """
    return (os.environ.get("AGENT_BRAIN_BACKEND") or "").strip().lower() or None


def _tool_table(tools: tuple[contracts.ToolSpec, ...]) -> str:
    """从 manifest 自动生成工具表(名 + desc + slot 名)。加工具即改 manifest,提示词自动跟着变。"""
    lines = []
    for t in tools:
        slot_names = ", ".join(s.name for s in t.slots) or "ไม่มี"
        lines.append(f"- {t.name}: {t.desc_th} (พารามิเตอร์: {slot_names})")
    return "\n".join(lines)


def _history_block(history: Optional[list]) -> str:
    turns = [
        f'{h.get("role", "")}: {h.get("content", "")}'.strip()
        for h in (history or [])
        if (h.get("content") or "").strip()
    ]
    if not turns:
        return ""
    return "\n\nบทสนทนาล่าสุด (บริบทเท่านั้น จัดประเภทเฉพาะข้อความล่าสุดด้านล่าง):\n" + "\n".join(
        turns
    )
