# -*- coding: utf-8 -*-
"""餐厅 POS 桌台/区域管理路由(POS 项目 · PO-R1 · docs/pos/restaurant/02 §1)。

薄层:require_owner(收银员不可改桌位布局)→ 模块守门(pos)→ 账套归属 → 调 services/pos/restaurant/tables。
统一 POS 信封。写端单事务(get_cursor_rls commit=True)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, assert_module_enabled, ok, pos_auth, require_workspace
from services.pos.restaurant import tables as tables_svc

router = APIRouter(prefix="/api/pos/admin/restaurant", tags=["pos-restaurant-admin"])


def _owner_ctx(request: Request, ws_override: Optional[int]) -> tuple[dict, str, int]:
    user = pos_auth(request)
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("pos.forbidden", 403)
    if user.get("role") == "cashier" and not user.get("is_super_admin"):
        raise PosError("pos.forbidden", 403)  # 桌位布局=老板动作,收银员 403
    ws = user.get("workspace_client_id") or ws_override
    if ws is None:
        raise PosError("pos.forbidden", 403)
    return user, str(tid), int(ws)


def _run(request: Request, ws_override: Optional[int], fn, commit: bool):
    _user, tid, ws = _owner_ctx(request, ws_override)
    with db.get_cursor_rls(tid, commit=commit) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, ws)
        return ok(fn(cur, tid, ws))


# ── 区域 ──────────────────────────────────────────────────────────────
class AreaCreate(BaseModel):
    workspace_client_id: Optional[int] = None
    name: str
    sort: int = 0


class AreaUpdate(BaseModel):
    workspace_client_id: Optional[int] = None
    name: Optional[str] = None
    sort: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/areas")
async def api_list_areas(request: Request, workspace_client_id: Optional[int] = Query(None)):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws: tables_svc.list_areas(cur, tenant_id=tid, workspace_client_id=ws),
        commit=False,
    )


@router.post("/areas")
async def api_create_area(req: AreaCreate, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws: tables_svc.create_area(
            cur, tenant_id=tid, workspace_client_id=ws, name=req.name, sort=req.sort
        ),
        commit=True,
    )


@router.patch("/areas/{area_id}")
async def api_update_area(area_id: int, req: AreaUpdate, request: Request):
    fields = {k: v for k, v in req.model_dump().items() if k not in ("workspace_client_id",)}
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws: tables_svc.update_area(
            cur, tenant_id=tid, workspace_client_id=ws, area_id=area_id, fields=fields
        ),
        commit=True,
    )


@router.delete("/areas/{area_id}")
async def api_delete_area(
    area_id: int, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """删区域(仅空区域;还有桌台 → 409)。"""
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws: tables_svc.delete_area(
            cur, tenant_id=tid, workspace_client_id=ws, area_id=area_id
        ),
        commit=True,
    )


# ── 桌台 ──────────────────────────────────────────────────────────────
class TableCreate(BaseModel):
    workspace_client_id: Optional[int] = None
    name: str
    area_id: Optional[int] = None
    seats: int = Field(4, ge=1)
    sort: int = 0


class TableUpdate(BaseModel):
    workspace_client_id: Optional[int] = None
    name: Optional[str] = None
    area_id: Optional[int] = None
    seats: Optional[int] = Field(None, ge=1)
    sort: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/tables")
async def api_list_tables(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    area_id: Optional[int] = Query(None),
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws: tables_svc.list_tables(
            cur, tenant_id=tid, workspace_client_id=ws, area_id=area_id
        ),
        commit=False,
    )


@router.post("/tables")
async def api_create_table(req: TableCreate, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws: tables_svc.create_table(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            name=req.name,
            area_id=req.area_id,
            seats=req.seats,
            sort=req.sort,
        ),
        commit=True,
    )


@router.patch("/tables/{table_id}")
async def api_update_table(table_id: int, req: TableUpdate, request: Request):
    fields = {k: v for k, v in req.model_dump().items() if k not in ("workspace_client_id",)}
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws: tables_svc.update_table(
            cur, tenant_id=tid, workspace_client_id=ws, table_id=table_id, fields=fields
        ),
        commit=True,
    )


@router.delete("/tables/{table_id}")
async def api_delete_table(
    table_id: int, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """硬删桌台(仅从没开过台的;开过台的留账 → 409 只能停用)。"""
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws: tables_svc.delete_table(
            cur, tenant_id=tid, workspace_client_id=ws, table_id=table_id
        ),
        commit=True,
    )
