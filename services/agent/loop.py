# -*- coding: utf-8 -*-
"""单轮编排(M1-SOCKET-DESIGN §7)—— 一条消息进,一段回复出。

消息 → 大脑选动作 → 参数闸 → (B 档复述确认) → 执行 → 回执。任何一步卡住都反问/引导,
绝不带编造值执行。多轮 pending(记住缺什么、等确认)的持久化由 WP5 接 LINE 时接线;
M1 把分支跑通,依赖(大脑/工具集/历史)可注入以便单测。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Callable, Optional

from services.agent import brain, copy_map, executor, manifest, slots
from services.agent.contracts import AgentContext

logger = logging.getLogger(__name__)

_CONFIRM_WORDS = ("ยืนยัน", "确认", "確認", "ok", "yes", "ใช่")


def _today() -> str:
    return date.today().isoformat()


def _recent(ctx: AgentContext) -> list:
    """LINE 短期记忆(无 line_user_id/tenant 则空 · 不触 DB)。"""
    if not ctx.line_user_id or not ctx.tenant_id:
        return []
    from services.line_binding import line_chat_memory

    return line_chat_memory.recent(line_user_id=ctx.line_user_id, tenant_id=ctx.tenant_id)


def _user_confirmed(user_text: str) -> bool:
    low = (user_text or "").strip().lower()
    return any(w in low for w in _CONFIRM_WORDS)


def handle_turn(
    user_text: str,
    ctx: AgentContext,
    *,
    decide: Optional[Callable] = None,
    toolset: Optional[executor.AgentToolset] = None,
    history: Optional[list] = None,
    today: Optional[str] = None,
) -> str:
    decide = decide or brain.decide
    toolset = toolset or executor.AgentToolset()
    history = history if history is not None else _recent(ctx)
    today = today or _today()

    action = decide(user_text, history, today=today)

    if action.kind == "out_of_scope":
        return copy_map.out_of_scope(action.message)
    if action.kind == "chat":
        return copy_map.chat(action.message)
    if action.kind == "ask":
        return copy_map.ask(action.ask_field or "")

    spec = manifest.TOOLS_BY_NAME.get(action.tool)
    if not spec:  # 大脑选了不存在的工具 → 当超范围
        return copy_map.out_of_scope()

    chk = slots.check_slots(action, user_text=user_text, history=history, ctx=ctx)
    if not chk.ok:
        if chk.rejected:  # 审计:模型试图编值
            logger.warning("slot_fabricated tool=%s rejected=%s", action.tool, chk.rejected)
        return copy_map.ask(chk.missing[0])

    if spec.confirm and not _user_confirmed(user_text):  # B 档:先复述确认
        return copy_map.confirm(spec, chk.grounded)

    handler = getattr(toolset, spec.handler, None)
    if handler is None:  # manifest 登记了但 executor 没实现
        return copy_map.failure("unknown")
    result = handler(ctx, **chk.grounded)
    return result.receipt if result.ok else copy_map.failure(result.error_code)
