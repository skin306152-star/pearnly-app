# -*- coding: utf-8 -*-
"""Pearnly AI 工单 HTTP API:开单、推进、补料、复核、冻结与交付。
全组受 pearnly_ai_m1 闸保护;租户、工单归属和账套作用域均 fail-closed。
业务编排在 services/workorder/api,后台推进在 services/workorder/runner。
四权分立细码见 C* 常量 + services/workorder/sod.py。
每条 {id} 路由校验工单归属+账套作用域，越权 404 防枚举。
"""

from __future__ import annotations

import logging
import mimetypes
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from core import db
from core.route_helpers import (
    assert_owns_workspace,
    authorize_pearnly_ai,
    content_disposition,
)
from services.audit import file_access as audit_file_access
from services.authz.deps import check_workspace_scope
from services.workorder import api, archive, engine, intake_prep, runner, storage, store
from services.workorder.steps import intake
from routes.workorder_schemas import (
    DecisionIn,
    OrderCreate,
    ReviewSignoffIn,
    SalesSummaryIn,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _client_name_for_order(cur, *, tenant_id: str, user_id: str, workspace_client_id) -> str:
    """交付物/报表下载文件名用的客户名。查不到(异常边缘态)诚实回空串,调用方据此退回落盘原名,不拼一个假名字。"""
    try:
        client = db.get_workspace_client(workspace_client_id, user_id, tenant_id=tenant_id)
        return (client or {}).get("name") or ""
    except Exception:
        return ""


# 工单 = 月度申报工作,四权分立映射到 tax.filing.* 细码(C3):制单/复核/授权/申报/只读
# 各自独立判定,owner/admin 走 all 短路、accountant 全含、clerk 仅制单+只读——一人所全兼
# 零特判(codes 非互斥枚举)。SoD 强制(复核人≠制单人等)按 pearnly_ai_sod 闸叠加,见
# services/workorder/sod.py。
_C_VIEW = "tax.filing.view"
_C_PREPARE = "tax.filing.create"
_C_REVIEW = "tax.filing.review"
_C_APPROVE = "tax.filing.approve"
_C_FILE = "tax.filing.file"

# 补料上限:单文件 20MB 照 bank_recon_routes 的单据上传上限(手机实拍/PDF 远小于此);
# 单次 50 张系本域自定(仓库无多文件计数先例,vat_excel 的 30/1000 是业务条目数非上传数)
# ——一个月的原料一次给全(L2 真语料 104 张)分三批以内传完,又封住恶意万张打爆内存/磁盘。
_MAX_MATERIAL_BYTES = 20 * 1024 * 1024
_MAX_MATERIAL_FILES = 50


def _authorize(request: Request, perm: str) -> tuple[dict, str]:
    """登录 + M1 闸(关→404 fail-closed)+ 动作细码权限。返回 (user, tenant_id)。"""
    return authorize_pearnly_ai(request, perm, not_found="workorder.not_found")


@router.get("/api/ai/session")
async def ai_session(request: Request):
    """AI 壳门禁探针:只跑权限守卫,不触发业务读写。"""
    _authorize(request, _C_VIEW)
    return {"ok": True}


def _assert_owns_workspace(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    assert_owns_workspace(cur, request, user, tenant_id, ws_id, not_found="workorder.not_found")


def _load_order(cur, request: Request, user: dict, tenant_id: str, work_order_id: str) -> dict:
    """取工单 + 校验归属(本租户 + 账套作用域)。越权/不存在一律 404,不泄漏存在性。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        raise HTTPException(404, detail="workorder.not_found")
    check_workspace_scope(request, user, wo["workspace_client_id"])
    return wo


def _load_mutable_order(cur, request: Request, user: dict, tenant_id: str, work_order_id: str):
    """取单 + 冻结只读闸。写端点(run/裁决/补料/填销项/签批)一律走这里,漏挂只读闸在结构上
    不可能;verify/回执/下载/看图等冻结后仍要工作的端点走 _load_order。判定归
    archive.assert_mutable 单一实现(词汇=engine.STATUS_ARCHIVE 权威常量,不手打字符串)。"""
    wo = _load_order(cur, request, user, tenant_id, work_order_id)
    try:
        archive.assert_mutable(wo)
    except api.WorkOrderApiError as e:
        _raise_from_api_error(e)
    return wo


# 冻结/归档相关业务错 → 409(状态冲突);归属类 → 404;其余校验错 → 422。
# SoD(C3):授权人自审/无有效复核在场 = 状态冲突(409);复核人自审(#11)不在此列 → 422
# (它是「这次签批请求不合法」的校验错,不是工单状态冲突)。
_CONFLICT_CODES = {
    "workorder.already_archived",
    "workorder.not_reviewable",
    "workorder.no_deliverables",
    "workorder.freeze_source_missing",
    "workorder.archived_readonly",
    "workorder.not_archived",
    "workorder.sod.approver_is_preparer",
    "workorder.sod.review_required",
    "workorder.run_in_progress",
}


def _raise_from_api_error(e: "api.WorkOrderApiError") -> None:
    if e.code in (
        "workorder.not_found",
        "workorder.item_not_found",
        "workorder.bank_recon_tx_not_found",
        "workorder.bank_sales_row_not_found",
    ):
        raise HTTPException(404, detail=e.code)
    status = 409 if e.code in _CONFLICT_CODES else 422
    detail = {"code": e.code, **e.context} if e.context else e.code
    raise HTTPException(status, detail=detail)


def _schedule_advance(
    background: BackgroundTasks, tenant_id: str, work_order_id: str, user: dict
) -> bool:
    """抢 run 租约 + 落 run_requested + 交后台 advance。抢到返 True(已排后台);抢不到(已有 run 在跑)返 False。

    P-7 引擎自驱:裁决/补料/补销项落库成功后调此,引擎自动续跑,用户不必盯着状态手点 /run。
    实体是 runner.request_run 推进原语(路由/收尸/LINE 回写同一事实源),路由径保留
    BackgroundTasks 派发(响应返回后才起跑)。抢不到租约不是错:已有 run 会带着刚落库的
    新事件续跑(reconcile 从事件流回放),不重复排。"""
    owner = runner.request_run(
        tenant_id, work_order_id, actor=f"user:{user['id']}", background=background
    )
    return owner is not None


def _auto_advance(
    background: BackgroundTasks, tenant_id: str, work_order_id: str, user: dict
) -> None:
    """补料/裁决/补销项后的尽力而为自驱(P-7)。绝不让自驱的意外(租约抖动等)牵连已提交的
    落库结果——用户的裁决/销项已经落库成功,推进失败最多是「还得手点一次 /run」的退化,不能
    让它把一个成功的写操作翻成 5xx。抢不到租约(已有 run 在跑)是正常路径,静默即可。"""
    try:
        _schedule_advance(background, tenant_id, work_order_id, user)
    except Exception:  # noqa: BLE001 - 自驱是增益不是主路径,失败不翻已成功的写
        logger.warning(
            "auto-advance scheduling failed for %s (mutation already committed)", work_order_id
        )


@router.post("/api/workorder/orders")
async def create_order(req: OrderCreate, request: Request):
    """开单(幂等:同账套同期同意图返既有单)。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
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
    _user, tenant_id = _authorize(request, _C_VIEW)
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
    user, tenant_id = _authorize(request, _C_VIEW)
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
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor() as cur:  # 冻结只读闸 + 归属校验先行(读侧),再抢租约推进
        wo = _load_mutable_order(cur, request, user, tenant_id, work_order_id)
    if not _schedule_advance(background, tenant_id, work_order_id, user):
        # 抢不到租约=已有 run 在跑:409 带「正在跑」结构化体(F6 病历:409 无信息像死机)。
        raise HTTPException(409, detail=_run_in_progress_detail(tenant_id, work_order_id))
    return {"queued": True, "status": wo["status"]}


def _run_in_progress_detail(tenant_id: str, work_order_id: str) -> dict:
    """/run 撞租约的结构化体(R1):code + 可轮询工单号 + 当前租约持有者(best-effort;进度/到期由前端轮询 GET /orders/{id} 取,查不到留 None 绝不翻 5xx)。"""
    owner = None
    try:
        with db.get_cursor() as cur:
            holder = store.run_lease_holder(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        owner = (holder or {}).get("run_lease_owner")
    except Exception:  # noqa: BLE001 - 附加进度 best-effort,失败不牵连 409 本身
        logger.warning("run-in-progress lease lookup skipped for %s", work_order_id)
    return {
        "code": "workorder.run_in_progress",
        "work_order_id": work_order_id,
        "run_lease": {"owner": owner} if owner else None,
    }


@router.post("/api/workorder/orders/{work_order_id}/decisions")
async def add_decision(
    work_order_id: str, req: DecisionIn, request: Request, background: BackgroundTasks
):
    """人工裁决(face_value/recalc/exclude),落 human_decision 事件(校验 item 属该单)。
    落库成功后引擎自动续跑(P-7),用户不必手点 /run。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
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
    _auto_advance(background, tenant_id, work_order_id, user)
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/sales-summary")
async def add_sales_summary(
    work_order_id: str, req: SalesSummaryIn, request: Request, background: BackgroundTasks
):
    """人工填销项(销售额 + 销项税 + 凭据备注)。落 item_classified(sales_summary) 事件,
    reconcile 的 R2 据此解锁(引擎/steps 不改)。金额十进制字符串进出、禁 float、非负。
    落库成功后引擎自动续跑(P-7):补销项常是最后一块料,自驱直接把工单带到 review。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
        try:
            evt = api.record_sales_summary(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                sales_amount=req.sales_amount,
                output_vat=req.output_vat,
                note=req.note,
                actor=f"user:{user['id']}",
                source_label=req.source_label,
            )
        except api.WorkOrderApiError as e:
            code = 422 if e.code.startswith("workorder.sales_summary") else 404
            raise HTTPException(code, detail=e.code) from e
    _auto_advance(background, tenant_id, work_order_id, user)
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/materials")
async def add_materials(
    work_order_id: str,
    request: Request,
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    password: Optional[str] = Form(None),
    defer_run: bool = Form(False),
):
    """补料:multipart 上传,预处理(zip/HEIC/密码 PDF/损坏)后落盘并登记成 work_order_items
    (走 intake 幂等指纹)。默认登记后自动续跑；批量投料可 defer_run，收齐后再显式 /run。

    密码 PDF 随传 password 参数即当场解开;不传则 422 pdf_password_required 要密码(密码只用于
    解密,不留存)。整批先读+校验齐全再落盘,任一件不合规=整批拒且盘上零孤儿。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    if len(files) > _MAX_MATERIAL_FILES:
        raise HTTPException(413, detail="workorder.too_many_files")
    with db.get_cursor() as cur:  # 先验归属,再落盘(不给未授权请求写磁盘的机会)
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)

    # 段一:整批读入 + 预处理(不落盘)。封顶读法:最多读上限+1 字节,超限即 413。段内抛错=盘上零残留。
    pairs = []
    for upload in files:
        content = await upload.read(_MAX_MATERIAL_BYTES + 1)
        if len(content) > _MAX_MATERIAL_BYTES:
            raise HTTPException(413, detail="workorder.file_too_large")
        pairs.append((upload.filename, content))
    try:
        prepared = intake_prep.normalize_batch(pairs, password=password)
    except intake_prep.IntakePrepError as e:
        # 结构化 422:{code, message(四语), ...逐件点名 context}。
        raise HTTPException(
            422, detail={"code": e.code, "message": e.message_map(), **e.context}
        ) from e

    # 段二:落盘 + 登记(单事务)。register=False 的是留证原件(HEIC 源),落盘不登记进 items。
    registered = []
    with db.get_cursor(commit=True) as cur:
        ctx = engine.StepContext(cur=cur, tenant_id=tenant_id, work_order_id=work_order_id)
        for nf in prepared:
            path = storage.save_material(
                tenant_id, work_order_id, nf.content, nf.suffix, original_name=nf.original_name
            )
            if not nf.register:
                continue
            item = intake.register_file(ctx, path, "upload")
            if item.get("file_ref") != str(path):
                storage.remove_material(path)  # 去重收敛到既有 item → 清刚落盘的重复件
            registered.append({"item_id": item["id"], "file_ref": item["file_ref"]})
    if registered and defer_run is not True:
        _auto_advance(background, tenant_id, work_order_id, user)
    return {"registered": registered, "count": len(registered)}


@router.get("/api/workorder/orders/{work_order_id}/items/{item_id}/image")
async def get_item_image(work_order_id: str, item_id: str, request: Request):
    """审核队列原图直出(W3 契约 §1.2 缺口 A)。与交付物下载同构:只放行该 item 库里
    登记过的 file_ref,再断言落在工单目录内(防穿越);Content-Type 按扩展名给。"""
    user, tenant_id = _authorize(request, _C_VIEW)
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
    # 落盘密文经 storage.read_bytes 解回明文再出流(FileResponse 会直吐密文,故换 Response)。
    content = storage.read_bytes(path)
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.MATERIAL_VIEWED,
        target_type="workorder_item",
        target_id=item_id,
        details={
            "kind": "material_image",
            "ref": item.get("file_ref"),
            "work_order_id": work_order_id,
        },
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition(download_name, path.name)},
    )


@router.post("/api/workorder/orders/{work_order_id}/review")
async def review_signoff(work_order_id: str, req: ReviewSignoffIn, request: Request):
    """复核签批(C3 四权分立):review 态内落 append-only `review_signoff` 事件,不新增
    状态位。SoD flag 关时人人可签(现状不变);开时复核人不得是制单人(→ 422
    sod.reviewer_is_preparer)。同一复核人重签幂等覆盖(latest-wins)。"""
    user, tenant_id = _authorize(request, _C_REVIEW)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
        try:
            evt = api.record_review_signoff(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                actor=f"user:{user['id']}",
                note=req.note,
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/archive")
async def archive_order(work_order_id: str, request: Request):
    """冻结:review→archive 原子出 freeze_manifest(六要素齐)。冻结后工单只读。

    fail-closed:任一源文件已不在盘 → 409 workorder.freeze_source_missing 并点名(detail.missing);
    非 review 态/已冻结 → 409。签批人=登录 actor;SoD flag 开时授权人不得是制单人且须有
    有效复核在场(services/workorder/sod.py,→ 409 sod.approver_is_preparer/review_required)。"""
    user, tenant_id = _authorize(request, _C_APPROVE)
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
    user, tenant_id = _authorize(request, _C_VIEW)
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
    user, tenant_id = _authorize(request, _C_FILE)
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
