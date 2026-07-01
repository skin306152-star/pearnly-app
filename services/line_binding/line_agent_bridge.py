# -*- coding: utf-8 -*-
"""对话 Agent 插座 ↔ LINE 入口的桥(WP5)。

line_expense.handle_expense_text 为灰度用户在关键词分支「之前」调 try_agent_turn(前门倒置):
模型自己判意图——查询/闲聊自己组织人话回复(接管本轮),记账/改错/超范围 → 返 None(defer),
调用方逐字节落回旧 understand()+_dispatch_agent()。能力只增不减,旧路一行不改。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 记账待确认 pending 前缀(存 line_pending_entry.missing)· 与改错的 correct* 前缀并列不冲突。
AGENTREC = "agentrec:"


def frontdoor_enabled(bound_user) -> bool:
    """本用户是否走「前门倒置」(灰度钥匙闸)。关 → 老确定性路一行不变。"""
    from core import feature_flags

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    return feature_flags.agent_enabled_for(uid)


def write_enabled(bound_user) -> bool:
    """本用户是否启用写工具(记账等 B 档)· 默认关 → 记账走旧乐观路,现状不变。"""
    from core import feature_flags

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    return feature_flags.agent_write_enabled_for(uid)


def _persist_record_pending(ctx, data) -> None:
    """把待确认的记账草稿落进 line_pending_entry(下轮用户"是"由入口 pop → 落库)。"""
    from core import db
    from services.expense import conversation

    with db.get_cursor_rls(
        tenant_id=str(ctx.tenant_id), user_id=str(ctx.user["id"]), commit=True
    ) as cur:
        conversation.save_pending(
            cur,
            line_user_id=ctx.line_user_id,
            tenant_id=str(ctx.tenant_id),
            workspace_client_id=ctx.workspace_client_id,
            draft=data["draft"],
            missing=AGENTREC,
        )


def try_agent_turn(bound_user, text, lang, tid, ws, line_user_id, history) -> Optional[str]:
    """钥匙闸 + agent 循环。命中并接管 → 模型撰写的自然语言回复;否则 None(交旧路)。

    lang 保留兼容:回复语言由模型按用户最新消息自适应,不再套模板。
    """
    from core import feature_flags

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    if not feature_flags.agent_enabled_for(uid):
        return None
    try:
        from services.agent import loop
        from services.agent.contracts import AgentContext

        ctx = AgentContext(
            user=bound_user,
            tenant_id=tid,
            workspace_client_id=ws,
            line_user_id=line_user_id,
        )
        return loop.handle_turn(
            text,
            ctx,
            history=history,
            allow_write=feature_flags.agent_write_enabled_for(uid),
            confirm_persist=_persist_record_pending,
        )
    except Exception:
        # 任何异常一律 defer(铁律:Agent 不许把错误抛给用户);带 uid + 栈便于排障。
        logger.warning("[line agent] turn failed; defer to legacy (uid=%s)", uid, exc_info=True)
        return None
