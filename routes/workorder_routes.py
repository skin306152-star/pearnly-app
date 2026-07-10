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
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import assert_owns_workspace, authorize_pearnly_ai
from services.authz.deps import check_workspace_scope
from services.workorder import api, archive, engine, runner, storage, store
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
    return authorize_pearnly_ai(request, _PERM, not_found="workorder.not_found")


def _assert_owns_workspace(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    assert_owns_workspace(cur, request, user, tenant_id, ws_id, not_found="workorder.not_found")


def _load_order(cur, request: Request, user: dict, tenant_id: str, work_order_id: str) -> dict:
    """取工单 + 校验归属(本租户 + 账套作用域)。越权/不存在一律 404,不泄漏存在性。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise HTTPException(404, detail="workorder.not_found")
    check_workspace_scope(request, user, wo["workspace_client_id"])
    return wo


def _assert_mutable(wo: dict) -> None:
    """冻结(archive)后工单只读:拒绝重跑/裁决/补料/填销项(唯回执可 append-only 补挂)。"""
    if wo.get("status") == "archive":
        raise HTTPException(409, detail="workorder.archived_readonly")


# 冻结/归档相关业务错 → 409(状态冲突);归属类 → 404;其余校验错 → 422。
_CONFLICT_CODES = {
    "workorder.already_archived",
    "workorder.not_reviewable",
    "workorder.no_deliverables",
    "workorder.freeze_source_missing",
    "workorder.archived_readonly",
    "workorder.not_archived",
}


def _raise_from_api_error(e: "api.WorkOrderApiError") -> None:
    if e.code in ("workorder.not_found", "workorder.item_not_found"):
        raise HTTPException(404, detail=e.code)
    status = 409 if e.code in _CONFLICT_CODES else 422
    detail = {"code": e.code, **e.context} if e.context else e.code
    raise HTTPException(status, detail=detail)


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
    """触发推进。HTTP 不阻塞:抢 running 租约防重入,落 run_requested 事件即返回,真跑交后台。

    双终端/双击同时 /run:先抢 DB 租约,抢不到(他人未过期租约占着)→ 409 run_in_progress;
    抢到者把 owner 交后台 advance,收尾释放。进程猝死则租约过期后另一终端可接管。"""
    user, tenant_id = _authorize(request)
    owner = f"run:{uuid.uuid4().hex}"
    store.ensure_runtime()  # 建租约列(独立事务)· 必须先于下面 SELECT/UPDATE 锁 work_orders
    with db.get_cursor(commit=True) as cur:
        wo = _load_order(cur, request, user, tenant_id, work_order_id)
        _assert_mutable(wo)  # 冻结后只读:拒绝重跑
        if not store.acquire_run_lease(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            owner=owner,
            ttl_seconds=runner.run_lease_ttl_seconds(),
        ):
            raise HTTPException(409, detail="workorder.run_in_progress")
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=runner.RUN_STEP,
            event_type="run_requested",
            actor=f"user:{user['id']}",
        )
    background.add_task(runner.advance, tenant_id, work_order_id, owner)
    return {"queued": True, "status": wo["status"]}


@router.post("/api/workorder/orders/{work_order_id}/decisions")
async def add_decision(work_order_id: str, req: DecisionIn, request: Request):
    """人工裁决(face_value/recalc/exclude),落 human_decision 事件(校验 item 属该单)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        _assert_mutable(_load_order(cur, request, user, tenant_id, work_order_id))
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
        _assert_mutable(_load_order(cur, request, user, tenant_id, work_order_id))
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
        _assert_mutable(_load_order(cur, request, user, tenant_id, work_order_id))

    saved: list[Path] = []
    for upload in files:
        # 照 uploads_routes 的封顶读法:最多读上限+1 字节,超限即拒,不把超大文件整读进内存。
        content = await upload.read(_MAX_MATERIAL_BYTES + 1)
        if len(content) > _MAX_MATERIAL_BYTES:
            raise HTTPException(413, detail="workorder.file_too_large")
        if not content:
            continue
        suffix = os.path.splitext(upload.filename or "")[1].lower() or ".bin"
        saved.append(
            storage.save_material(
                tenant_id, work_order_id, content, suffix, original_name=upload.filename
            )
        )

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
    # 下载名还原用户原始文件名:优先无损列 original_name,空回落落盘名反解,审核看图不再是 uuid。
    download_name = (
        item.get("original_name") or storage.original_name_of(item.get("file_ref")) or path.name
    )
    return FileResponse(str(path), media_type=media_type, filename=download_name)


@router.post("/api/workorder/orders/{work_order_id}/archive")
async def archive_order(work_order_id: str, request: Request):
    """冻结:review→archive 原子出 freeze_manifest(六要素齐)。冻结后工单只读。

    fail-closed:任一源文件已不在盘 → 409 workorder.freeze_source_missing 并点名(detail.missing);
    非 review 态/已冻结 → 409。签批人=登录 actor(单一 actor,多角色审批属 C3)。"""
    user, tenant_id = _authorize(request)
    store.ensure_runtime()  # 建 version/original_name 列(独立事务·先于锁工单表的 txn)
    with db.get_cursor(commit=True) as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        try:
            out = archive.archive_order(
                cur, tenant_id=tenant_id, work_order_id=work_order_id, actor=f"user:{user['id']}"
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    return {"ok": True, **out}


@router.get("/api/workorder/orders/{work_order_id}/verify")
async def verify_order(work_order_id: str, request: Request):
    """篡改校验:逐 item 现算源文件 sha256 与冻结 manifest 比对(未冻结 → 409 not_archived)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        try:
            return archive.verify_manifest(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)


@router.post("/api/workorder/orders/{work_order_id}/receipt")
async def attach_receipt(work_order_id: str, request: Request, file: UploadFile = File(...)):
    """申报回执补挂(append-only):冻结后唯一可写路径,落 receipt_attached 事件(带回执哈希),
    不改已冻 manifest 本体。仅归档态可挂。"""
    user, tenant_id = _authorize(request)
    content = await file.read(_MAX_MATERIAL_BYTES + 1)
    if len(content) > _MAX_MATERIAL_BYTES:
        raise HTTPException(413, detail="workorder.file_too_large")
    if not content:
        raise HTTPException(422, detail="workorder.receipt_empty")
    with db.get_cursor(commit=True) as cur:
        _load_order(cur, request, user, tenant_id, work_order_id)
        try:
            out = archive.attach_receipt(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                content=content,
                original_name=file.filename,
                actor=f"user:{user['id']}",
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    return {"ok": True, **out}
