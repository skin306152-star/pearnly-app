# -*- coding: utf-8 -*-
"""Pearnly AI · 工单制 HTTP API(M1-B1 · 引擎后端化)。

把 M0 的 CLI 发动机接上真后端:开单 / 列表看板 / 详情 / 触发推进 / 人工裁决 / 补料 / 交付包。
全组挂 feature flag `pearnly_ai_m1`(默认关):闸关时一律 404 —— 对存量 Pearnly 用户,这些
路由等于不存在(fail-closed)。租户隔离全走 store.py 既有函数(tenant_id 取自登录态),
每条 {id} 路由都校验工单归属本租户 + 账套作用域(check_workspace_scope,越权 404 防枚举)。

编排细节在 services/workorder/api(无框架内核),后台推进在 services/workorder/runner
(HTTP 不阻塞:/run 交 BackgroundTasks,引擎每步独立事务提交,续跑安全)。
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.feature_flags import pearnly_ai_m1_enabled_for
from core.route_helpers import _tid
from services.authz.deps import check_workspace_scope, require_perm
from services.workorder import api, engine, runner, storage, store
from services.workorder.steps import intake

router = APIRouter()

# 工单 = 在某账套主体上做月度申报工作 → 与「管理账套主体」同权(照 workspace_routes)。
# M1 单用户,owner 短路即过;角色模型落地后(M3)可再拆 acct.entry.view/review。
_PERM = "settings.workspace.manage"

# 补料上限:单文件 20MB 照 bank_recon_routes 的单据上传上限(手机实拍/PDF 远小于此);
# 单次 50 张系本域自定(仓库无多文件计数先例,vat_excel 的 30/1000 是业务条目数非上传数)
# ——一个月的原料一次给全(L2 真语料 104 张)分三批以内传完,又封住恶意万张打爆内存/磁盘。
_MAX_MATERIAL_BYTES = 20 * 1024 * 1024
_MAX_MATERIAL_FILES = 50


class OrderCreate(BaseModel):
    workspace_client_id: int = Field(..., description="账套主体 id")
    period: str = Field(..., min_length=1, max_length=20, description="申报期,如 2569-05")
    intent: str = Field("monthly_vat", max_length=40, description="工单意图(默认月度 VAT)")


class DecisionIn(BaseModel):
    item_id: str = Field(..., description="被裁决的 work_order_item id")
    decision: str = Field(..., description="face_value | recalc | exclude | assign_kind | waive")
    values: Optional[dict] = Field(None, description="recalc 时的人工补正数(如 {vat: '35.00'})")
    kind: Optional[str] = Field(
        None, description="assign_kind 方向裁决:purchase_invoice | sales_doc | non_tax"
    )
    reason: Optional[str] = Field(
        None, max_length=500, description="waive 豁免理由(必填):谁豁免·为何放行出包"
    )


class SalesSummaryIn(BaseModel):
    sales_amount: str = Field(..., max_length=40, description="销项销售额(十进制字符串)")
    output_vat: str = Field(..., max_length=40, description="销项税额(十进制字符串)")
    note: str = Field("", max_length=500, description="凭据备注(人工申报来源)")


def _authorize(request: Request) -> tuple[dict, str]:
    """登录 + M1 闸(关→404 fail-closed)+ 动作权限。返回 (user, tenant_id)。"""
    user = get_current_user_from_request(request)
    tenant_id = _tid(user)
    if not pearnly_ai_m1_enabled_for(tenant_id, str(user["id"])):
        raise HTTPException(404, detail="workorder.not_found")
    require_perm(request, _PERM)
    if not tenant_id:
        raise HTTPException(403, detail="authz.forbidden")
    return user, tenant_id


def _assert_owns_workspace(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (ws_id, tenant_id),
    )
    if not cur.fetchone():
        raise HTTPException(404, detail="workorder.not_found")
    check_workspace_scope(request, user, ws_id)


def _load_order(cur, request: Request, user: dict, tenant_id: str, work_order_id: str) -> dict:
    """取工单 + 校验归属(本租户 + 账套作用域)。越权/不存在一律 404,不泄漏存在性。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise HTTPException(404, detail="workorder.not_found")
    check_workspace_scope(request, user, wo["workspace_client_id"])
    return wo


@router.post("/api/workorder/orders")
async def create_order(req: OrderCreate, request: Request):
    """开单(幂等:同账套同期同意图返既有单)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, req.workspace_client_id)
        wo = api.open_order(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=req.workspace_client_id,
            period=req.period,
            intent=req.intent,
        )
    return {
        "id": wo["id"],
        "workspace_client_id": wo["workspace_client_id"],
        "period": wo["period"],
        "intent": wo["intent"],
        "status": wo["status"],
        "current_step": wo["current_step"],
    }


@router.get("/api/workorder/orders")
async def list_orders(
    request: Request,
    client_id: Optional[int] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """工单列表(按账套/账期/状态筛,倒序分页)。"""
    _user, tenant_id = _authorize(request)
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    with db.get_cursor() as cur:
        return api.list_orders(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=client_id,
            period=period,
            status=status,
            limit=limit,
            offset=offset,
        )


@router.get("/api/workorder/orders/{work_order_id}")
async def get_order(work_order_id: str, request: Request):
    """工单详情:status/current_step + flagged 清单 + needs/停机原因 + 关键数字 + 交付物概览。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        detail = api.order_detail(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if detail is None:
        raise HTTPException(404, detail="workorder.not_found")
    return detail


@router.post("/api/workorder/orders/{work_order_id}/run")
async def run_order(work_order_id: str, request: Request, background: BackgroundTasks):
    """触发推进。HTTP 不阻塞:落 run_requested 事件即返回,真跑交后台(每步独立事务提交)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        wo = _load_order(cur, request, user, tenant_id, work_order_id)
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=runner.RUN_STEP,
            event_type="run_requested",
            actor=f"user:{user['id']}",
        )
    background.add_task(runner.advance, tenant_id, work_order_id)
    return {"queued": True, "status": wo["status"]}


@router.post("/api/workorder/orders/{work_order_id}/decisions")
async def add_decision(work_order_id: str, req: DecisionIn, request: Request):
    """人工裁决(face_value/recalc/exclude),落 human_decision 事件(校验 item 属该单)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        try:
            evt = api.record_decision(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                item_id=req.item_id,
                decision=req.decision,
                values=req.values,
                actor=f"user:{user['id']}",
                kind=req.kind,
                reason=req.reason,
            )
        except api.WorkOrderApiError as e:
            code = 404 if e.code == "workorder.item_not_found" else 422
            raise HTTPException(code, detail=e.code) from e
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/sales-summary")
async def add_sales_summary(work_order_id: str, req: SalesSummaryIn, request: Request):
    """人工填销项(销售额 + 销项税 + 凭据备注)。落 item_classified(sales_summary) 事件,
    reconcile 的 R2 据此解锁(引擎/steps 不改)。金额十进制字符串进出、禁 float、非负。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        try:
            evt = api.record_sales_summary(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                sales_amount=req.sales_amount,
                output_vat=req.output_vat,
                note=req.note,
                actor=f"user:{user['id']}",
            )
        except api.WorkOrderApiError as e:
            code = 422 if e.code.startswith("workorder.sales_summary") else 404
            raise HTTPException(code, detail=e.code) from e
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/materials")
async def add_materials(work_order_id: str, request: Request, files: list[UploadFile] = File(...)):
    """补料:multipart 上传,落盘到工单目录并登记成 work_order_items(走 intake 幂等指纹)。"""
    user, tenant_id = _authorize(request)
    if len(files) > _MAX_MATERIAL_FILES:
        raise HTTPException(413, detail="workorder.too_many_files")
    with db.get_cursor() as cur:  # 先验归属,再落盘(不给未授权请求写磁盘的机会)
        _load_order(cur, request, user, tenant_id, work_order_id)

    saved: list[Path] = []
    for upload in files:
        # 照 uploads_routes 的封顶读法:最多读上限+1 字节,超限即拒,不把超大文件整读进内存。
        content = await upload.read(_MAX_MATERIAL_BYTES + 1)
        if len(content) > _MAX_MATERIAL_BYTES:
            raise HTTPException(413, detail="workorder.file_too_large")
        if not content:
            continue
        suffix = os.path.splitext(upload.filename or "")[1].lower() or ".bin"
        saved.append(storage.save_material(tenant_id, work_order_id, content, suffix))

    registered = []
    with db.get_cursor(commit=True) as cur:
        ctx = engine.StepContext(cur=cur, tenant_id=tenant_id, work_order_id=work_order_id)
        for path in saved:
            item = intake.register_file(ctx, path, "upload")
            registered.append({"item_id": item["id"], "file_ref": item["file_ref"]})
    return {"registered": registered, "count": len(registered)}


@router.get("/api/workorder/orders/{work_order_id}/deliverables")
async def list_order_deliverables(work_order_id: str, request: Request):
    """交付物清单(kind + 关键数字 + 是否有可下载文件)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        return {
            "deliverables": api.list_deliverables(
                cur, tenant_id=tenant_id, work_order_id=work_order_id
            )
        }


@router.get("/api/workorder/orders/{work_order_id}/deliverables/{kind}")
async def download_deliverable(work_order_id: str, kind: str, request: Request):
    """下载单个交付物文件。只放行库里登记过的 artifact_path,再做工单目录内含校验(防穿越)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        artifact = api.deliverable_artifact_path(
            cur, tenant_id=tenant_id, work_order_id=work_order_id, kind=kind
        )
    if not artifact:
        raise HTTPException(404, detail="workorder.deliverable_not_found")
    path = storage.resolve_within_order(tenant_id, work_order_id, artifact)
    if not path:
        raise HTTPException(404, detail="workorder.deliverable_not_found")
    return FileResponse(str(path), filename=path.name)


@router.get("/api/workorder/orders/{work_order_id}/items/{item_id}/image")
async def get_item_image(work_order_id: str, item_id: str, request: Request):
    """审核队列原图直出(W3 契约 §1.2 缺口 A)。与交付物下载同构:只放行该 item 库里
    登记过的 file_ref,再断言落在工单目录内(防穿越);Content-Type 按扩展名给。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        item = store.get_item(
            cur, tenant_id=tenant_id, work_order_id=work_order_id, item_id=item_id
        )
    if not item or not item.get("file_ref"):
        raise HTTPException(404, detail="workorder.item_image_not_found")
    path = storage.resolve_within_order(tenant_id, work_order_id, item["file_ref"])
    if not path:
        raise HTTPException(404, detail="workorder.item_image_not_found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(str(path), media_type=media_type, filename=path.name)
