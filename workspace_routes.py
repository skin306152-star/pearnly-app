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

import db
from auth import get_current_user_from_request
from route_helpers import _tid, _require_owner_or_super

router = APIRouter()


class WorkspaceClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="账套主体公司名")
    tax_id: Optional[str] = Field(None, description="税号(可选)")
    erp_endpoint_id: Optional[str] = Field(None, description="绑定的已有 ERP endpoint id(可选)")


class WorkspaceEndpointBind(BaseModel):
    erp_endpoint_id: Optional[str] = Field(
        None, description="要绑定的已有 ERP endpoint id;None=解绑"
    )


@router.get("/api/workspace/clients")
async def list_workspace_clients(request: Request):
    """列出当前用户可见的账套主体。

    非破坏版:老板/超管看本租户全部。员工按分配过滤(restrict)留给 B3 接入 ——
    此处先不限制,避免在 B3 落地前误伤;员工可见范围最终由 B3 client_assignments 决定。
    """
    user = get_current_user_from_request(request)
    rows = db.list_workspace_clients(str(user["id"]), tenant_id=_tid(user))
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
