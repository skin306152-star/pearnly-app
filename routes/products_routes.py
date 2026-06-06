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
from core.auth import get_current_user_from_request
from services.sales import product_import
from services.sales import products as products_dal

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/sales/products", tags=["sales-products"])


def _require_tenant(request: Request) -> str:
    user = get_current_user_from_request(request)
    tid = user.get("tenant_id") if user else None
    if not tid:
        raise HTTPException(400, detail="sales.tenant_required")
    return str(tid)


class ProductCreate(BaseModel):
    name_th: str = Field(..., min_length=1, max_length=300)
    code: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    qr_payload: Optional[str] = Field(None, max_length=500)
    name_en: Optional[str] = Field(None, max_length=300)
    name_zh: Optional[str] = Field(None, max_length=300)
    unit: Optional[str] = Field(None, max_length=50)
    unit_price: float = Field(0, ge=0)
    vat_applicable: bool = True
    image_url: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None


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
    is_active: Optional[bool] = None


def _dump(req) -> dict:
    return req.model_dump() if hasattr(req, "model_dump") else req.dict()


def _out(p: dict) -> dict:
    return {
        "id": str(p["id"]),
        "code": p.get("code"),
        "barcode": p.get("barcode"),
        "qr_payload": p.get("qr_payload"),
        "name_th": p.get("name_th"),
        "name_en": p.get("name_en"),
        "name_zh": p.get("name_zh"),
        "unit": p.get("unit"),
        "unit_price": float(p["unit_price"]) if p.get("unit_price") is not None else 0.0,
        "vat_applicable": bool(p.get("vat_applicable")),
        "image_url": p.get("image_url"),
        "category_id": int(p["category_id"]) if p.get("category_id") is not None else None,
        "is_active": bool(p.get("is_active")),
        "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
        "updated_at": p["updated_at"].isoformat() if p.get("updated_at") else None,
    }


@router.get("")
async def api_list_products(
    request: Request, include_inactive: bool = False, q: Optional[str] = None
):
    tid = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        rows = products_dal.list_products(
            cur, tenant_id=tid, include_inactive=include_inactive, query=q
        )
    return {"products": [_out(r) for r in rows]}


@router.post("")
async def api_create_product(req: ProductCreate, request: Request):
    tid = _require_tenant(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        row = products_dal.create_product(cur, tenant_id=tid, fields=_dump(req))
    return {"ok": True, "product": _out(row)}


@router.get("/lookup")
async def api_lookup_product(
    request: Request,
    code: Optional[str] = None,
    barcode: Optional[str] = None,
    qr: Optional[str] = None,
):
    """按 code/barcode/qr 精确带出在售商品(POS 点单/扫码用)。"""
    tid = _require_tenant(request)
    key, value = next(
        ((k, v) for k, v in (("code", code), ("barcode", barcode), ("qr", qr)) if v),
        (None, None),
    )
    if not key:
        raise HTTPException(400, detail="sales.lookup_key_required")
    with db.get_cursor_rls(tid) as cur:
        row = products_dal.find_by(cur, tenant_id=tid, key=key, value=value)
    if not row:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"product": _out(row)}


@router.post("/import")
async def api_import_products(request: Request, file: UploadFile = File(...)):
    """Excel 批量导入:解析 → 行校验 → 入库可入库行 · 返回入库数 + 行级错误。"""
    tid = _require_tenant(request)
    data = await file.read()
    if not data:
        raise HTTPException(400, detail="sales.empty_file")
    try:
        valid, errors = product_import.parse_workbook(data)
    except ValueError as e:
        raise HTTPException(400, detail=f"sales.import_{e}")
    created = 0
    with db.get_cursor_rls(tid, commit=True) as cur:
        for rec in valid:
            try:
                products_dal.create_product(cur, tenant_id=tid, fields=rec)
                created += 1
            except Exception as e:  # 单行入库失败不连累整批
                logger.warning("[product_import] row insert failed: %s", e)
                errors.append({"row": "?", "error": "db_insert_failed"})
    return {"ok": True, "created": created, "skipped": len(errors), "errors": errors[:100]}


@router.get("/{product_id}")
async def api_get_product(product_id: str, request: Request):
    tid = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        row = products_dal.get_product(cur, tenant_id=tid, product_id=product_id)
    if not row:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"product": _out(row)}


@router.patch("/{product_id}")
async def api_update_product(product_id: str, req: ProductUpdate, request: Request):
    tid = _require_tenant(request)
    raw = {k: v for k, v in _dump(req).items() if v is not None}
    if not raw:
        raise HTTPException(400, detail="sales.no_changes")
    with db.get_cursor_rls(tid, commit=True) as cur:
        row = products_dal.update_product(cur, tenant_id=tid, product_id=product_id, fields=raw)
    if not row:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"ok": True, "product": _out(row)}


@router.delete("/{product_id}")
async def api_delete_product(product_id: str, request: Request):
    tid = _require_tenant(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        ok = products_dal.deactivate_product(cur, tenant_id=tid, product_id=product_id)
    if not ok:
        raise HTTPException(404, detail="sales.product_not_found")
    return {"ok": True}
