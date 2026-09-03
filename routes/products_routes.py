# -*- coding: utf-8 -*-
"""销项商品主数据路由(PO-2 · docs/sales-module/docs/13)。

薄层:鉴权 + 请求整形 + 四态响应;SQL 全在 services/sales/products.py。
商品按 tenant 作用域,租户隔离走 db.get_cursor_rls(写带 commit=True)。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from core import db
from core import workspace_context as wc
from core.route_helpers import translate_unique_violation
from services.authz import field_mask
from services.authz.deps import require_perm_tid
from services.sales import product_import
from services.sales import products as products_dal
from services.products import units as units_dal
from services.products.names import display_product_name

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/sales/products", tags=["sales-products"])


# POS PO-A2 库存地基:base_unit/批次效期/称重/低库存阈值/参考成本(都可空 · 不破既有调用)。
class ProductCreate(BaseModel):
    name_th: str = Field(..., min_length=1, max_length=300)
    code: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    qr_payload: Optional[str] = Field(None, max_length=500)
    name_en: Optional[str] = Field(None, max_length=300)
    name_zh: Optional[str] = Field(None, max_length=300)
    unit: Optional[str] = Field(None, max_length=50)
    # 默认 None 不是 0:带默认 0 时后端永远收不到"没设价",它和真的 ฿0 在库里是同一个值,
    # 收银台的零元闸只拦得住 null —— 于是"扫码→就地建品"建出来的商品全部 ฿0 可售。
    unit_price: Optional[float] = Field(None, ge=0)
    vat_applicable: bool = True
    image_url: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    base_unit: Optional[str] = Field(None, max_length=50)
    track_batch: Optional[bool] = None
    track_expiry: Optional[bool] = None
    is_weighed: Optional[bool] = None
    min_stock: Optional[float] = Field(None, ge=0)
    default_cost: Optional[float] = Field(None, ge=0)


class ProductUpdate(BaseModel):
    name_th: Optional[str] = Field(None, min_length=1, max_length=300)
    code: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    qr_payload: Optional[str] = Field(None, max_length=500)
    name_en: Optional[str] = Field(None, max_length=300)
    name_zh: Optional[str] = Field(None, max_length=300)
    unit: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[float] = Field(None, ge=0)
    vat_applicable: Optional[bool] = None
    image_url: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    base_unit: Optional[str] = Field(None, max_length=50)
    track_batch: Optional[bool] = None
    track_expiry: Optional[bool] = None
    is_weighed: Optional[bool] = None
    min_stock: Optional[float] = Field(None, ge=0)
    default_cost: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class UnitCreate(BaseModel):
    unit_name: str = Field(..., min_length=1, max_length=50)
    factor_to_base: float = Field(..., gt=0)
    barcode: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    is_default_sell: bool = False


class UnitUpdate(BaseModel):
    unit_name: Optional[str] = Field(None, min_length=1, max_length=50)
    factor_to_base: Optional[float] = Field(None, gt=0)
    barcode: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    is_default_sell: Optional[bool] = None


# 一张表上多个唯一键 → 撞哪个报哪个(统一报"编码已存在"= 用户按提示改编码,条码还是重的)。
# 索引名见 alembic 0092/0093 / services.sales.products._BARCODE_UNIQUE_DDL。
# 单位码索引也进商品这张表:重新上架(PATCH is_active=true)和按编码复活都会把单位行的码一起
# 收回来,那一刻码可能已经被别人占了 —— 报"编码已存在"就是撒谎,用户按提示改编码永远改不好。
_PRODUCT_UNIQUE_CODES = {
    "uq_products_tenant_code": "sales.product_code_exists",
    "uq_products_ws_barcode": "sales.product_barcode_exists",
    "uq_product_units_live_barcode": "sales.unit_barcode_exists",
}
_UNIT_UNIQUE_CODES = {"uq_product_units_live_barcode": "sales.unit_barcode_exists"}


def _dump(req) -> dict:
    return req.model_dump() if hasattr(req, "model_dump") else req.dict()


def _patch_fields(req, nullable: set) -> dict:
    """PATCH 语义:只收客户端这次真发过的键(exclude_unset),显式 null = 把这列清空。

    老写法 `{k: v for k, v in _dump(req).items() if v is not None}` 把"这次没传"和"传了 null"
    揉成同一件事,于是「清空条码」静默变成不改还回 ok:true;而上一版为此写的"唯一键留空落
    NULL"分支只在收到空白【字符串】时才生效 —— 前端 readForm() 永远不发空串,那段修复对
    产品是死代码。null 才是"清空"唯一说得清的表达,前后端认这一份。

    nullable 之外的列收到 null 一律当没传:那些是 NOT NULL 列,写下去数据库直接报错,
    拦在这里比让用户吃个 500 说得清。
    """
    sent = (
        req.model_dump(exclude_unset=True)
        if hasattr(req, "model_dump")
        else req.dict(exclude_unset=True)
    )
    return {k: v for k, v in sent.items() if v is not None or k in nullable}


def _out(p: dict, *, cost_visible: bool = True) -> dict:
    return {
        "id": str(p["id"]),
        "code": p.get("code"),
        "barcode": p.get("barcode"),
        "qr_payload": p.get("qr_payload"),
        "name_th": p.get("name_th"),
        "name_en": p.get("name_en"),
        "name_zh": p.get("name_zh"),
        "display_name": display_product_name(p),
        "unit": p.get("unit"),
        # 没设价回 null,不回 0.0:回 0 等于替用户拍板"这货免费",前端就再也画不出
        # "还没定价"这个状态,POS 也分不出该拦谁。四态诚实,数据层是什么就回什么。
        "unit_price": float(p["unit_price"]) if p.get("unit_price") is not None else None,
        "vat_applicable": bool(p.get("vat_applicable")),
        "image_url": p.get("image_url"),
        "category_id": int(p["category_id"]) if p.get("category_id") is not None else None,
        "base_unit": p.get("base_unit"),
        "track_batch": bool(p.get("track_batch")),
        "track_expiry": bool(p.get("track_expiry")),
        "is_weighed": bool(p.get("is_weighed")),
        "min_stock": float(p["min_stock"]) if p.get("min_stock") is not None else None,
        "default_cost": (
            float(p["default_cost"]) if cost_visible and p.get("default_cost") is not None else None
        ),
        "is_active": bool(p.get("is_active")),
        "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
        "updated_at": p["updated_at"].isoformat() if p.get("updated_at") else None,
    }


def _sent_fields(req) -> set[str]:
    fields = getattr(req, "model_fields_set", None)
    if fields is None:
        fields = getattr(req, "__fields_set__", set())
    return set(fields)


def _guard_cost_write(req, request: Request) -> None:
    if "default_cost" in _sent_fields(req) and not field_mask.cost_visible(request):
        raise HTTPException(403, detail="authz.forbidden")


def _unit_out(u: dict) -> dict:
    return {
        "id": str(u["id"]),
        "product_id": str(u["product_id"]),
        "unit_name": u.get("unit_name"),
        "factor_to_base": (
            float(u["factor_to_base"]) if u.get("factor_to_base") is not None else None
        ),
        "barcode": u.get("barcode"),
        "price": float(u["price"]) if u.get("price") is not None else None,
        "is_default_sell": bool(u.get("is_default_sell")),
        "created_at": u["created_at"].isoformat() if u.get("created_at") else None,
        "updated_at": u["updated_at"].isoformat() if u.get("updated_at") else None,
    }


@router.get("")
async def api_list_products(
    request: Request, include_inactive: bool = False, q: Optional[str] = None
):
    tid, _ = require_perm_tid(request, "sales.product.view")
    cost_visible = field_mask.cost_visible(request)
    with db.get_cursor_rls(tid) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        rows = products_dal.list_products(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            include_inactive=include_inactive,
            query=q,
        )
    return {
        "products": [_out(r, cost_visible=cost_visible) for r in rows],
        "cost_visible": cost_visible,
    }


@router.post("")
async def api_create_product(req: ProductCreate, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.manage")
    _guard_cost_write(req, request)
    cost_visible = field_mask.cost_visible(request)
    with (
        db.get_cursor_rls(tid, commit=True) as cur,
        translate_unique_violation("sales.product_code_exists", _PRODUCT_UNIQUE_CODES),
    ):
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        row = products_dal.create_product(
            cur, tenant_id=tid, workspace_client_id=ws, fields=_dump(req)
        )
    return {"ok": True, "product": _out(row, cost_visible=cost_visible)}


@router.get("/lookup")
async def api_lookup_product(
    request: Request,
    code: Optional[str] = None,
    barcode: Optional[str] = None,
    qr: Optional[str] = None,
):
    """按 code/barcode/qr 精确带出在售商品(POS 点单/扫码用)。

    matched_by/matched_unit 随信封回:条码可能配在某个售卖单位上(箱码/瓶码),
    前端要靠它把"这码是 X 商品【箱】的码"说准,不然只能含糊说"已被占用"。
    """
    tid, _ = require_perm_tid(request, "sales.product.view")
    cost_visible = field_mask.cost_visible(request)
    key, value = next(
        ((k, v) for k, v in (("code", code), ("barcode", barcode), ("qr", qr)) if v),
        (None, None),
    )
    if not key:
        raise HTTPException(400, detail="sales.lookup_key_required")
    with db.get_cursor_rls(tid) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        row = products_dal.find_by(cur, tenant_id=tid, workspace_client_id=ws, key=key, value=value)
    if not row:
        raise HTTPException(404, detail="sales.product_not_found")
    return {
        "product": _out(row, cost_visible=cost_visible),
        "matched_by": row.get("matched_by"),
        "matched_unit": row.get("matched_unit"),
    }


@router.post("/import")
async def api_import_products(request: Request, file: UploadFile = File(...)):
    """Excel 批量导入:解析 → 行校验 → 入库可入库行 · 返回入库数 + 行级错误。"""
    tid, _ = require_perm_tid(request, "sales.product.manage")
    data = await file.read()
    if not data:
        raise HTTPException(400, detail="sales.empty_file")
    try:
        valid, errors = product_import.parse_workbook(data)
    except ValueError as e:
        raise HTTPException(400, detail=f"sales.import_{e}")
    created = 0
    with db.get_cursor_rls(tid, commit=True) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        for rec in valid:
            try:
                products_dal.create_product(cur, tenant_id=tid, workspace_client_id=ws, fields=rec)
                created += 1
            except Exception as e:  # 单行入库失败不连累整批
                logger.warning("[product_import] row insert failed: %s", e)
                errors.append({"row": "?", "error": "db_insert_failed"})
    return {"ok": True, "created": created, "skipped": len(errors), "errors": errors[:100]}


@router.get("/{product_id}")
async def api_get_product(product_id: str, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.view")
    cost_visible = field_mask.cost_visible(request)
    with db.get_cursor_rls(tid) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        row = products_dal.get_product(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id
        )
    if not row:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"product": _out(row, cost_visible=cost_visible), "cost_visible": cost_visible}


@router.patch("/{product_id}")
async def api_update_product(product_id: str, req: ProductUpdate, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.manage")
    _guard_cost_write(req, request)
    cost_visible = field_mask.cost_visible(request)
    raw = _patch_fields(req, products_dal.NULLABLE_FIELDS)
    if not raw:
        raise HTTPException(400, detail="sales.no_changes")
    with (
        db.get_cursor_rls(tid, commit=True) as cur,
        translate_unique_violation("sales.product_code_exists", _PRODUCT_UNIQUE_CODES),
    ):
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        row = products_dal.update_product(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id, fields=raw
        )
    if not row:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"ok": True, "product": _out(row, cost_visible=cost_visible)}


@router.delete("/{product_id}")
async def api_delete_product(product_id: str, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        ok = products_dal.deactivate_product(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id
        )
    if not ok:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"ok": True}


# ── 多单位/拆零 product_units(POS PO-A2 · 盒/板/粒 换算)──────────────
@router.get("/{product_id}/units")
async def api_list_units(product_id: str, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.view")
    with db.get_cursor_rls(tid) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        rows = units_dal.list_units(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id
        )
    return {"units": [_unit_out(r) for r in rows]}


@router.post("/{product_id}/units")
async def api_create_unit(product_id: str, req: UnitCreate, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.manage")
    with (
        db.get_cursor_rls(tid, commit=True) as cur,
        translate_unique_violation("sales.unit_name_exists", _UNIT_UNIQUE_CODES),
    ):
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        # 先确认商品属于本租户+本套账(product_id 非租户级 FK · 防挂到他人/别套账商品)。
        if not products_dal.get_product(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id
        ):
            raise HTTPException(404, detail="sales.product_not_found")
        row = units_dal.create_unit(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id, fields=_dump(req)
        )
    return {"ok": True, "unit": _unit_out(row)}


@router.patch("/{product_id}/units/{unit_id}")
async def api_update_unit(product_id: str, unit_id: str, req: UnitUpdate, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.manage")
    raw = _patch_fields(req, units_dal.NULLABLE_UNIT_FIELDS)
    if not raw:
        raise HTTPException(400, detail="sales.no_changes")
    with (
        db.get_cursor_rls(tid, commit=True) as cur,
        translate_unique_violation("sales.unit_name_exists", _UNIT_UNIQUE_CODES),
    ):
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        row = units_dal.update_unit(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            product_id=product_id,
            unit_id=unit_id,
            fields=raw,
        )
    if not row:
        raise HTTPException(404, detail="sales.unit_not_found")
    return {"ok": True, "unit": _unit_out(row)}


@router.delete("/{product_id}/units/{unit_id}")
async def api_delete_unit(product_id: str, unit_id: str, request: Request):
    tid, _ = require_perm_tid(request, "sales.product.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        ok = units_dal.delete_unit(
            cur, tenant_id=tid, workspace_client_id=ws, product_id=product_id, unit_id=unit_id
        )
    if not ok:
        raise HTTPException(404, detail="sales.unit_not_found")
    return {"ok": True}
