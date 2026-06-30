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
) -> Optional[str]:
    """一轮对话。返回 copy_map 占位串 = Agent 接管本轮;返回 None = defer。

    ★ 能力只增不减(MASTER-PLAN 铁律):Agent 只接管**有工具且能完成**的意图,其余一律 defer
    (None)→ 调用方落回旧 understand()+_dispatch_agent() 照常完成(撤销/改错/记账都在旧路)。
    只有新旧 LINE 都不做的(改密码/POS),才由旧路引导去 App。
    """
    decide = decide or brain.decide
    toolset = toolset or executor.AgentToolset()
    history = history if history is not None else _recent(ctx)
    today = today or _today()

    action = decide(user_text, history, today=today)

    # 无工具的意图(超范围/闲聊)→ 让旧路处理,不降级。
    if action.kind in ("out_of_scope", "chat"):
        return None
    if action.kind == "ask":  # 大脑主动反问 → Agent 接管(守槽纪律)
        return copy_map.ask(action.ask_field or "")

    spec = manifest.TOOLS_BY_NAME.get(action.tool)
    if not spec:  # 大脑选了不存在的工具 → defer 给旧路
        return None

    chk = slots.check_slots(action, user_text=user_text, history=history, ctx=ctx)
    if not chk.ok:
        if chk.rejected:  # 审计:模型试图编值
            logger.warning("slot_fabricated tool=%s rejected=%s", action.tool, chk.rejected)
        return copy_map.ask(chk.missing[0])  # 必填槽没接地 → 反问(绝不带编造值执行)

    if spec.confirm and not _user_confirmed(user_text):  # B 档:先复述确认
        return copy_map.confirm(spec, chk.grounded)

    handler = getattr(toolset, spec.handler, None)
    if handler is None:  # manifest 登记了但 executor 没实现 → defer
        return None
    result = handler(ctx, **chk.grounded)
    # 工具失败也 defer:旧路可能仍能完成,绝不因新路出错降级用户已有能力。
    return result.receipt if result.ok else None
