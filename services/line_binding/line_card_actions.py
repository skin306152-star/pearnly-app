# -*- coding: utf-8 -*-
"""LINE 数据卡动作落地(postback → 做账安全带 · docs/smart-intake/15 §4)。

全套动作,让用户「想干嘛干嘛」、永不卡死(均复用现有采购/做账服务,不另起逻辑):
  confirm     草稿 → post_doc(入账 + 做账 enqueue),镜像 web /docs/{id}/post
  undo        已入账 → void_doc(冲销 + 反库存),镜像 web /docs/{id}/void
  discard     草稿 → delete_doc(仅草稿可删;正式单永不物理删,只能 undo)
作用域硬隔离(套账 ws),并发/状态错友好回执不报错。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_booker, line_client, line_postback, line_reply

logger = logging.getLogger(__name__)


def _terminal_card(reply_token, state, ref, ws, amount, lang, tid, luid, *, detail=None) -> None:
    """动作后回终态卡(已撤销/已丢弃):一眼看懂收尾状态,不显示不可执行动作(P1D 验收6)。
    detail 传入 → 带税前/VAT 拆解,撤销后与确认前后展示一致(P1G·不置零 VAT)。"""
    import os

    from services.line_binding import line_card, line_posted_card

    fields = line_posted_card.fields_from_detail(detail) if detail else None
    card = line_card.terminal_card(
        state=state,
        amount=amount,
        doc_id=ref,
        lang=lang,
        liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
        workspace_client_id=str(ws or ""),
        fields=fields,
    )
    # 终态卡(已撤销/已丢弃)也是"代表真单据"的卡 → 出卡口登记锚点(引用它仍可说「恢复」·06)。
    line_booker.send_doc_card(
        card,
        reply_token=reply_token,
        tenant_id=tid,
        ws=ws,
        line_user_id=luid,
        doc_id=ref,
        state=state,
    )


def send_terminal(reply_token, *, state, doc_id, ws, amount, lang, tid, luid, detail=None) -> None:
    """对外:撤销/删除后回终态卡(已撤销/已丢弃·复用 _terminal_card·验收 #4)。
    detail=作废/删除前的单据详情 → 终态卡带税额拆解(验收:撤销后税前/VAT 与确认前后一致)。"""
    _terminal_card(reply_token, state, doc_id, ws, amount, lang, tid, luid, detail=detail)


def send_detail_link(reply_token, text, *, doc_id, ws, lang, tid, luid, quote_token="") -> None:
    """多行/明细需详情页 → 文案 + 「打开详情」按钮(真 deeplink·不只文字·验收 #5)。"""
    import os

    from services.line_binding import line_card_i18n, line_card_sections

    uri = line_card_sections.liff_link(
        os.getenv("LINE_LIFF_ID", "").strip(),
        "https://pearnly.com/home",
        str(doc_id),
        view="edit",
        ws=str(ws or ""),
    )
    label = line_card_i18n.chrome(lang).get("btn_detail") or "Detail"
    body = (text or "Pearnly")[:160]
    msg = {
        "type": "template",
        "altText": body,
        "template": {
            "type": "buttons",
            "text": body,
            "actions": [{"type": "uri", "label": label[:20], "uri": uri}],
        },
    }
    line_reply.reply_messages_context(
        reply_token, [msg], line_user_id=luid, tenant_id=tid, quote_token=quote_token
    )


def _send_posted(cur, reply_token, detail, *, ref, ws, lang, tid, luid) -> None:
    """入账成功 → posted 数据卡(状态/金额/日期/卖家/记录号 + 查看详情/撤销·验收 1),并续接
    active_doc:入账后续低风险改错(seller/date/category/payment)无需引用即命中同一张(验收 5)。"""
    from services.line_binding import line_posted_card

    card = line_posted_card.build(detail, doc_id=ref, lang=lang, workspace_client_id=ws)
    # 出卡口登记锚点 + 续接 active_doc(state=posted·设焦点,免再单独 _set_active)。
    line_booker.send_doc_card(
        card,
        reply_token=reply_token,
        tenant_id=tid,
        ws=ws,
        line_user_id=luid,
        doc_id=ref,
        state="posted",
        cur=cur,
    )


def _send_voided(reply_token, *, ref, ws, lang, tid, luid, detail) -> None:
    """已撤销终态卡(带税额拆解·金额取自 detail):postback 撤销 / 重复点击重发 共用(去重复)。"""
    amount = (detail.get("doc") or {}).get("grand_total") if detail else None
    _terminal_card(reply_token, "voided", ref, ws, amount, lang, tid, luid, detail=detail)


def _reshow_current(cur, reply_token, *, ref, ws, lang, tid, luid) -> None:
    """重复点击/已处理 → 按单据真实状态重发当前卡(验收 2/6):posted 重发 posted 卡(不重复入账)、
    void 回终态卡;草稿/已删 → 友好回执(不报错、不跳登录)。"""
    from services.purchase import docs as docs_svc

    detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=ref)
    status = (detail.get("doc") or {}).get("status") if detail else None
    if status == "posted":
        _send_posted(cur, reply_token, detail, ref=ref, ws=ws, lang=lang, tid=tid, luid=luid)
    elif status == "void":
        _send_voided(reply_token, ref=ref, ws=ws, lang=lang, tid=tid, luid=luid, detail=detail)
    else:
        line_reply.reply_text_context(
            reply_token,
            line_client.t_line(lang, "card_action_stale"),
            line_user_id=luid,
            tenant_id=tid,
        )


def send_state_card_reply(cur, reply_token, *, doc_id, ws, lang, tid, luid) -> bool:
    """改错低风险直改后回当前状态卡(Req5 · reply 版):posted 数据卡 / draft 可确认卡 / void 终态卡。

    替代原「已更新 X→Y」纯文字 —— 让用户看到改动后的整张卡。状态→卡映射复用 line_posted_card.
    build_state_card;token 留空走兼容动作链路(active 续接由调用方另设)。返回是否已发卡(否→回文字)。
    """
    from services.line_binding import line_posted_card
    from services.purchase import docs as docs_svc

    detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
    card = line_posted_card.build_state_card(
        detail, doc_id=doc_id, ws=ws, lang=lang, source="doc", token=""
    )
    if card is None:
        return False
    line_booker.send_doc_card(
        card,
        reply_token=reply_token,
        tenant_id=tid,
        ws=ws,
        line_user_id=luid,
        doc_id=doc_id,
        state=line_booker.state_from_status((detail.get("doc") or {}).get("status")),
        cur=cur,
    )
    return True


def handle_postback(bound_user, reply_token, data: str, lang: str) -> None:
    """卡按钮回调 → 全套动作分发。任何异常都回执不抛(主路径不得崩)。

    带一次性令牌(PO-12)→ 原子消费防重放,目标记录取自令牌(不信客户端 doc_id);
    旧卡无令牌 → 兼容链路(default_workspace_id + 客户端 ref,状态机仍防双击)。
    回执统一走 line_reply(postback 按钮无用户消息可引用 → 普通回复,不带 quoteToken)。
    """
    parsed = line_postback.parse(data)
    action, ref, token = parsed["action"], parsed["doc_id"], parsed["token"]
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    luid = bound_user.get("line_user_id") or ""

    # 批量撤销自带令牌消费 + 逐笔执行,走独立模块(不进单条 doc 的 consume/reshow 逻辑)。
    if action in (line_postback.ACTION_BULK_UNDO, line_postback.ACTION_BULK_CANCEL):
        from services.expense import line_bulk_undo

        line_bulk_undo.handle_postback(bound_user, reply_token, action, token, lang)
        return

    # 学习按钮(Phase B-1):令牌自带学习 payload,按 scope 写 expense_learned,走独立模块。
    if action == line_postback.ACTION_LEARN:
        from services.expense import line_learn

        line_learn.handle_postback(bound_user, reply_token, parsed["scope"], token, lang)
        return

    def _say(key, doc=None):
        amt = (doc or {}).get("grand_total") if doc is not None else None
        line_reply.reply_text_context(
            reply_token,
            line_client.t_line(lang, key, amount=amt),
            line_user_id=luid,
            tenant_id=tid,
        )

    if not action or not tid:
        _say("card_action_stale")
        return
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    try:
        from core.workspace_context import default_workspace_id
        from services.line_binding import line_action_nonce as nonce
        from services.purchase import correct as correct_svc
        from services.purchase import posting as posting_svc
        from services.purchase import settings as settings_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            if token:
                res = nonce.consume(cur, tenant_id=tid, token=token)
                if res["status"] == "expired":
                    _say("card_action_expired")
                    return
                if res["status"] == "used":  # 重放/双击 → 按真实状态重发当前卡(验收 2),不报错
                    ref, ws = res.get("action_ref"), res.get("workspace_client_id")
                    if ref and ws is not None:
                        _reshow_current(
                            cur, reply_token, ref=ref, ws=ws, lang=lang, tid=tid, luid=luid
                        )
                    else:
                        _say("card_action_stale")
                    return
                if res["status"] != "ok":  # missing(伪造/旧卡无此 token)
                    _say("card_action_stale")
                    return
                ref = res["action_ref"]
                ws = res["workspace_client_id"]
            else:
                ws = default_workspace_id(cur, tid)
            if ws is None or not ref:
                _say("card_action_stale")
                return
            scope = {"tenant_id": tid, "workspace_client_id": ws}

            if action == line_postback.ACTION_CONFIRM:
                from core.pos_api import PosError

                cfg = settings_svc.get_settings(cur, **scope)
                try:
                    res = posting_svc.post_doc(
                        cur,
                        **scope,
                        doc_id=ref,
                        auto_stock_in=bool(cfg.get("auto_stock_in")),
                        created_by=uid,
                    )
                except PosError as e:
                    # 重复点击(单已非草稿)→ 重发当前状态卡,不重复入账/不报错/不跳登录(验收 2)。
                    if (e.code or "") == "purchase.not_draft":
                        _reshow_current(
                            cur, reply_token, ref=ref, ws=ws, lang=lang, tid=tid, luid=luid
                        )
                        return
                    raise
                _send_posted(cur, reply_token, res, ref=ref, ws=ws, lang=lang, tid=tid, luid=luid)

            elif action == line_postback.ACTION_UNDO:
                res = posting_svc.void_doc(cur, **scope, doc_id=ref, created_by=uid)
                # 终态卡(已撤销):徽章 + 整句 + 金额/税额拆解/记录号 + 「查看记录」(原单留存可查)。
                _send_voided(reply_token, ref=ref, ws=ws, lang=lang, tid=tid, luid=luid, detail=res)

            elif action == line_postback.ACTION_DISCARD:
                # 软删(status=discarded·留库可恢复)·仅草稿(内部 status='draft' 守)。
                correct_svc.discard_doc(cur, **scope, doc_id=ref)
                # 终态卡(已丢弃):仍显「已丢弃」徽章+整句(可引用该卡说「恢复」找回·Slice 2b)。
                _terminal_card(reply_token, "discarded", ref, ws, None, lang, tid, luid)
    except Exception:
        # 状态错(已入账再确认 / 草稿撤销 / 项已处理)或并发 → 友好回执,不报错。
        logger.warning("[line card] postback action failed", exc_info=True)
        _say("card_action_stale")
