# -*- coding: utf-8 -*-
"""LINE 文本路 · 查账/问答/撤销 回复(从 line_expense 抽出 · 控 <500)。

只读 QA + 撤销四件:本月汇总 / 本月明细 / 撤销上一笔 / 知识中心问答。
都是 DB 真查(绝不让模型编数字)+ line_i18n 模板回复。逻辑零改,纯搬家。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_client, line_reply

logger = logging.getLogger(__name__)


def _today_th() -> str:
    """今天日期(泰国本地·ISO)· 答「今天几号」用。复用开票历法叶子,口径与连号/票面一致。"""
    from services.sales import dates

    return dates.bangkok_today().isoformat()


def _qr_item(label: str, text: str) -> dict:
    return {"type": "action", "action": {"type": "message", "label": label[:20], "text": text}}


# 问候/引导/跑题 + 大脑 chat_kind 枚举 → 统一 line_i18n 文案(P1E-1·Brain OS);感谢/求助仍走
# replies 轮选池(治复读)。L1 intro_intent 与 L2 chat_kind 共用此表,同义入口收敛到同一套文案。
_DIRECT_KEY = {
    "greeting": "line_greeting",
    "capability": "line_intro_capability",
    "start": "line_start_hint",
    "upload": "line_upload_hint",
    "receipt_help": "line_upload_hint",
    "edit_help": "line_need_reply_record",
    "delete_help": "line_need_reply_record",
    "photo_failed_help": "line_ocr_failed_recovery",
    # out_of_scope / unknown 不在此表 → 落 replies.pick 轮选池(P3A-2b·治复读·语气层回落话术)。
    # 旧键 line_out_of_scope / line_unknown_intent 已无引用,留着无害(P3A-3 清)。
}
# 「记一笔」Quick Reply 不再发演示金额(会误记一笔),改触发「怎么开始」引导(line_start_hint)。
_QR_START = {"zh": "怎么开始", "th": "เริ่มยังไง", "en": "How to start", "ja": "始め方"}


def reply_pool(
    reply_token,
    kind,
    text,
    lang,
    *,
    override_body=None,
    quote_token="",
    line_user_id="",
    tenant_id=None,
) -> None:
    """问候/感谢/求助/跑题 → 回复 + Quick Reply 引导(不复读)· 引用用户当前消息。

    问候(greeting)/跑题(scope)取 line_i18n 收口文案;感谢/求助走 replies 轮选池(治复读)。
    override_body 非空(P3A-2 自然语气层)→ 直接用它作正文,跳过模板查表;Quick Reply 钩子照常带上。
    """
    from services.expense import replies

    start_txt = _QR_START.get((lang or "zh").lower(), _QR_START["th"])
    items = [
        _qr_item(line_client.t_line(lang, "qr_record"), start_txt),
        _qr_item(line_client.t_line(lang, "qr_query"), line_client.t_line(lang, "qr_query_text")),
    ]
    if override_body:
        body = override_body
    elif kind == "date_query":
        # 日期与记账相关:答今天日期(确定性·泰国时区)再引导继续,不当离题。
        body = line_client.t_line(lang, "line_date_answer", date=_today_th())
    else:
        key = _DIRECT_KEY.get(kind)
        body = line_client.t_line(lang, key) if key else replies.pick(kind, text, lang)
    msg = {"type": "text", "text": body, "quickReply": {"items": items}}
    line_reply.reply_messages_context(
        reply_token, [msg], quote_token=quote_token, line_user_id=line_user_id, tenant_id=tenant_id
    )


def reply_summary(reply_token, lang, tid, ws, *, quote_token="", line_user_id="") -> None:
    """查账汇总(本月已入账 + 按分类拆解)· DB 真查,绝不让模型编数字。引用用户当前消息。"""
    from services.expense import line_qa

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    try:
        with db.get_cursor_rls(tid) as cur:
            s = line_qa.month_summary(cur, tenant_id=tid, workspace_client_id=ws)
    except Exception:
        logger.exception("[line] summary failed")
        _say(line_client.t_line(lang, "exp_q_not_found"))
        return
    if s["count"] == 0:
        _say(line_client.t_line(lang, "exp_sum_empty"))
        return
    uncat = line_client.t_line(lang, "exp_uncat")
    lines = [
        line_client.t_line(lang, "line_query_summary_intro"),
        "",
        line_client.t_line(lang, "exp_sum_head", amount=s["total"], n=s["count"]),
    ]
    for c in s["by_category"][:6]:
        lines.append(f"• {c['name'] or uncat}: ฿{c['amount']} ({c['count']})")
    _say("\n".join(lines))


def reply_detail(reply_token, lang, tid, ws, line_user_id=None, *, quote_token="") -> None:
    """查明细(本月逐笔)· DB 真查 → 列表。存有序 doc_id 入会话态供「第 N 笔改成…」定位(P2)。"""
    from services.expense import line_qa

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    try:
        with db.get_cursor_rls(tid) as cur:
            rows = line_qa.month_detail(cur, tenant_id=tid, workspace_client_id=ws, limit=10)
    except Exception:
        logger.exception("[line] detail failed")
        _say(line_client.t_line(lang, "exp_q_not_found"))
        return
    if not rows:
        _say(line_client.t_line(lang, "exp_sum_empty"))
        return
    uncat = line_client.t_line(lang, "exp_uncat")
    lines = [line_client.t_line(lang, "line_query_detail_intro"), ""]
    for i, r in enumerate(rows, 1):
        tail = f" · {r['vendor']}" if r["vendor"] else ""
        lines.append(f"{i}. {r['date']} {r['category'] or uncat} ฿{r['amount']}{tail}")
    if line_user_id:
        _remember_detail_order(tid, ws, line_user_id, [r["id"] for r in rows])
    _say("\n".join(lines))


def _remember_detail_order(tid, ws, line_user_id, ids) -> None:
    """把列表的 doc_id 顺序记进会话态(missing=detail:id1,id2,…),供下一句「第 N 笔改成…」定位。"""
    from services.expense import conversation
    from services.expense.expense_draft import ExpenseDraft

    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.save_pending(
                cur,
                line_user_id=line_user_id,
                tenant_id=tid,
                workspace_client_id=ws,
                draft=ExpenseDraft(),
                missing="detail:" + ",".join(ids),
            )
    except Exception:
        logger.warning("[line] remember detail order failed; 第N笔 定位将回落上一笔")


_UNDO_ERR = {
    "ambiguous": "line_need_reply_record",
    "ref_not_found": "guide_detail_list",
    "none": "exp_undo_none",
}


def _undo_resolved(
    bound_user, reply_token, lang, tid, ws, doc_id, line_user_id, quote_token
) -> None:
    """对已定位的 (ws, doc_id) 执行撤销:草稿丢弃 / 已入账 void → 终态卡。查不到(已删)→ stale_discarded
    幂等;已结期 → 诚实拦。reply_undo(引用/上一笔)与 reply_undo_last(裸撤最近)共用,消除两份撤销核。"""
    from core.pos_api import PosError
    from services.line_binding import line_card_actions
    from services.purchase import correct as correct_svc
    from services.purchase import docs as docs_svc
    from services.purchase import posting as posting_svc

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
            status = (detail.get("doc") or {}).get("status") if detail else None
            if status is None or status == "discarded":
                # 单已删(物理删/软删 discarded)→ 幂等回「已删除」,不报错、绝不碰别的单(05 账务安全)。
                from services.expense import line_correct_i18n as ci

                _say(ci.t(ci.STALE_DISCARDED, lang))
                return
            if status == "draft":
                # 草稿未入账,「取消/删除」= 软删丢弃(status=discarded·留库可恢复),不走 void → 永不死路。
                amt = (detail.get("doc") or {}).get("grand_total")
                correct_svc.discard_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
                line_card_actions.send_terminal(
                    reply_token,
                    state="discarded",
                    doc_id=doc_id,
                    ws=ws,
                    amount=amt,
                    lang=lang,
                    tid=tid,
                    luid=line_user_id,
                    detail=detail,
                )
                return
            res = posting_svc.void_doc(
                cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id, created_by=uid
            )
            amt = (res.get("doc") or {}).get("grand_total")
        line_card_actions.send_terminal(
            reply_token,
            state="voided",
            doc_id=doc_id,
            ws=ws,
            amount=amt,
            lang=lang,
            tid=tid,
            luid=line_user_id,
            detail=res,
        )
    except PosError as e:
        if (e.code or "") == "acct.period_closed":
            _say(line_client.t_line(lang, "exp_correct_closed"))
            return
        logger.warning("[line] undo blocked: %s", e.code)
        _say(line_client.t_line(lang, "exp_undo_none"))
    except Exception:
        logger.exception("[line] undo failed")
        _say(line_client.t_line(lang, "exp_undo_none"))


def reply_undo(
    bound_user,
    reply_token,
    lang,
    tid,
    ws,
    line_user_id=None,
    quoted_message_id=None,
    text="",
    *,
    quote_token="",
) -> None:
    """撤销已入账单 · void_doc 冲销(不物理删)。目标定位:引用某条→撤那张;明确「上一笔」→撤最近;
    对象不明确→提示 reply 某条记录(绝不默认撤最近一笔)。已结期 → 诚实引导网页。"""
    from services.line_binding import line_message_refs

    with db.get_cursor_rls(tid) as cur:
        tgt = line_message_refs.resolve_target(
            cur,
            tenant_id=tid,
            ws=ws,
            line_user_id=line_user_id,
            quoted_message_id=quoted_message_id,
            text=text,
        )
    if tgt["error"]:
        line_reply.reply_text_context(
            reply_token,
            line_client.t_line(lang, _UNDO_ERR[tgt["error"]]),
            quote_token=quote_token,
            line_user_id=line_user_id,
            tenant_id=tid,
        )
        return
    _undo_resolved(
        bound_user, reply_token, lang, tid, tgt["ws"], tgt["doc_id"], line_user_id, quote_token
    )


def reply_undo_last(bound_user, reply_token, lang, tid, ws, line_user_id, quote_token="") -> None:
    """裸「取消/删除」无引用 → 撤最近一笔 LINE 已入账单(find_last_posted)。无 → 诚实「没有可撤销的」。"""
    from services.line_binding import line_message_refs

    with db.get_cursor_rls(tid) as cur:
        row = line_message_refs.find_last_posted(cur, tenant_id=tid, ws=ws)
    if not row:
        line_reply.reply_text_context(
            reply_token,
            line_client.t_line(lang, "exp_undo_none"),
            quote_token=quote_token,
            line_user_id=line_user_id,
            tenant_id=tid,
        )
        return
    _undo_resolved(
        bound_user, reply_token, lang, tid, ws, str(row["id"]), line_user_id, quote_token
    )


def maybe_bare_undo(
    bound_user, reply_token, line_user_id, text, lang, tid, ws, quoted_message_id, ctx
) -> bool:
    """裸「取消/删除」(无引用·非批量)→ 目标 = 最近展示给用户的那张卡(active 焦点·草稿或已入账·
    implicit anchor·06 §2)→ 草稿丢弃(软删)/ 已入账 void。无焦点才回落 find_last_posted。

    批量(撤N条/全部)交 line_bulk_undo;引用某卡的取消交 try_void_quoted;提问中编辑的取消已被
    try_correction_state 截走(本函数在其之后跑·此处 pending 必非提问态)。非此情形 → False。"""
    from services.expense import line_bulk_undo, line_classify, line_stale_ref

    if quoted_message_id or not (
        line_classify.is_cancel_intent(text) or line_classify.is_delete_intent(text)
    ):
        return False
    if line_bulk_undo.detect_bulk_undo(text) is not None:
        return False
    qt = ctx.get("quote_token", "")
    with db.get_cursor_rls(tid) as cur:
        focus = line_stale_ref._active_target(cur, line_user_id)  # 最近一张卡的 (ws, doc)
    if focus:  # 锚定到当前焦点卡(草稿/已入账·_undo_resolved 按状态丢弃或冲销),不再误撤更早的单
        _undo_resolved(
            bound_user, reply_token, lang, tid, focus[0], str(focus[1]), line_user_id, qt
        )
        return True
    reply_undo_last(bound_user, reply_token, lang, tid, ws, line_user_id, qt)
    return True


def reply_question(reply_token, lang, tid, question, *, quote_token="", line_user_id="") -> None:
    """问答 · 知识中心带出处;查不到诚实兜底 + 指路(绝不编造)。引用用户当前消息。"""
    from services.expense import line_qa

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    try:
        with db.get_cursor_rls(tid) as cur:
            res = line_qa.knowledge_answer(cur, tenant_id=tid, question=question)
    except Exception:
        logger.exception("[line] question failed")
        res = None
    if not res:
        _say(line_client.t_line(lang, "exp_q_not_found"))
        return
    src = ", ".join(res["citations"]) if res.get("citations") else ""
    body = res["answer"]
    if src:
        body += "\n\n" + line_client.t_line(lang, "exp_q_source", src=src)
    _say(body)
