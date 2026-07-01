# -*- coding: utf-8 -*-
"""对话 Agent 插座 ↔ LINE 入口的桥(WP5)。

line_expense.handle_expense_text 为灰度用户在关键词分支「之前」调 try_agent_turn(前门倒置):
模型自己判意图——查询/闲聊自己组织人话回复(接管本轮),记账/改错/超范围 → 返 None(defer),
调用方逐字节落回旧 understand()+_dispatch_agent()。能力只增不减,旧路一行不改。
"""

from __future__ import annotations

import logging

from services.agent.loop import TurnResult  # 前门结论类型(reply/card_sent/defer_*/crash)

logger = logging.getLogger(__name__)

__all__ = ["TurnResult", "frontdoor_enabled", "write_enabled", "try_agent_turn"]


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
) -> TurnResult:
    """钥匙闸 + agent 循环 → TurnResult。故障/未启用一律归 crash(入口走安全兜底,绝不掉旧路地雷)。

    reply_token/quote_token/book=入口的出卡料;写开启时记账走 book 高置信直录出富卡。
    lang 保留兼容:回复语言由模型按用户最新消息自适应,不再套模板。
    """
    from core import feature_flags

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    if not feature_flags.agent_enabled_for(uid):
        return TurnResult("crash")
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
        # 任何异常 → crash(铁律:Agent 不许把错误抛给用户);入口安全兜底,带 uid + 栈便于排障。
        logger.warning("[line agent] turn failed; safe fallback (uid=%s)", uid, exc_info=True)
        return TurnResult("crash")
