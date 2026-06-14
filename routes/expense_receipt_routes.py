# -*- coding: utf-8 -*-
"""替代收据凭证 PDF 服务(ใบแทนใบเสร็จ · doc 14 §7)。

LINE 卡按钮在外部浏览器打开,无会话 → 用 HMAC 签名 token 鉴权(token 自带 tenant/ws/draft/exp,
不需 DB 查权限)。token 由 confirm 回执时签发(JWT_SECRET 签)。验签 + 未过期 → 取草稿渲染 PDF。
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Query, Response

from services.expense import receipt_token

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/expense/receipt/{draft_id}")
def expense_receipt_pdf(draft_id: str, t: str = Query("")):
    """替代收据 PDF(token 鉴权 · 公开路由白名单)。token 失效/不符 → 403。"""
    payload = receipt_token.verify(t, int(time.time()))
    if not payload or payload.get("d") != draft_id:
        return Response("invalid or expired link", status_code=403)

    from core import db
    from services.expense import expense_draft as draft_store
    from services.expense.receipt_pdf import build_receipt_pdf

    tid, ws = payload["t"], int(payload["w"])
    with db.get_cursor_rls(tid) as cur:
        d = draft_store.get_draft(cur, tenant_id=tid, workspace_client_id=ws, draft_id=draft_id)
        biz = ""
        if d:
            cur.execute(
                "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s", (ws, tid)
            )
            row = cur.fetchone()
            biz = (row["name"] or "") if row else ""
    if not d:
        return Response("not found", status_code=404)

    d["business_name"] = biz
    pdf = build_receipt_pdf(d)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="receipt-{draft_id[:8]}.pdf"'},
    )
