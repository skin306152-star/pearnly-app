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
from core.feature_flags import pearnly_ai_m1_enabled_for
from core.route_helpers import _tid, _log_op
from services.authz.deps import actor_has_perm, get_authz, require_perm
from services.modules.store import get_business_type
from services.workspace import thai_name_gate

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
    # 账务设置(引导步③ · per-主体)
    fiscal_year_start_month: Optional[int] = Field(
        None, ge=1, le=12, description="财年起始月 1-12(默认 1=日历年)"
    )
    doc_prefix: Optional[str] = Field(
        None, max_length=20, description="单据前缀(空=回落租户级)· 覆盖开票连号前缀"
    )


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
    fiscal_year_start_month: Optional[int] = Field(None, ge=1, le=12, description="财年起始月 1-12")
    doc_prefix: Optional[str] = Field(
        None, max_length=20, description="单据前缀(空串=清空回落租户级)"
    )


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


@router.get("/api/workspace/clients/can-create")
async def can_create_workspace_client(request: Request):
    """员工端"+新建客户"按钮显隐探针(N1-P0-1)。建账套主体挂 settings.workspace.manage
    (owner/admin 专属),客户目录页要在渲染前就知道能不能显示按钮——不给点了才 403 的
    假门(state honesty:按钮存在即承诺可用)。必须放在 /{workspace_client_id} 之前注册,
    否则 "can-create" 会被当成 int 路径参数解析失败(422)。"""
    user = get_current_user_from_request(request)
    return {"allowed": actor_has_perm(request, user, "settings.workspace.manage")}


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
    重试 · 已拼好 name/address/branch_label)。查到即证明该号已注册 VAT → 附
    vat_registered=true;查不到 / 格式错诚实返 {ok:false,error},前端降级为手动填。

    只回主体登记绿卡要的归一字段(不透传 raw_fields 17 字段噪音):
    {tax_id, name, address, branch_no, branch_label, post_code, province, vat_registered}。
    """
    require_perm(request, "settings.workspace.manage")
    from services.rd.rd_api import lookup_vat

    # lookup_vat 是同步阻塞 SOAP(requests · 5s 超时)· 丢线程池跑,别堵 async worker 的 event loop。
    result = await asyncio.to_thread(lookup_vat, tax_id, branch or 0)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or "not_found"}
    src = result.get("data") or {}
    data = {
        "tax_id": src.get("tax_id"),
        "name": src.get("name"),
        "address": src.get("address"),
        "branch_no": src.get("branch_no"),
        "branch_label": src.get("branch_label"),
        "post_code": src.get("post_code"),
        "province": src.get("province"),
        "vat_registered": True,  # 能在 VAT 服务查到 = 已注册 VAT
    }
    return {"ok": True, "data": data, "cached": bool(result.get("cached"))}


def _pos_single_store_blocked(tenant_id: Optional[str]) -> bool:
    """pos_only 且该租户已有 ≥1 个套账 → True(阻止再建)。

    非 pos_only(含 firm)恒 False——判据显式限定 business_type == "pos_only",
    firm/未选业态/其它租户零影响。无 tenant_id(未建档主体)也恒 False,不碰 DB。

    ⚠️ 与 services/pos/entitlements.py 的 pos_entitlements.store_limit 是两套独立机制,
    这里硬编码 >=1,不读 store_limit——Zihao 拍板「一号一店」是固定业务规则(2026-07-12),
    不是「额度内可多店」的软上限。若未来 grant API 开放 store_limit>1(目前无入口暴露),
    此闸仍会卡死第 2 家,须显式改这里,不会自动跟着额度联动。
    """
    if not tenant_id:
        return False
    with db.get_cursor_rls(tenant_id=tenant_id) as cur:
        if get_business_type(cur, tenant_id=tenant_id) != "pos_only":
            return False
        cur.execute(
            "SELECT count(*) AS n FROM workspace_clients WHERE tenant_id = %s",
            (tenant_id,),
        )
        return int((cur.fetchone() or {}).get("n") or 0) >= 1


@router.post("/api/workspace/clients")
async def create_workspace_client(req: WorkspaceClientCreate, request: Request):
    """新建账套主体。仅老板/超管(建账套主体是重大操作 · 区别于建买方)。

    注意:Pearnly 不在 ERP 内自动创建账套公司,这里只是在 Pearnly 侧登记一个工作台
    主体,并可绑定到一个**已存在**的 ERP endpoint。
    """
    user = require_perm(request, "settings.workspace.manage")
    tenant_id = _tid(user)
    # POS 一号一店(Zihao 2026-07-12 拍板):pos_only 已有套账 → 禁止再建(照本文件既有
    # 错误抛法 · HTTPException+detail code · 与下方 tax_id_duplicate 同款,前端 apiClient
    # 读 err.detail 映射四语,不用 PosError 信封)。
    if _pos_single_store_blocked(tenant_id):
        raise HTTPException(403, detail="pos.workspace_single_store")
    # M1-B2:泰文注册名必填(闸关 = 现状不变)——税号被 OCR 读花时,这是分拣方向
    # 判定唯一的名称锚兜底(见 L2-验收.md 真语料坐实)。
    if pearnly_ai_m1_enabled_for(
        tenant_id, str(user["id"])
    ) and not thai_name_gate.has_thai_registered_name(req.name):
        raise HTTPException(
            422, detail=thai_name_gate.error_payload(thai_name_gate.ERR_THAI_NAME_REQUIRED)
        )
    # 企业主体税号在本租户内不得重复(向导步1 杀手锏的边界 · workspace-entry §五)。
    if (
        (req.subject_type or "company") != "personal"
        and (req.tax_id or "").strip()
        and db.tax_id_in_use(str(user["id"]), tenant_id, req.tax_id)
    ):
        raise HTTPException(422, detail="workspace.tax_id_duplicate")
    wid = db.create_workspace_client(
        str(user["id"]),
        tenant_id,
        req.name,
        tax_id=req.tax_id,
        erp_endpoint_id=req.erp_endpoint_id,
        address=req.address,
        branch=req.branch,
        phone=req.phone,
        vat_registered=req.vat_registered if req.vat_registered is not None else True,
        subject_type=req.subject_type,
        fiscal_year_start_month=req.fiscal_year_start_month,
        doc_prefix=req.doc_prefix,
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
    tenant_id = _tid(user)
    raw = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    payload = {k: v for k, v in raw.items() if v is not None}
    if not payload:
        raise HTTPException(400, detail="workspace.no_changes")
    # M1-B2:编辑不许清空已登记的泰文注册名(名称锚兜底不能被悄悄拆掉)。只在
    # 请求真的想改 name 时查一次现状;缺泰文名的存量客户改其它字段不受影响
    # (「存量不炸」——不强制回填,补填引导是 W1 前端另做)。
    if (
        (req.name or "").strip()
        and pearnly_ai_m1_enabled_for(tenant_id, str(user["id"]))
        and not thai_name_gate.has_thai_registered_name(req.name)
    ):
        current = db.get_workspace_client(workspace_client_id, str(user["id"]), tenant_id=tenant_id)
        if current and thai_name_gate.has_thai_registered_name(current.get("name")):
            raise HTTPException(
                422, detail=thai_name_gate.error_payload(thai_name_gate.ERR_THAI_NAME_LOCKED)
            )
    # 改税号时不得撞本租户其它主体(排除自身)。
    if (req.tax_id or "").strip() and db.tax_id_in_use(
        str(user["id"]), tenant_id, req.tax_id, exclude_id=workspace_client_id
    ):
        raise HTTPException(422, detail="workspace.tax_id_duplicate")
    ok = db.update_workspace_client(
        workspace_client_id,
        str(user["id"]),
        tenant_id=tenant_id,
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
