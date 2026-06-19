# -*- coding: utf-8 -*-
"""引用已撤单说「恢复」→ 真恢复出新活单(LINE 平台 05 · Slice 2 · 恢复闭环)。

用户引用一张已撤销(VOIDED)的卡片说「恢复/กู้คืน/restore」→ 克隆原单数据(行/卖家/日期/分类/
票面)为新单并重新过账成 posted(restored_from 审计链·原死单不动)。活单/已更正/草稿删/已结期 →
诚实文案,不建单。恢复幂等:已恢复过 → 给当前活单不重复建。意图判定见 line_classify.detect_restore。
"""

from __future__ import annotations

from core import db
from core.pos_api import PosError
from services.expense import line_classify, line_correct
from services.expense import line_correct_i18n as ci
from services.line_binding import line_message_refs, line_reply
from services.purchase import correct as correct_svc


def maybe_restore(
    bound_user, reply_token, line_user_id, text, lang, tid, ws, quoted_message_id, ctx
) -> bool:
    """恢复意图入口(改字段路由之前判):非恢复 → False。引用 VOIDED → 重建活单;其余按状态诚实回。"""
    if not line_classify.detect_restore(text, has_quote=bool(quoted_message_id)):
        return False
    reply_lang = line_classify.detect_text_lang(text) or lang

    def _say(body):
        line_reply.reply_text_context(
            reply_token,
            body,
            quote_token=ctx.get("quote_token", ""),
            line_user_id=line_user_id,
            tenant_id=tid,
        )

    if not quoted_message_id:  # 裸「恢复」无引用 → 请引用要恢复的那张卡
        _say(ci.t(ci.RESTORE_NEED_QUOTE, reply_lang))
        return True
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            tgt = line_message_refs.resolve_target(
                cur,
                tenant_id=tid,
                ws=ws,
                line_user_id=line_user_id,
                quoted_message_id=quoted_message_id,
                text=text,
            )
            doc_id = tgt["doc_id"] if not tgt.get("error") else None
            if not doc_id:  # 引用过期/查不到
                _say(ci.t(ci.RESTORE_NEED_QUOTE, reply_lang))
                return True
            ws_eff = tgt["ws"]
            state, live = line_message_refs.resolve_card_state(
                cur, tid=tid, ws=ws_eff, doc_id=doc_id
            )
            if state == line_message_refs.LIVE:
                _say(ci.t(ci.RESTORE_NOT_VOIDED, reply_lang))
                return True
            if state == line_message_refs.SUPERSEDED:
                d = live.get("doc") or {}
                _say(
                    ci.t(
                        ci.RESTORE_ALREADY,
                        reply_lang,
                        ref=ci.short_ref(d.get("id")),
                        amt=ci.money(d.get("grand_total")),
                    )
                )
                return True
            # VOIDED(已撤)/ DISCARDED(草稿软删·或旧物理删)→ 尝试恢复(restore_doc 区分软删/已删)。
            res = correct_svc.restore_doc(
                cur, tenant_id=tid, workspace_client_id=ws_eff, doc_id=doc_id, created_by=uid
            )
            if res.get("gone"):  # 旧物理删·数据已不在 → 诚实引导重记
                _say(ci.t(ci.RESTORE_GONE, reply_lang))
                return True
            if res.get("not_deleted"):  # 活单 → 没删没撤(幂等)
                _say(ci.t(ci.RESTORE_NOT_VOIDED, reply_lang))
                return True
            if res.get("already"):
                row = res["already"]
                _say(
                    ci.t(
                        ci.RESTORE_ALREADY,
                        reply_lang,
                        ref=ci.short_ref(row["id"]),
                        amt=ci.money(row["grand_total"]),
                    )
                )
                return True
            rdoc = (res["restored"].get("doc")) or {}
            new_id = str(rdoc.get("id"))
            line_correct._set_active(tid, ws_eff, new_id, line_user_id, cur=cur)
            _say(
                ci.t(
                    ci.RESTORE_DONE,
                    reply_lang,
                    amt=ci.money(rdoc.get("grand_total")),
                    ref=ci.short_ref(new_id),
                )
            )
            return True
    except PosError as e:
        if (e.code or "") in ("acct.period_closed", "acct.no_open_period"):
            _say(ci.t(ci.RESTORE_CLOSED, reply_lang))
            return True
        raise
