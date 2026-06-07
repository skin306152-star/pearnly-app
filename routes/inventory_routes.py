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
from core.pos_api import (
    PosError,
    assert_module_enabled,
    ok,
    require_owner,
    require_tenant,
    require_workspace,
)
from services.inventory import ledger, queries, store

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _read(request: Request, workspace_client_id: int, fn, commit: bool = False):
    """读端骨架:鉴权 → 开游标 → 模块守门 + 账套归属 → fn(cur, tid) → 信封。

    模块守门与业务读用同一游标(不另起连接);GET 需懒建默认仓时传 commit=True。
    """
    tid, _uid = require_tenant(request)
    with db.get_cursor_rls(tid, commit=commit) as cur:
        assert_module_enabled(cur, tid, "inventory")
        require_workspace(cur, tid, workspace_client_id)
        return ok(fn(cur, tid))


def _write(request: Request, req, fn):
    """写端骨架:鉴权(老板/会计 · 收银员 token 不可调库存写)→ 单事务(模块守门 + 账套归属
    + 解析仓 + fn)→ 信封。

    require_owner:库存进货/盘点/调整是后台动作,收银员 token → pos.forbidden(403)(docs/10
    §5.1)。POS 售卖扣库存走服务层(不经此路由),不受影响。
    InventoryError → PosError(422) 收口在此一处(各 handler 不再各写 try/except)。
    """
    tid, uid = require_owner(request)
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            assert_module_enabled(cur, tid, "inventory")
            require_workspace(cur, tid, req.workspace_client_id)
            wh = _resolve_warehouse(cur, tid, req.workspace_client_id, req.warehouse_id)
            return ok(fn(cur, tid, uid, wh))
    except ledger.InventoryError as e:
        raise PosError(e.code, 422)


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
    def _fn(cur, tid):
        store.get_or_create_default_warehouse(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id
        )
        rows = store.list_warehouses(cur, tenant_id=tid, workspace_client_id=workspace_client_id)
        return {"warehouses": [dict(r) for r in rows]}

    return _read(request, workspace_client_id, _fn, commit=True)


@router.get("/stock")
async def api_stock(
    request: Request,
    workspace_client_id: int = Query(...),
    filter: str = Query("all"),
    q: Optional[str] = None,
):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid: queries.stock_overview(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id, filter_=filter, q=q
        ),
    )


@router.get("/near-expiry")
async def api_near_expiry(
    request: Request, workspace_client_id: int = Query(...), days: int = Query(30, ge=0)
):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid: {
            "items": queries.near_expiry(
                cur, tenant_id=tid, workspace_client_id=workspace_client_id, days=days
            )
        },
    )


@router.post("/in")
async def api_receive(req: InRequest, request: Request):
    return _write(
        request,
        req,
        lambda cur, tid, uid, wh: ledger.receive(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            warehouse_id=wh,
            lines=[_dump(line) for line in req.lines],
            ref_type=req.ref_type,
            ref_id=req.ref_id,
            client_uuid=req.client_uuid,
            created_by=uid,
        ),
    )


@router.post("/count")
async def api_count(req: CountRequest, request: Request):
    return _write(
        request,
        req,
        lambda cur, tid, uid, wh: ledger.count(
            cur,
            tenant_id=tid,
            workspace_client_id=req.workspace_client_id,
            warehouse_id=wh,
            lines=[_dump(line) for line in req.lines],
            created_by=uid,
        ),
    )


@router.post("/adjust")
async def api_adjust(req: AdjustRequest, request: Request):
    return _write(
        request,
        req,
        lambda cur, tid, uid, wh: ledger.adjust(
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
        ),
    )
