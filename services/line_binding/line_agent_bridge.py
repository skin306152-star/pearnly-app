# -*- coding: utf-8 -*-
"""对话 Agent 插座 ↔ LINE 入口的桥(WP5)。

line_expense.handle_expense_text 为灰度用户在关键词分支「之前」调 try_agent_turn(前门倒置):
模型自己判意图——查询/闲聊自己组织人话回复(接管本轮),记账/改错/超范围 → 返 None(defer),
调用方逐字节落回旧 understand()+_dispatch_agent()。能力只增不减,旧路一行不改。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.agent.loop import RECORD_CARD_SENT  # 再导出:入口见此哨兵=记账已出卡,不再发文字

logger = logging.getLogger(__name__)

__all__ = ["RECORD_CARD_SENT", "frontdoor_enabled", "write_enabled", "try_agent_turn"]


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


def _record_sink(bound_user, text, lang, tid, ws, line_user_id, reply_token, quote_token, book):
    """记账出卡回调:模型抽的草稿 + 暖话 say → 现有 book(=line_expense._do_record·used_l2=False
    高置信直录·ack_text=say 让暖话显示在数据卡上方)。写关/缺件 → None(记账 defer 回旧乐观路)。"""
    if not (book and reply_token and write_enabled(bound_user)):
        return None
    return lambda _ctx, draft, say="": book(
        bound_user,
        reply_token,
        draft.raw_text or text,
        tid,
        ws,
        draft,
        False,
        quote_token,
        lang,
        line_user_id,
        ack_text=say,
    )


def try_agent_turn(
    bound_user,
    text,
    lang,
    tid,
    ws,
    line_user_id,
    history,
    *,
    reply_token=None,
    quote_token=None,
    book=None,
) -> Optional[str]:
    """钥匙闸 + agent 循环。命中并接管 → 模型撰写的自然语言回复;否则 None(交旧路)。

    reply_token/quote_token/book=入口的出卡料;写开启时记账走 book 出富卡 + 确认按钮(否则 defer)。
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
        sink = None
        if feature_flags.agent_write_enabled_for(uid):
            sink = _record_sink(
                bound_user, text, lang, tid, ws, line_user_id, reply_token, quote_token, book
            )
        return loop.handle_turn(
            text, ctx, history=history, allow_write=sink is not None, record_sink=sink
        )
    except Exception:
        # 任何异常一律 defer(铁律:Agent 不许把错误抛给用户);带 uid + 栈便于排障。
        logger.warning("[line agent] turn failed; defer to legacy (uid=%s)", uid, exc_info=True)
        return None
