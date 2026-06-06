# -*- coding: utf-8 -*-
"""单据 PDF 组装(解析双方 + 渲染 · PO-6/PO-7 共用)。

已开出从冻结快照取双方(docs/16 §A · 不实时 join);草稿/旧单实时组合。渲染层直接吃
get_document 返回的原始行(列已是扁平 totals/payment + lines),不需先转 API JSON。
下载 / 发送 / 公开分享三条路径走同一套,避免重复。
"""

from __future__ import annotations

from services.sales import buyer as buyer_mod
from services.sales import pdf as pdf_svc
from services.sales import seller_profile


def resolve_parties(cur, *, tenant_id: str, doc: dict):
    """PDF 双方来源:已开出从快照,草稿实时组合,旧单回退 clients。"""
    snap = doc.get("parties_snapshot")
    if snap:
        return snap.get("seller"), snap.get("buyer")
    seller = None
    if doc.get("seller_workspace_client_id"):
        seller = seller_profile.get_seller(
            cur, tenant_id=tenant_id, workspace_client_id=doc["seller_workspace_client_id"]
        )
    if doc.get("buyer_type"):
        buyer = buyer_mod.from_row(doc)
    elif doc.get("client_id"):
        buyer = seller_profile.get_buyer(cur, tenant_id=tenant_id, client_id=doc["client_id"])
    else:
        buyer = None
    return seller, buyer


def build_pdf(
    cur,
    *,
    tenant_id: str,
    doc: dict,
    page: str = "A4",
    copy_kind: str = "original",
    copies_layout: str = "separate",
    parties: tuple = None,
) -> bytes:
    """parties 给了就复用(避免调用方已解析后再解析一次);否则现解析。"""
    seller, buyer = (
        parties if parties is not None else resolve_parties(cur, tenant_id=tenant_id, doc=doc)
    )
    return pdf_svc.render_invoice_pdf(
        doc, seller, buyer, page=page, copy_kind=copy_kind, copies_layout=copies_layout
    )
