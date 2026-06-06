# -*- coding: utf-8 -*-
"""发票分享能力 token(PO-7 · docs/16 §L5)。

给已开票生成一个不可猜的 token,组成公开 PDF 链接(LINE「我自己转发」:卖方用自己 LINE
把链接转给买家;也通用于任何链接式分享)。token 即凭证(capability URL):公开端点不鉴权,
凭 token 反查租户/单据再渲染。token 按需生成、生成后复用。纯参数化叶子。
"""

from __future__ import annotations

import secrets
from typing import Optional


def get_or_create_share_token(cur, *, tenant_id: str, doc_id) -> Optional[str]:
    """取/建单据分享 token(已开票才有意义,调用方保证)。已存在直接复用。"""
    cur.execute(
        "SELECT share_token FROM sales_documents WHERE tenant_id=%s AND id=%s",
        (tenant_id, doc_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    if row.get("share_token"):
        return row["share_token"]
    token = secrets.token_urlsafe(24)
    cur.execute(
        "UPDATE sales_documents SET share_token=%s, updated_at=now() WHERE tenant_id=%s AND id=%s",
        (token, tenant_id, doc_id),
    )
    return token


def resolve_token(cur, token: str) -> Optional[dict]:
    """凭 token 反查 {tenant_id, document_id}(无租户上下文,调用方用 bypass-RLS 游标)。"""
    if not token:
        return None
    cur.execute(
        "SELECT tenant_id, id AS document_id FROM sales_documents WHERE share_token=%s",
        (token,),
    )
    return cur.fetchone()
