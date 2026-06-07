# -*- coding: utf-8 -*-
"""库存后台路由(POS 项目 · PO-A3 · docs/pos/04 §4)。

薄层:鉴权(信封)+ 模块开关(inventory)+ 账套归属校验 + 调 services/inventory。
统一 POS 信封(ok / PosError);SQL 全在 services/inventory/{store,queries,ledger,fefo}。
owner/会计用;租户隔离走 db.get_cursor_rls + 每条语句 WHERE tenant_id。
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, assert_module_enabled, ok, require_tenant
from services.inventory import ledger, queries, store

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _ctx(request: Request, workspace_client_id: int) -> tuple[str, Optional[str]]:
    """鉴权 + inventory 模块开 + 账套属本租户。返回 (tenant_id, user_id)。"""
    tid, uid = require_tenant(request)
    assert_module_enabled(tid, "inventory")
    return tid, uid


def _require_workspace(cur, tid: str, workspace_client_id: int) -> None:
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tid),
    )
    if not cur.fetchone():
        raise PosError("pos.forbidden", 403)


class InLine(BaseModel):
    product_id: str
    unit_name: Optional[str] = None
    qty: float = Field(..., gt=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    batch_no: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[str] = None


class InRequest(BaseModel):
    workspace_client_id: int
    warehouse_id: Optional[int] = None
    lines: List[InLine] = Field(..., min_length=1)
    ref_type: str = "purchase"
    ref_id: Optional[str] = None
    client_uuid: Optional[str] = None


class CountLine(BaseModel):
    product_id: str
    batch_id: Optional[str] = None
    counted_qty: float = Field(..., ge=0)


class CountRequest(BaseModel):
    workspace_client_id: int
    warehouse_id: Optional[int] = None
    lines: List[CountLine] = Field(..., min_length=1)


class AdjustRequest(BaseModel):
    workspace_client_id: int
    warehouse_id: Optional[int] = None
    product_id: str
    batch_id: Optional[str] = None
    qty_delta: float
    reason: Optional[str] = Field(None, max_length=200)
    client_uuid: Optional[str] = None


def _dump(req) -> dict:
    return req.model_dump() if hasattr(req, "model_dump") else req.dict()


def _resolve_warehouse(cur, tid: str, workspace_client_id: int, warehouse_id: Optional[int]) -> int:
    """给定 warehouse_id 校验归属;未给则取/建账套默认仓。"""
    if warehouse_id is not None:
        if not store.get_warehouse(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id, warehouse_id=warehouse_id
        ):
            raise PosError("pos.forbidden", 403)
        return warehouse_id
    wh = store.get_or_create_default_warehouse(
        cur, tenant_id=tid, workspace_client_id=workspace_client_id
    )
    return wh["id"]


@router.get("/warehouses")
async def api_list_warehouses(request: Request, workspace_client_id: int = Query(...)):
    tid, _ = _ctx(request, workspace_client_id)
    with db.get_cursor_rls(tid, commit=True) as cur:
        _require_workspace(cur, tid, workspace_client_id)
        store.get_or_create_default_warehouse(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id
        )
        rows = store.list_warehouses(cur, tenant_id=tid, workspace_client_id=workspace_client_id)
    return ok({"warehouses": [dict(r) for r in rows]})


@router.get("/stock")
async def api_stock(
    request: Request,
    workspace_client_id: int = Query(...),
    filter: str = Query("all"),
    q: Optional[str] = None,
):
    tid, _ = _ctx(request, workspace_client_id)
    with db.get_cursor_rls(tid) as cur:
        _require_workspace(cur, tid, workspace_client_id)
        data = queries.stock_overview(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id, filter_=filter, q=q
        )
    return ok(data)


@router.get("/near-expiry")
async def api_near_expiry(
    request: Request, workspace_client_id: int = Query(...), days: int = Query(30, ge=0)
):
    tid, _ = _ctx(request, workspace_client_id)
    with db.get_cursor_rls(tid) as cur:
        _require_workspace(cur, tid, workspace_client_id)
        items = queries.near_expiry(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id, days=days
        )
    return ok({"items": items})


@router.post("/in")
async def api_receive(req: InRequest, request: Request):
    tid, uid = _ctx(request, req.workspace_client_id)
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            _require_workspace(cur, tid, req.workspace_client_id)
            wh = _resolve_warehouse(cur, tid, req.workspace_client_id, req.warehouse_id)
            data = ledger.receive(
                cur,
                tenant_id=tid,
                workspace_client_id=req.workspace_client_id,
                warehouse_id=wh,
                lines=[_dump(line) for line in req.lines],
                ref_type=req.ref_type,
                ref_id=req.ref_id,
                client_uuid=req.client_uuid,
                created_by=uid,
            )
    except ledger.InventoryError as e:
        raise PosError(e.code, 422)
    return ok(data)


@router.post("/count")
async def api_count(req: CountRequest, request: Request):
    tid, uid = _ctx(request, req.workspace_client_id)
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            _require_workspace(cur, tid, req.workspace_client_id)
            wh = _resolve_warehouse(cur, tid, req.workspace_client_id, req.warehouse_id)
            data = ledger.count(
                cur,
                tenant_id=tid,
                workspace_client_id=req.workspace_client_id,
                warehouse_id=wh,
                lines=[_dump(line) for line in req.lines],
                created_by=uid,
            )
    except ledger.InventoryError as e:
        raise PosError(e.code, 422)
    return ok(data)


@router.post("/adjust")
async def api_adjust(req: AdjustRequest, request: Request):
    tid, uid = _ctx(request, req.workspace_client_id)
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            _require_workspace(cur, tid, req.workspace_client_id)
            wh = _resolve_warehouse(cur, tid, req.workspace_client_id, req.warehouse_id)
            data = ledger.adjust(
                cur,
                tenant_id=tid,
                workspace_client_id=req.workspace_client_id,
                warehouse_id=wh,
                product_id=req.product_id,
                batch_id=req.batch_id,
                qty_delta=req.qty_delta,
                reason=req.reason,
                client_uuid=req.client_uuid,
                created_by=uid,
            )
    except ledger.InventoryError as e:
        raise PosError(e.code, 422)
    return ok(data)
