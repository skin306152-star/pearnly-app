# -*- coding: utf-8 -*-
"""引用一张卡 → 强锚定整句(LINE 平台 05/06 · Slice 3 · Anchored Action)。

本轮带 quoted_message_id 时,handle_expense_text 在 smalltalk / 记账 L1 / 大脑 / 语气层【全部
之前】先进这里:整句只围绕被引用的那张卡 —— 永不另记一笔、永不操作别的单、永不被语气层带跑。

- 卡片动作(改字段 / 删 / 撤 / 恢复 / 「识别错了」)→ 交既有改错路由 line_correct_flow.route 执行,
  它已按被引用单的【当前真实状态】走死单不改 / 落最新活单 / 恢复(Slice 1/2)。
- 非卡片动作(看着像新记账 / 裸数字 / 闲聊 / 问候 / 全局查账 / 不明)→ 不落新单,锚定回应:
  · 像新记账 / 裸数字 → ANCHOR_SUGGEST_EDIT(把解析值当建议,问要不要用它更新这张)。
  · 闲聊 / 查账 / 不明 → ANCHOR_ASK(฿X · 卖家 → 要对这张做什么)。
- 引用过期 / 查不到 / 回复的不是记录卡 → ANCHOR_EXPIRED(绝不落新单)。
- 被引用单已撤(VOIDED)/ 草稿软删(DISCARDED)且发的是非卡片动作 → 诚实死单文案(STALE_*)。
"""

from __future__ import annotations

from core import db
from services.expense import line_classify, line_correct_flow
from services.expense import line_correct_i18n as ci
from services.expense import line_quick_entry as lqe
from services.line_binding import line_message_refs, line_reply


def maybe_dispatch(
    bound_user, reply_token, line_user_id, text, lang, quoted_message_id, *, quote_token=""
) -> bool:
    """webhook 入口闸(_handle_line_text 在记账/大脑/语气层之前调):本轮有引用 → 解析套账后进强锚定
    分发,接管即 True。无引用 / 无套账 / 未开 expense → False(放行原有流程,无引用路径完全不变)。"""
    if not quoted_message_id:
        return False
    tid = bound_user.get("tenant_id")
    if not tid:
        return False
    stid = str(tid)
    from core.workspace_context import default_workspace_id
    from services.purchase import intake as intake_svc

    text = line_classify.normalize_user_text(text)  # 与 handle_expense_text 同口径(全角标点归一)
    with db.get_cursor_rls(stid) as cur:
        if not intake_svc.line_expense_gate_open(cur, tenant_id=stid):
            return False
        ws = default_workspace_id(cur, stid)
    if ws is None:
        return False
    ctx = dict(quote_token=quote_token, line_user_id=line_user_id, tenant_id=stid)
    return dispatch(
        bound_user, reply_token, line_user_id, text, lang, stid, ws, quoted_message_id, ctx
    )


def dispatch(
    bound_user, reply_token, line_user_id, text, lang, tid, ws, quoted_message_id, ctx
) -> bool:
    """引用某张卡 → 强锚定分发。总返回 True(这张卡的事此处全包,永不回落记账 / 大脑 / 语气层)。

    仅在本轮有 quoted_message_id 且套账已解析时调用。
    """
    reply_lang = line_classify.detect_text_lang(text) or lang
    with db.get_cursor_rls(tid) as cur:
        tgt = line_message_refs.resolve_target(
            cur,
            tenant_id=tid,
            ws=ws,
            line_user_id=line_user_id,
            quoted_message_id=quoted_message_id,
            text=text,
        )
        doc_id = tgt["doc_id"] if not tgt.get("error") else None
        if not doc_id:  # 引用过期 / 查不到 / 回复的不是记录卡 → 锚定失效,绝不落新单
            _say(reply_token, ci.t(ci.ANCHOR_EXPIRED, reply_lang), ctx)
            return True
        state, live = line_message_refs.resolve_card_state(
            cur, tid=tid, ws=tgt["ws"], doc_id=doc_id
        )

    # 卡片动作 → 既有改错路由按被引用单当前真实状态执行(死单不改 / 落最新活单 / 恢复)。
    if line_correct_flow.route(
        bound_user, reply_token, line_user_id, text, lang, tid, ws, quoted_message_id, ctx
    ):
        return True

    # 非卡片动作 → 不落新单,锚定追问 / 建议(按被引用单当前状态)。
    if state in (line_message_refs.LIVE, line_message_refs.SUPERSEDED):
        sug = _suggestion(text)
        if sug:
            doc = (live or {}).get("doc") or {}
            _say(
                reply_token,
                ci.t(ci.ANCHOR_SUGGEST_EDIT, reply_lang, sug=sug, ref=ci.short_ref(doc.get("id"))),
                ctx,
            )
        else:
            _say(reply_token, ci.t(ci.ANCHOR_ASK, reply_lang, who=_card_label(live)), ctx)
        return True
    # 被引用单已死(撤销 / 草稿删)且发的是非卡片动作 → 诚实死单文案,给恢复 / 重记出路。
    pool = ci.STALE_VOIDED if state == line_message_refs.VOIDED else ci.STALE_DISCARDED
    _say(reply_token, ci.t(pool, reply_lang), ctx)
    return True


def _suggestion(text: str) -> str:
    """整句看着像新记账 / 裸数字 → 当作「要把这张改成什么」的建议串;闲聊 / 查账 / 不明 → ''。"""
    parsed = lqe.parse_expense(text)
    if not parsed.has_amount():
        return ""
    amt = ci.money(parsed.amount)
    if not lqe.has_item_context(text):  # 裸数字(无物品 / 无卖家)→ 只建议金额
        return f"฿{amt}"
    item = (parsed.note or "").strip()
    return f"{item} ฿{amt}" if item else f"฿{amt}"


def _card_label(live) -> str:
    """被引用卡的人话标签(฿金额 · 卖家)供锚定追问。卖家空 → 只显金额。"""
    doc = (live or {}).get("doc") or {}
    amt = ci.money(doc.get("grand_total"))
    seller = ((live or {}).get("supplier") or {}).get("name") or ""
    return f"฿{amt} · {seller}" if seller else f"฿{amt}"


def _say(reply_token, body, ctx):
    line_reply.reply_text_context(reply_token, body, **ctx)
