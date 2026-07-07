# -*- coding: utf-8 -*-
"""商户采购配置后台路由 · 供应商 / 两级费用科目 / 采购设置(docs/purchasing/02 §5-6)。

平铺页接口(前端导航进页 · 页内动作弹窗)。读=任意成员(录入需选供应商/科目/默认);
写=账号 owner。套账隔离 + expense 模块门控走 routes.purchase_common。薄层:解析上下文 →
开游标(写端 commit)→ 调 services/purchase DAL。统一 POS 信封。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, gate, resolve_ws
from services.erp import mappings_store as erp_mappings
from services.expense import keyword_rules
from services.purchase import categories as cat_svc
from services.purchase import settings as settings_svc
from services.purchase import suppliers as sup_svc

router = APIRouter(prefix="/api/purchase", tags=["purchase-config"])


# ---- 供应商 ------------------------------------------------------------------


class SupplierIn(BaseModel):
    workspace_client_id: Optional[int] = None
    name: str = ""
    tax_id: Optional[str] = None
    branch_type: Optional[str] = None
    branch_no: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    note: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/suppliers")
async def api_list_suppliers(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
):
    _, tid = auth_member(request, "purchase.doc.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = sup_svc.list_suppliers(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            q=q,
            include_inactive=include_inactive,
        )
        return ok({"suppliers": rows})


@router.post("/suppliers")
async def api_create_supplier(req: SupplierIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    if not (req.name or "").strip():
        raise PosError("purchase.line_invalid", 422, detail="name_required")
    if not sup_svc.is_valid_tax_id(req.tax_id):
        raise PosError("purchase.tax_id_invalid", 422)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        row = sup_svc.create_supplier(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            name=req.name,
            tax_id=req.tax_id,
            branch_type=req.branch_type,
            branch_no=req.branch_no,
            address=req.address,
            phone=req.phone,
            note=req.note,
        )
        return ok({"supplier": row})


@router.patch("/suppliers/{supplier_id}")
async def api_update_supplier(supplier_id: str, req: SupplierIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    if req.tax_id is not None and not sup_svc.is_valid_tax_id(req.tax_id):
        raise PosError("purchase.tax_id_invalid", 422)
    fields = req.model_dump(exclude_unset=True, exclude={"workspace_client_id", "is_active"})
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        if req.is_active is not None:
            sup_svc.set_active(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                supplier_id=supplier_id,
                is_active=req.is_active,
            )
        row = sup_svc.update_supplier(
            cur, tenant_id=tid, workspace_client_id=ws, supplier_id=supplier_id, **fields
        )
        if row is None:
            raise PosError("purchase.unexpected", 404)
        return ok({"supplier": row})


@router.delete("/suppliers/{supplier_id}")
async def api_delete_supplier(
    supplier_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "purchase.supplier.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        if (
            sup_svc.doc_count(cur, tenant_id=tid, workspace_client_id=ws, supplier_id=supplier_id)
            > 0
        ):
            raise PosError("purchase.supplier_inactive", 409, detail="has_documents")
        sup_svc.delete_supplier(cur, tenant_id=tid, workspace_client_id=ws, supplier_id=supplier_id)
        return ok({"deleted": True})


# ---- 费用科目(两级)---------------------------------------------------------


class CategoryIn(BaseModel):
    workspace_client_id: Optional[int] = None
    name: str = ""
    parent_id: Optional[str] = None
    sort: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/categories")
async def api_get_categories(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "purchase.doc.view")
    with db.get_cursor_rls(tid, commit=True) as cur:  # commit:首次读懒种子预设
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok({"categories": cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)})


@router.post("/categories")
async def api_create_category(req: CategoryIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        row = cat_svc.create_category(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            name=req.name,
            parent_id=req.parent_id,
            sort=req.sort or 0,
        )
        if row is None:
            raise PosError("purchase.line_invalid", 422, detail="invalid_category")
        return ok({"category": row})


@router.patch("/categories/{category_id}")
async def api_update_category(category_id: str, req: CategoryIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        new_name = (req.name or "").strip()
        old_name = (
            cat_svc.name_of(cur, tenant_id=tid, workspace_client_id=ws, category_id=category_id)
            if new_name
            else None
        )
        row = cat_svc.update_category(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            category_id=category_id,
            name=req.name or None,
            is_active=req.is_active,
            sort=req.sort,
        )
        if row is None:
            raise PosError("purchase.unexpected", 404)
        # 改名连带改 GL 科目映射(name-keyed·不改就断推送科目)· 同事务
        if old_name and new_name and old_name != new_name:
            erp_mappings.rename_category_mapping(cur, tid, old_name, new_name)
        return ok({"category": row})


@router.delete("/categories/{category_id}")
async def api_delete_category(
    category_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "purchase.supplier.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        res = cat_svc.delete_category(
            cur, tenant_id=tid, workspace_client_id=ws, category_id=category_id
        )
        return ok(res)


# ---- 费用识别关键词规则(Phase 2 · 灰度)-------------------------------------


class ExpenseRuleIn(BaseModel):
    workspace_client_id: Optional[int] = None
    target_id: str = ""  # 挂词的科目 id(通常小类)
    keyword: str = ""


@router.get("/expense-rules")
async def api_get_expense_rules(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "purchase.doc.view")
    if not keyword_rules.rules_enabled(tid):
        return ok({"enabled": False, "rules": [], "hits": {}})
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok(
            {
                "enabled": True,
                "rules": keyword_rules.list_rules(cur, tenant_id=tid, workspace_client_id=ws),
                "hits": keyword_rules.hit_counts(cur, tenant_id=tid, workspace_client_id=ws),
            }
        )


@router.post("/expense-rules")
async def api_add_expense_rule(req: ExpenseRuleIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    if not keyword_rules.rules_enabled(tid):
        raise PosError("purchase.unexpected", 403, detail="feature_disabled")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        row = keyword_rules.add_rule(
            cur, tenant_id=tid, workspace_client_id=ws, target_id=req.target_id, keyword=req.keyword
        )
        if row is None:
            raise PosError("purchase.line_invalid", 422, detail="invalid_rule")
        return ok({"rule": row})


@router.delete("/expense-rules")
async def api_delete_expense_rule(req: ExpenseRuleIn, request: Request):
    _, tid = auth_member(request, "purchase.supplier.manage")
    if not keyword_rules.rules_enabled(tid):
        raise PosError("purchase.unexpected", 403, detail="feature_disabled")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        deleted = keyword_rules.delete_rule(
            cur, tenant_id=tid, workspace_client_id=ws, keyword=req.keyword
        )
        return ok({"deleted": deleted})


# ---- 采购设置 ----------------------------------------------------------------


class SettingsIn(BaseModel):
    workspace_client_id: Optional[int] = None
    default_vat_rate: float = Field(7, ge=0, le=100)
    auto_stock_in: bool = False
    dedupe_block: bool = True
    default_due_days: int = Field(0, ge=0)
    pay_needs_approval: bool = False
    default_wht_service_rate: float = Field(3, ge=0, le=100)
    base_currency: str = "THB"
    auto_book: bool = False


@router.get("/settings")
async def api_get_settings(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "purchase.doc.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok(settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws))


@router.put("/settings")
async def api_save_settings(req: SettingsIn, request: Request):
    _, tid = auth_member(request, "purchase.settings.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        return ok(
            settings_svc.save_settings(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                default_vat_rate=req.default_vat_rate,
                auto_stock_in=req.auto_stock_in,
                dedupe_block=req.dedupe_block,
                default_due_days=req.default_due_days,
                pay_needs_approval=req.pay_needs_approval,
                default_wht_service_rate=req.default_wht_service_rate,
                base_currency=req.base_currency,
                auto_book=req.auto_book,
            )
        )
