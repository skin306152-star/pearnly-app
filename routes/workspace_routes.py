# -*- coding: utf-8 -*-
"""Pearnly · workspace_clients(账套主体 / 工作台归属)路由 · B4 非破坏版(2026-05-25)

概念:workspace_client = "在为哪家公司做账"(账套主体 / 权限范围 / 用哪个 ERP 账套)。
与发票买方(history.client_id → MR.ERP 应收客户)是两回事(见 B0)。

本版**非破坏**:
  - 只新增 /api/workspace/* 只读+管理接口;
  - 不改任何上传/推送/对账主路径;
  - 不强制校验(B1)、不弹登录窗(B2)—— 那两步等 Codex 验收后由 Zihao 确认上线;
  - 旧 ClientSwitcher / clients 路由保持不动,workspace 切换器作为并行能力。

依赖:db.* (re-export 自 services/workspace/store.py · B0) + auth + route_helpers。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid, _require_owner_or_super

router = APIRouter()


class WorkspaceClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="账套主体公司名")
    tax_id: Optional[str] = Field(None, description="税号(可选)")
    erp_endpoint_id: Optional[str] = Field(None, description="绑定的已有 ERP endpoint id(可选)")
    # 开票方资料(销项 PO-6 · 出合规税票用)
    address: Optional[str] = Field(None, max_length=500, description="地址")
    branch: Optional[str] = Field(None, max_length=120, description="总公司/分公司")
    phone: Optional[str] = Field(None, max_length=50, description="电话")
    vat_registered: Optional[bool] = Field(None, description="是否注册 VAT")


class WorkspaceEndpointBind(BaseModel):
    erp_endpoint_id: Optional[str] = Field(
        None, description="要绑定的已有 ERP endpoint id;None=解绑"
    )


class WorkspaceClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="账套主体公司名")
    tax_id: Optional[str] = Field(None, description="税号(可选 · 空串=清空)")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    branch: Optional[str] = Field(None, max_length=120, description="总公司/分公司")
    phone: Optional[str] = Field(None, max_length=50, description="电话")
    vat_registered: Optional[bool] = Field(None, description="是否注册 VAT")


@router.get("/api/workspace/clients")
async def list_workspace_clients(request: Request, include_inactive: bool = False):
    """列出当前用户可见的账套主体(带发票统计 · 客户管理页用)。

    非破坏版:老板/超管看本租户全部。员工按分配过滤(restrict)留给 B3 接入 ——
    此处先不限制,避免在 B3 落地前误伤;员工可见范围最终由 B3 client_assignments 决定。
    include_inactive=True 时连归档的也返回(管理页「已归档」筛选用)。
    """
    user = get_current_user_from_request(request)
    rows = db.list_workspace_clients_enriched(
        str(user["id"]), tenant_id=_tid(user), active_only=not include_inactive
    )
    return {"clients": rows, "count": len(rows)}


@router.post("/api/workspace/clients")
async def create_workspace_client(req: WorkspaceClientCreate, request: Request):
    """新建账套主体。仅老板/超管(建账套主体是重大操作 · 区别于建买方)。

    注意:Pearnly 不在 ERP 内自动创建账套公司,这里只是在 Pearnly 侧登记一个工作台
    主体,并可绑定到一个**已存在**的 ERP endpoint。
    """
    user = _require_owner_or_super(request)
    wid = db.create_workspace_client(
        str(user["id"]),
        _tid(user),
        req.name,
        tax_id=req.tax_id,
        erp_endpoint_id=req.erp_endpoint_id,
        address=req.address,
        branch=req.branch,
        phone=req.phone,
        vat_registered=req.vat_registered if req.vat_registered is not None else True,
    )
    if not wid:
        raise HTTPException(400, detail="workspace.create_failed")
    return {"ok": True, "id": wid}


@router.put("/api/workspace/clients/{workspace_client_id}/endpoint")
async def bind_workspace_endpoint(
    workspace_client_id: int, req: WorkspaceEndpointBind, request: Request
):
    """把账套主体绑定到一个**已有** ERP endpoint(绝不创建 ERP 账套)。仅老板/超管。"""
    user = _require_owner_or_super(request)
    ok = db.bind_workspace_endpoint(
        workspace_client_id,
        req.erp_endpoint_id,
        str(user["id"]),
        tenant_id=_tid(user),
    )
    if not ok:
        raise HTTPException(404, detail="workspace.not_found")
    return {"ok": True}


@router.patch("/api/workspace/clients/{workspace_client_id}")
async def update_workspace_client_route(
    workspace_client_id: int, req: WorkspaceClientUpdate, request: Request
):
    """改账套主体名称/税号。仅老板/超管(账套主体是重大主体 · 与改买方不同)。"""
    user = _require_owner_or_super(request)
    raw = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    payload = {k: v for k, v in raw.items() if v is not None}
    if not payload:
        raise HTTPException(400, detail="workspace.no_changes")
    ok = db.update_workspace_client(
        workspace_client_id,
        str(user["id"]),
        tenant_id=_tid(user),
        **payload,
    )
    if not ok:
        raise HTTPException(404, detail="workspace.not_found")
    return {"ok": True, "id": workspace_client_id}


@router.delete("/api/workspace/clients/{workspace_client_id}")
async def archive_workspace_client_route(workspace_client_id: int, request: Request):
    """归档账套主体(软删 · is_active=False)。仅老板/超管。

    软删保留发票归属链与 seller 路由记忆,不做硬删。归档后默认列表不显示。
    """
    user = _require_owner_or_super(request)
    ok = db.archive_workspace_client(
        workspace_client_id,
        str(user["id"]),
        tenant_id=_tid(user),
        active=False,
    )
    if not ok:
        raise HTTPException(404, detail="workspace.not_found")
    return {"ok": True}
