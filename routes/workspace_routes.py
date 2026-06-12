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

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid, _log_op
from services.authz.deps import get_authz, require_perm

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
    subject_type: Optional[str] = Field(None, description="主体类型 company|personal(默认 company)")


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
    subject_type: Optional[str] = Field(None, description="主体类型 company|personal(升级用)")


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
    authz = get_authz(request, user)
    if not user.get("is_super_admin") and authz.scope_mode == "assigned":
        allowed = authz.workspace_ids or frozenset()
        rows = [r for r in rows if int(r.get("id") or 0) in allowed]
    return {"clients": rows, "count": len(rows)}


@router.get("/api/workspace/clients/{workspace_client_id}")
async def get_workspace_client_detail(workspace_client_id: int, request: Request):
    """取单个账套主体完整资料(公司资料页读 · 行内编辑前先拉)。

    tenant 隔离 + 作用域:被分派成员只能读分配给自己的主体(fail-closed),
    越权返 404(不泄漏存在性)。
    """
    user = get_current_user_from_request(request)
    authz = get_authz(request, user)
    if (
        not user.get("is_super_admin")
        and authz.scope_mode == "assigned"
        and not authz.allows_workspace(workspace_client_id)
    ):
        raise HTTPException(404, detail="workspace.not_found")
    client = db.get_workspace_client(workspace_client_id, str(user["id"]), tenant_id=_tid(user))
    if not client:
        raise HTTPException(404, detail="workspace.not_found")
    return {"client": client}


@router.get("/api/workspace/tax-lookup")
async def workspace_tax_lookup(tax_id: str, request: Request, branch: int = 0):
    """按 13 位税号查公司名+地址(建企业主体时自动带出)。仅老板/超管。

    复用 RD VAT 服务(services.rd.rd_api.lookup_vat · 内置 7 天缓存 + 5s 超时 + 1 次
    重试)。查到即证明该号已注册 VAT → 附 vat_registered=true 提示;查不到 / 格式错
    诚实返 {ok:false,error},前端降级为手动填(不阻塞 onboarding)。
    """
    require_perm(request, "settings.workspace.manage")
    from services.rd.rd_api import lookup_vat

    # lookup_vat 是同步阻塞 SOAP(requests · 5s 超时)· 丢线程池跑,别堵 async worker 的 event loop。
    result = await asyncio.to_thread(lookup_vat, tax_id, branch or 0)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or "not_found"}
    data = dict(result.get("data") or {})
    data["vat_registered"] = True
    return {"ok": True, "data": data, "cached": bool(result.get("cached"))}


@router.post("/api/workspace/clients")
async def create_workspace_client(req: WorkspaceClientCreate, request: Request):
    """新建账套主体。仅老板/超管(建账套主体是重大操作 · 区别于建买方)。

    注意:Pearnly 不在 ERP 内自动创建账套公司,这里只是在 Pearnly 侧登记一个工作台
    主体,并可绑定到一个**已存在**的 ERP endpoint。
    """
    user = require_perm(request, "settings.workspace.manage")
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
        subject_type=req.subject_type,
    )
    if not wid:
        raise HTTPException(400, detail="workspace.create_failed")
    _log_op(
        request,
        user,
        "workspace.client.create",
        target_type="workspace_client",
        target_id=str(wid),
        target_name=req.name,
        details={"subject_type": req.subject_type or "company"},
    )
    return {"ok": True, "id": wid}


@router.put("/api/workspace/clients/{workspace_client_id}/endpoint")
async def bind_workspace_endpoint(
    workspace_client_id: int, req: WorkspaceEndpointBind, request: Request
):
    """把账套主体绑定到一个**已有** ERP endpoint(绝不创建 ERP 账套)。仅老板/超管。"""
    user = require_perm(request, "settings.workspace.manage")
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
    user = require_perm(request, "settings.workspace.manage")
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
    _log_op(
        request,
        user,
        "workspace.client.update",
        target_type="workspace_client",
        target_id=str(workspace_client_id),
        details={"fields": sorted(payload.keys())},
    )
    return {"ok": True, "id": workspace_client_id}


@router.delete("/api/workspace/clients/{workspace_client_id}")
async def archive_workspace_client_route(workspace_client_id: int, request: Request):
    """归档账套主体(软删 · is_active=False)。仅老板/超管。

    软删保留发票归属链与 seller 路由记忆,不做硬删。归档后默认列表不显示。
    """
    user = require_perm(request, "settings.workspace.manage")
    ok = db.archive_workspace_client(
        workspace_client_id,
        str(user["id"]),
        tenant_id=_tid(user),
        active=False,
    )
    if not ok:
        raise HTTPException(404, detail="workspace.not_found")
    return {"ok": True}
