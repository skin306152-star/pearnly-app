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
from services.line_binding import line_client, line_postback, line_reply

logger = logging.getLogger(__name__)


def _terminal_card(reply_token, state, ref, ws, amount, lang, tid, luid) -> None:
    """动作后回终态卡(已撤销/已丢弃):一眼看懂收尾状态,不显示不可执行动作(P1D 验收6)。"""
    import os

    from services.line_binding import line_card

    card = line_card.terminal_card(
        state=state,
        amount=amount,
        doc_id=ref,
        lang=lang,
        liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
        workspace_client_id=str(ws or ""),
    )
    line_reply.reply_messages_context(reply_token, [card], line_user_id=luid, tenant_id=tid)


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
        from services.purchase import docs as docs_svc
        from services.purchase import posting as posting_svc
        from services.purchase import settings as settings_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            if token:
                res = nonce.consume(cur, tenant_id=tid, token=token)
                if res["status"] == "expired":
                    _say("card_action_expired")
                    return
                if res["status"] != "ok":  # used(重放/双击) / missing → 已处理过
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
                cfg = settings_svc.get_settings(cur, **scope)
                res = posting_svc.post_doc(
                    cur,
                    **scope,
                    doc_id=ref,
                    auto_stock_in=bool(cfg.get("auto_stock_in")),
                    created_by=uid,
                )
                _say("card_confirmed", res.get("doc"))

            elif action == line_postback.ACTION_UNDO:
                res = posting_svc.void_doc(cur, **scope, doc_id=ref, created_by=uid)
                # 终态卡(已撤销):徽章 + 整句 + 金额/记录号 + 仅「查看记录」(原单留存可查)。
                _terminal_card(
                    reply_token,
                    "voided",
                    ref,
                    ws,
                    (res.get("doc") or {}).get("grand_total"),
                    lang,
                    tid,
                    luid,
                )

            elif action == line_postback.ACTION_DISCARD:
                docs_svc.delete_doc(cur, **scope, doc_id=ref)  # 仅草稿可删(内部 status='draft' 守)
                # 终态卡(已丢弃):草稿已删→无记录可看→不出「查看」死链(只显徽章+整句)。
                _terminal_card(reply_token, "discarded", ref, ws, None, lang, tid, luid)
    except Exception:
        # 状态错(已入账再确认 / 草稿撤销 / 项已处理)或并发 → 友好回执,不报错。
        logger.warning("[line card] postback action failed", exc_info=True)
        _say("card_action_stale")
