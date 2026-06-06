# -*- coding: utf-8 -*-
"""开票方(卖方=账套主体)资料路由(PO-6 · docs/sales-module/docs/13)。

账套主体(workspace_clients)= 在为哪家公司做账 = 开票时的卖方。这里读/写它的开票
字段(法定名称/税号/地址/总分公司/电话/是否注册 VAT),开票选账套即带出卖方块。
薄层:鉴权 + 整形;SQL 在 services/sales/seller_profile.py。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from services.sales import seller_profile

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/sales/sellers", tags=["sales-sellers"])


def _require_tenant(request: Request) -> str:
    user = get_current_user_from_request(request)
    tid = user.get("tenant_id") if user else None
    if not tid:
        raise HTTPException(400, detail="sales.tenant_required")
    return str(tid)


class SellerProfileIn(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    branch: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=50)
    vat_registered: Optional[bool] = None
    promptpay_id: Optional[str] = Field(None, max_length=40, description="PromptPay 代理 · §L1")
    # 品牌/模板(§L4):账套级,渲染套到每张票。
    template_id: Optional[str] = Field(None, max_length=40)
    brand_color: Optional[str] = Field(None, max_length=9)
    logo_url: Optional[str] = Field(None, max_length=500)
    seal_url: Optional[str] = Field(None, max_length=500)
    signature_url: Optional[str] = Field(None, max_length=500)
    footer_text: Optional[str] = Field(None, max_length=500)


def _out(s: dict) -> dict:
    return {
        "id": int(s["id"]),
        "name": s.get("name"),
        "tax_id": s.get("tax_id"),
        "address": s.get("address"),
        "branch": s.get("branch"),
        "phone": s.get("phone"),
        "vat_registered": bool(s.get("vat_registered")),
        "promptpay_id": s.get("promptpay_id"),
        "template_id": s.get("template_id"),
        "brand_color": s.get("brand_color"),
        "logo_url": s.get("logo_url"),
        "seal_url": s.get("seal_url"),
        "signature_url": s.get("signature_url"),
        "footer_text": s.get("footer_text"),
    }


@router.get("")
async def api_list_sellers(request: Request):
    tid = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        rows = seller_profile.list_sellers(cur, tenant_id=tid)
    return {"sellers": [_out(r) for r in rows]}


@router.get("/{workspace_client_id}")
async def api_get_seller(workspace_client_id: int, request: Request):
    tid = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        row = seller_profile.get_seller(cur, tenant_id=tid, workspace_client_id=workspace_client_id)
    if not row:
        raise HTTPException(404, detail="sales.seller_not_found")
    return {"seller": _out(row)}


@router.put("/{workspace_client_id}")
async def api_set_seller(workspace_client_id: int, req: SellerProfileIn, request: Request):
    tid = _require_tenant(request)
    fields = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    with db.get_cursor_rls(tid, commit=True) as cur:
        row = seller_profile.set_seller(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id, fields=fields
        )
    if not row:
        raise HTTPException(404, detail="sales.seller_not_found")
    return {"ok": True, "seller": _out(row)}
