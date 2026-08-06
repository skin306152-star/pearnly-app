# -*- coding: utf-8 -*-
"""POS 补开全式税票通路路由(SM 缺口批次 G2 · 独立文件控 pos_sales_routes 行数)。

两个端点都是收银台/主站行内动作共用的 POS 域出口——主站同能力的权限门
(settings.workspace.manage / sales.doc.view)收银员 token 进不去,这里给等价面并把
作用域收敛:税号查询只读 RD 公开档;发票 PDF 只放「本账套小票升级出的那张」,
不开放任意 doc_id(跨单据面仍归主站销项模块管)。
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from core import db, pos_api
from core.pos_api import PosError, assert_module_enabled, ok, require_workspace_access

router = APIRouter(prefix="/api/pos", tags=["pos-taxinv"])


@router.get("/tax-lookup")
async def api_pos_tax_lookup(
    request: Request,
    tax_id: str = Query(...),
    branch: int = Query(0),
    workspace_client_id: Optional[int] = Query(None),
):
    """税号 → RD 官方名称/地址带出(补开买方表单自动填)。

    复用 services.rd.lookup_vat(SOAP · 7 天缓存 · 5s 超时);同步阻塞丢线程池,
    不堵 event loop(同 workspace_tax_lookup 先例)。查不到/超时 → found:false 交端上
    手填——查不到不是错误,不走 4xx(四态诚实)。归一字段同 workspace 端点。
    """
    user, tid = pos_api.subject(request)
    ws = pos_api.resolve_ws(user, workspace_client_id)
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace_access(cur, request, tid, ws)
    from services.rd.rd_api import lookup_vat, normalize_lookup

    result = await asyncio.to_thread(lookup_vat, tax_id, branch or 0)
    if not result.get("ok"):
        return ok({"found": False, "error": result.get("error") or "not_found"})
    norm = normalize_lookup(result.get("data") or {})
    return ok(
        {
            "found": True,
            "tax_id": norm["tax_id"],
            "name": norm["name"],
            "address": norm["address"],
            "branch_no": norm["branch_no"],
            "branch_label": norm["branch_label"],
            "vat_registered": norm["vat_registered"],
        }
    )


@router.get("/sales/{sale_id}/full-invoice-pdf")
async def api_full_invoice_pdf(
    sale_id: str,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    copy: str = Query("original"),
):
    """已升级小票的全式税票 A4 PDF(打印/重打)。

    作用域:经 sale.full_invoice_id 反查,只出本账套这张小票升级出的单据;
    未升级/单不存在 → pos.product_not_found(同小票详情口径)。
    """
    from services.pos import sales_store
    from services.sales import document as doc_svc
    from services.sales import render as render_svc

    user, tid = pos_api.subject(request)
    ws = pos_api.resolve_ws(user, workspace_client_id)
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace_access(cur, request, tid, ws)
        sale = sales_store.get_sale(cur, tenant_id=tid, workspace_client_id=ws, sale_id=sale_id)
        if not sale or not sale.get("full_invoice_id"):
            raise PosError("pos.product_not_found", 404)
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=str(sale["full_invoice_id"]))
        if not doc:
            raise PosError("pos.product_not_found", 404)
        pdf = render_svc.build_pdf(
            cur,
            tenant_id=tid,
            doc=doc,
            page="A4",
            copy_kind=copy if copy in ("original", "copy") else "original",
        )
    return Response(content=pdf, media_type="application/pdf")
