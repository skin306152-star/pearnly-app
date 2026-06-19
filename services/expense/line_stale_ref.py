# -*- coding: utf-8 -*-
"""引用旧卡片的目标定位 + 死单安全网(LINE 平台 05 · Slice 1 · 账务级红线)。

LINE 聊天里发出的卡片气泡是死快照,底层单据(purchase_docs)会被改/撤/删。用户引用一张旧卡片
操作时,系统必须对【那张单据的当前真实状态】负责:活单→改;被更正(SUPERSEDED)→ 落最新活单;
已撤(VOIDED)/已删(DISCARDED)→ 不改死单、给出路。★绝不悄悄回落到「最近活跃单」去操作
(screenshot-29 真事故:引用已删 99090 + 改金额 → 改了另一张活记录 150)。

无引用时沿用 active 续接(行为不变)。状态判定见 line_message_refs.resolve_card_state。
"""

from __future__ import annotations

from core import db
from services.expense import conversation
from services.expense import line_correct as lc
from services.expense import line_correct_i18n as ci
from services.line_binding import line_client, line_message_refs
from services.purchase import docs as docs_svc


def _active_target(cur, line_user_id):
    """active 续接态(correctactive:<ws>:<doc>)指向的 (ws, doc_id);无 active → None。"""
    pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    m = str((pend or {}).get("missing") or "")
    if not m.startswith(lc._ACTIVE_PREFIX):
        return None
    ws_s, _, doc_id = m[len(lc._ACTIVE_PREFIX) :].partition(":")
    try:
        return int(ws_s), doc_id
    except (ValueError, TypeError):
        return ws_s, doc_id


def _superseded(live, reply_lang) -> dict:
    """SUPERSEDED → 落最新活单 + 提示前缀(并进同一条回复·reply_token 单次性)。"""
    doc = live.get("doc") or {}
    notice = ci.t(
        ci.SUPERSEDED_PREFIX,
        reply_lang,
        amt=ci.money(doc.get("grand_total")),
        ref=ci.short_ref(doc.get("id")),
    )
    return {
        "detail": live,
        "ws": doc.get("workspace_client_id"),
        "doc_id": str(doc.get("id")),
        "notice": notice,
    }


def locate_clarify_target(
    tid, ws, luid, text, quoted_message_id, reply_lang, *, has_amount
) -> dict:
    """定位「引用卡片 / active 续接」的改错目标 + 判定其当前真实状态。返回 dict:
    {"detail","ws","doc_id","notice"} 继续改 / {"reply": body} 终态回复 / {"passthrough": True} 放行记账。
    """
    with db.get_cursor_rls(tid) as cur:
        if quoted_message_id:
            tgt = line_message_refs.resolve_target(
                cur,
                tenant_id=tid,
                ws=ws,
                line_user_id=luid,
                quoted_message_id=quoted_message_id,
                text=text,
            )
            doc_id = tgt["doc_id"] if not tgt.get("error") else None
            if not doc_id:  # 引用 ref 过期/查不到 → 当死单,诚实提示,绝不碰别的单
                return {"reply": ci.t(ci.STALE_DISCARDED, reply_lang)}
            ws_eff = tgt["ws"]
            state, live = line_message_refs.resolve_card_state(
                cur, tid=tid, ws=ws_eff, doc_id=doc_id
            )
            if state == line_message_refs.LIVE:
                return {"detail": live, "ws": ws_eff, "doc_id": doc_id, "notice": ""}
            if state == line_message_refs.SUPERSEDED:
                got = _superseded(live, reply_lang)
                got["ws"] = got["ws"] if got["ws"] is not None else ws_eff
                return got
            if state == line_message_refs.VOIDED:
                return {"reply": ci.t(ci.STALE_VOIDED, reply_lang)}
            return {"reply": ci.t(ci.STALE_DISCARDED, reply_lang)}  # DISCARDED / 查不到
        act = _active_target(cur, luid)
        if act:
            ws_eff, doc_id = act
            detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws_eff, doc_id=doc_id)
            if lc._is_live(detail):
                return {"detail": detail, "ws": ws_eff, "doc_id": doc_id, "notice": ""}
    if has_amount:  # 无引用、无 active 活单、像一句新记账 → 放行给记账流(不劫持「买错了 50」)
        return {"passthrough": True}
    return {"reply": line_client.t_line(reply_lang, "line_need_reply_record")}
