# -*- coding: utf-8 -*-
"""供应商过账档案能力层 API(F4 · L2 · 零 UI · docs/purchasing/02)。

中立接口:脸4 政策包管理页与主站复核屏回流共用同一套 DAL(services/purchase/supplier_posting),
本路由只是给"人工管理"开的 CRUD 口子——不挂 pearnly_ai_m1(能力与壳分家),鉴权走主站采购域
权限(与 routes/purchase_config_routes.py 同款 _tid/gate/resolve_ws 范式)。

PUT 一律 source="user_rule"(供应商列表页显式挂的规则,upsert_profile 的 CASE/WHERE 已保证
它不会被自动回流的 correction 覆盖,见 services/purchase/supplier_posting.py)。值域集合从
services/ocr_history/posting_manual.py 同源取,不另抄一份。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, gate, resolve_ws
from services.ocr_history.posting_manual import _ITEM_TYPE_VALUES, _PAYMENT_VALUES
from services.purchase import supplier_posting as sp_svc
from services.purchase.field_clean import clean_tax_id

router = APIRouter(prefix="/api/purchase", tags=["supplier-posting-profiles"])

_PAYMENT_OR_UNSET = _PAYMENT_VALUES | {None}
_ITEM_TYPE_OR_UNSET = _ITEM_TYPE_VALUES | {None}


class SupplierProfileIn(BaseModel):
    workspace_client_id: Optional[int] = None
    default_payment: Optional[str] = None
    default_item_type: Optional[str] = None


@router.get("/supplier-profiles")
async def api_list_supplier_profiles(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=500),
):
    """列表读侧富化(Z3-b):每行带 supplier_name(LEFT JOIN suppliers,查不到给 None,
    前端显示「—」)。走独立读 helper,不动 list_profiles——预取/单票消费两条路无感知。"""
    _, tid = auth_member(request, "purchase.doc.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = sp_svc.list_profiles_with_supplier_names(
            cur, tenant_id=tid, workspace_client_id=ws, limit=limit
        )
        return ok({"profiles": rows})


@router.put("/supplier-profiles/{seller_tax_id}")
async def api_upsert_supplier_profile(seller_tax_id: str, req: SupplierProfileIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    tax = clean_tax_id(seller_tax_id)
    if not tax:
        raise PosError("purchase.tax_id_invalid", 422)
    changed = req.model_dump(exclude_unset=True, exclude={"workspace_client_id"})
    if "default_payment" in changed and changed["default_payment"] not in _PAYMENT_OR_UNSET:
        raise PosError("purchase.line_invalid", 422, detail="default_payment_invalid")
    if "default_item_type" in changed and changed["default_item_type"] not in _ITEM_TYPE_OR_UNSET:
        raise PosError("purchase.line_invalid", 422, detail="default_item_type_invalid")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        sp_svc.upsert_profile(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            seller_tax_id=tax,
            default_payment=changed.get("default_payment"),
            default_item_type=changed.get("default_item_type"),
            source="user_rule",
        )
        row = sp_svc.get_profiles(cur, tenant_id=tid, workspace_client_id=ws, tax_ids=[tax])
        return ok({"profile": row.get(tax)})


@router.delete("/supplier-profiles/{seller_tax_id}")
async def api_delete_supplier_profile(
    seller_tax_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """幂等 no-op:删不存在的税号不报错(与 purchase_config_routes.py 的
    DELETE /expense-rules 同惯例),deleted=False 只是告知调用方"这行本来就不在",不是失败。"""
    _, tid = auth_member(request, "purchase.supplier.manage")
    tax = clean_tax_id(seller_tax_id)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        deleted = sp_svc.delete_profile(
            cur, tenant_id=tid, workspace_client_id=ws, seller_tax_id=tax
        )
        return ok({"deleted": deleted})
