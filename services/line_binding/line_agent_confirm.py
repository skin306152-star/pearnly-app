# -*- coding: utf-8 -*-
"""记账确认续接(前门倒置·写档)—— agentrec 待办的"是/否"落地。

Agent 提议记账 → loop 落待办(line_pending_entry·前缀 AGENTREC)+ 大脑自撰复述问确认;
下一条用户消息在入口先走这里:确认 → pop 待办由注入的 book 回调落库;否/取消 → 清 + 回「已取消」;
新话题 → 清待办放行(绝不悬着误落库)。落库回调注入(line_expense._do_record)避免循环导入。
"""

from __future__ import annotations

from core import db
from services.line_binding import line_agent_bridge, line_reply


def classify_reply(text: str) -> str:
    """待确认续接时用户回复分类:yes(确认)/ no(取消)/ other(新话题·清待办放行)。

    yes 复用改错流的 _affirmative(否定优先·"不对"不误判"对");又发带金额新句 = 新记账,不当"是"。
    """
    from services.expense import line_classify, line_correct
    from services.expense import line_quick_entry as lqe

    if line_correct._affirmative(text) and not lqe.parse_expense(text).has_amount():
        return "yes"
    if line_classify.is_cancel_intent(text) or any(n in text.lower() for n in line_correct._NO):
        return "no"
    return "other"


def resolve_record(bound_user, reply_token, text, tid, ws, lang, ctx, *, book) -> bool:
    """有 agentrec 待办 → 按回复落库/取消/放行;写关或无待办 → False(交后续路由)。

    ctx = handle_expense_text 的回复上下文 dict(quote_token / line_user_id / tenant_id)。
    """
    from services.expense import conversation, line_classify

    if not line_agent_bridge.write_enabled(bound_user):
        return False
    line_user_id = ctx["line_user_id"]
    quote_token = ctx.get("quote_token")
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    if not pend or not str(pend.get("missing") or "").startswith(line_agent_bridge.AGENTREC):
        return False

    reply_lang = line_classify.detect_text_lang(text) or lang
    kind = classify_reply(text)
    if kind == "yes":
        with db.get_cursor_rls(tid, commit=True) as cur:
            popped = conversation.pop_pending(cur, line_user_id=line_user_id)
        if not popped:  # 竞态/刚过期 → 不误落库
            return False
        draft = popped["draft"]
        return book(
            bound_user,
            reply_token,
            draft.raw_text or text,
            tid,
            popped["workspace_client_id"],
            draft,
            True,
            quote_token,
            reply_lang,
            line_user_id,
        )

    # 非"是":清待办(不悬着)。明确否定 → 回「已取消」;含糊/新话题 → 放行让新消息正常路由。
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.clear_pending(cur, line_user_id=line_user_id)
    if kind == "no":
        from services.agent import agent_i18n, copy_map

        line_reply.reply_text_context(
            reply_token,
            agent_i18n.render(copy_map.cancelled(), reply_lang),
            quote_token=quote_token,
            line_user_id=line_user_id,
            tenant_id=tid,
        )
        return True
    return False
