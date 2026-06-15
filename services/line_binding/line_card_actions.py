# -*- coding: utf-8 -*-
"""LINE 数据卡动作落地(postback → 做账安全带 · docs/smart-intake/15 §4)。

confirm:草稿单 → post_doc(正式入账 + 做账 enqueue),镜像 web /docs/{id}/post。
undo:已入账正式单 → void_doc(反过账 + 反库存),镜像 web /docs/{id}/void。
作用域硬隔离(套账 ws),并发/状态错(非草稿确认 / 非 posted 撤销)友好回执不报错。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_client, line_postback

logger = logging.getLogger(__name__)


def handle_postback(bound_user, reply_token, data: str, lang: str) -> None:
    """卡按钮回调 → confirm / undo。任何异常都回执不抛(主路径不得崩)。"""
    parsed = line_postback.parse(data)
    action, doc_id = parsed["action"], parsed["doc_id"]
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    if not action or not doc_id or not tid:
        line_client.reply_text(reply_token, line_client.t_line(lang, "card_action_stale"))
        return
    try:
        from core.workspace_context import default_workspace_id
        from services.purchase import posting as posting_svc
        from services.purchase import settings as settings_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            ws = default_workspace_id(cur, tid)
            if ws is None:
                line_client.reply_text(reply_token, line_client.t_line(lang, "card_action_stale"))
                return
            if action == line_postback.ACTION_CONFIRM:
                cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
                res = posting_svc.post_doc(
                    cur,
                    tenant_id=tid,
                    workspace_client_id=ws,
                    doc_id=doc_id,
                    auto_stock_in=bool(cfg.get("auto_stock_in")),
                    created_by=str(bound_user["id"]) if bound_user.get("id") else None,
                )
                amt = (res.get("doc") or {}).get("grand_total")
                line_client.reply_text(
                    reply_token, line_client.t_line(lang, "card_confirmed", amount=amt)
                )
            else:  # ACTION_UNDO
                res = posting_svc.void_doc(
                    cur,
                    tenant_id=tid,
                    workspace_client_id=ws,
                    doc_id=doc_id,
                    created_by=str(bound_user["id"]) if bound_user.get("id") else None,
                )
                amt = (res.get("doc") or {}).get("grand_total")
                line_client.reply_text(
                    reply_token, line_client.t_line(lang, "card_undone", amount=amt)
                )
    except Exception:
        # 状态错(已入账再确认 / 草稿撤销)或并发 → 友好回执,不报错。
        logger.warning("[line card] postback action failed", exc_info=True)
        line_client.reply_text(reply_token, line_client.t_line(lang, "card_action_stale"))
