# -*- coding: utf-8 -*-
"""
Pearnly · ERP 映射底座路由模块(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

v118.27.0 · ERP 映射底座(客户 / 科目 / 税码 / 商品 4 个 sub-tab · 12 路由):
  GET    /api/erp/mappings/clients               · 列客户映射(接员工分配过滤)
  POST   /api/erp/mappings/clients               · upsert 客户映射(owner/super)
  DELETE /api/erp/mappings/clients/{mapping_id}   · 删客户映射(owner/super)
  GET    /api/erp/mappings/accounts              · 列科目映射(tenant 共享)
  POST   /api/erp/mappings/accounts              · upsert 科目映射(owner/super)
  DELETE /api/erp/mappings/accounts/{mapping_id}  · 删科目映射(owner/super)
  GET    /api/erp/mappings/taxes                 · 列税码映射(tenant 共享)
  POST   /api/erp/mappings/taxes                 · upsert 税码映射(owner/super)
  DELETE /api/erp/mappings/taxes/{mapping_id}     · 删税码映射(owner/super)
  GET    /api/erp/mappings/products              · 列商品映射(owner/super · erp_type 过滤)
  POST   /api/erp/mappings/products              · upsert 商品映射(owner/super)
  DELETE /api/erp/mappings/products/{mapping_id}  · 删商品映射(owner/super)

权限(原样保留):
  - 客户映射:接 client_assignments filter(员工只看自己客户)· GET 全员可调
  - 科目/税码映射:tenant 共享 · GET 全员可调
  - POST/DELETE 全部要 _require_owner_or_super(老板/超管才能改)
  - 商品映射:GET/POST/DELETE 都自查 role==owner or is_super_admin

依赖:
  - db.*(ERP 映射 CRUD + get_visible_client_ids_for_user)
  - auth.get_current_user_from_request
  - route_helpers._require_owner_or_super
  - _tid:app.py 也有同名 helper · 这里复制一份防循环 import
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _require_owner_or_super

router = APIRouter()


def _tid(user: dict) -> Optional[str]:
    """多租户共享:返回用户 tenant_id 字符串(app.py 同名 helper · 复制防循环 import)"""
    if not user:
        return None
    tid = user.get("tenant_id")
    return str(tid) if tid else None


# ─── 客户映射 ────────────────────────────────────────────
@router.get("/api/erp/mappings/clients")
async def erp_map_list_clients(request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        return {"items": []}
    visible = db.get_visible_client_ids_for_user(user)
    rows = db.list_erp_client_mappings(tid, restrict_client_ids=visible)
    return {"items": rows, "count": len(rows)}


@router.post("/api/erp/mappings/clients")
async def erp_map_upsert_client(request: Request):
    owner = _require_owner_or_super(request)
    body = await request.json()
    cid = body.get("client_id")
    erp_type = body.get("erp_type")
    erp_code = body.get("erp_code")
    notes = body.get("notes") or ""
    if not cid or not erp_type or not erp_code:
        raise HTTPException(400, detail="erp_map.missing_fields")
    new_id = db.upsert_erp_client_mapping(
        str(owner["tenant_id"]), int(cid), erp_type, erp_code, notes, str(owner["id"])
    )
    if not new_id:
        raise HTTPException(400, detail="erp_map.upsert_failed")
    return {"ok": True, "id": new_id}


@router.delete("/api/erp/mappings/clients/{mapping_id}")
async def erp_map_delete_client(mapping_id: str, request: Request):
    owner = _require_owner_or_super(request)
    ok = db.delete_erp_client_mapping(str(owner["tenant_id"]), mapping_id)
    if not ok:
        raise HTTPException(404, detail="erp_map.not_found")
    return {"ok": True}


# ─── 科目映射 ────────────────────────────────────────────
@router.get("/api/erp/mappings/accounts")
async def erp_map_list_accounts(request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        return {"items": []}
    rows = db.list_erp_account_mappings(tid)
    return {"items": rows, "count": len(rows)}


@router.post("/api/erp/mappings/accounts")
async def erp_map_upsert_account(request: Request):
    owner = _require_owner_or_super(request)
    body = await request.json()
    erp_type = body.get("erp_type")
    cat = body.get("pearnly_category")
    code = body.get("erp_code")
    name = body.get("erp_name") or ""
    notes = body.get("notes") or ""
    if not erp_type or not cat or not code:
        raise HTTPException(400, detail="erp_map.missing_fields")
    new_id = db.upsert_erp_account_mapping(
        str(owner["tenant_id"]), erp_type, cat, code, name, notes, str(owner["id"])
    )
    if not new_id:
        raise HTTPException(400, detail="erp_map.upsert_failed")
    return {"ok": True, "id": new_id}


@router.delete("/api/erp/mappings/accounts/{mapping_id}")
async def erp_map_delete_account(mapping_id: str, request: Request):
    owner = _require_owner_or_super(request)
    ok = db.delete_erp_account_mapping(str(owner["tenant_id"]), mapping_id)
    if not ok:
        raise HTTPException(404, detail="erp_map.not_found")
    return {"ok": True}


# ─── 税码映射 ────────────────────────────────────────────
@router.get("/api/erp/mappings/taxes")
async def erp_map_list_taxes(request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        return {"items": []}
    rows = db.list_erp_tax_mappings(tid)
    return {"items": rows, "count": len(rows)}


@router.post("/api/erp/mappings/taxes")
async def erp_map_upsert_tax(request: Request):
    owner = _require_owner_or_super(request)
    body = await request.json()
    erp_type = body.get("erp_type")
    kind = body.get("pearnly_tax_kind")
    code = body.get("erp_code")
    notes = body.get("notes") or ""
    if not erp_type or not kind or not code:
        raise HTTPException(400, detail="erp_map.missing_fields")
    new_id = db.upsert_erp_tax_mapping(
        str(owner["tenant_id"]), erp_type, kind, code, notes, str(owner["id"])
    )
    if not new_id:
        raise HTTPException(400, detail="erp_map.upsert_failed")
    return {"ok": True, "id": new_id}


@router.delete("/api/erp/mappings/taxes/{mapping_id}")
async def erp_map_delete_tax(mapping_id: str, request: Request):
    owner = _require_owner_or_super(request)
    ok = db.delete_erp_tax_mapping(str(owner["tenant_id"]), mapping_id)
    if not ok:
        raise HTTPException(404, detail="erp_map.not_found")
    return {"ok": True}


# ─── 商品映射 CRUD ──────────────────────────────────────────


class ErpProductMappingReq(BaseModel):
    erp_type: str
    item_name: str
    erp_code: str
    erp_name: Optional[str] = None
    notes: Optional[str] = None


@router.get("/api/erp/mappings/products")
async def list_mappings_products(request: Request, erp_type: str = ""):
    """列商品映射 · 可选 erp_type 过滤 · 默认列全部"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        raise HTTPException(400, detail="no_tenant")
    role = (user.get("role") or "owner").lower()
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="owner_only")
    rows = db.list_erp_product_mappings(tid, erp_type=(erp_type.strip() or None))
    out = []
    for r in rows:
        out.append(
            {
                "id": str(r.get("id")) if r.get("id") else None,
                "erp_type": r.get("erp_type"),
                "item_name": r.get("item_name"),
                "erp_code": r.get("erp_code"),
                "erp_name": r.get("erp_name"),
                "notes": r.get("notes"),
                "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
                "updated_at": r.get("updated_at").isoformat() if r.get("updated_at") else None,
            }
        )
    return {"ok": True, "items": out, "total": len(out)}


@router.post("/api/erp/mappings/products")
async def upsert_mapping_product(req: ErpProductMappingReq, request: Request):
    """加/改商品映射"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        raise HTTPException(400, detail="no_tenant")
    role = (user.get("role") or "owner").lower()
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="owner_only")
    mid = db.upsert_erp_product_mapping(
        tenant_id=tid,
        erp_type=req.erp_type,
        item_name=req.item_name,
        erp_code=req.erp_code,
        erp_name=req.erp_name,
        notes=req.notes,
        user_id=str(user["id"]),
    )
    if not mid:
        raise HTTPException(400, detail="upsert_failed")
    return {"ok": True, "id": mid}


@router.delete("/api/erp/mappings/products/{mapping_id}")
async def delete_mapping_product(mapping_id: str, request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        raise HTTPException(400, detail="no_tenant")
    role = (user.get("role") or "owner").lower()
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="owner_only")
    ok = db.delete_erp_product_mapping(tid, mapping_id)
    return {"ok": bool(ok)}
