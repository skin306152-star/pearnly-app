# -*- coding: utf-8 -*-
"""
对账异步任务 · submit + 状态查询路由(ADR-005 · #15 · BUG-FIX-RECON-ASYNC)。

加性改造(铁律 #17/#23:新路由进 *_routes.py · 不进 app.py):
  - 老的 /api/recon/bank-v2/run、/gl-vat/run、/api/vat_excel/build 同步接口**保持不动**
    (现前端仍在用 · #16 前端切到 submit 后它们才退役)。
  - 这里只新增 submit(秒回 job_id)+ 统一状态查询接口。

submit 流程(ADR-005 §4.2):鉴权 + 校验 + credits 前置检查 → 落盘暂存 → 建 job → 秒回。
重活由后台工人按 job_type 分发到 services/recon_jobs/handlers.py 跑(结果写现有结果表)。

暂存:文件写到 STAGE_DIR/<job_id>/(job_id 预生成 · 工人完成后按同一 id 清理)。
状态:GET /api/recon/jobs/{id} → {status, progress, result_table, result_id, error_code}。
       前端据 result_table/result_id 调现有结果接口渲染/下载(渲染/导出代码不动)。
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from core import db
from core import workspace_context as wc
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from services.recon_jobs import store, worker

logger = logging.getLogger("recon_jobs.routes")
router = APIRouter(tags=["recon-jobs"])


def _user_key(user) -> str:
    # 回退兼容服务器两种环境变量名(OCR 历史上 GEMINI_API_KEY / GOOGLE_API_KEY 混用)
    # → S7 AI 在生产不管服务器配哪个都能拿到 key · 否则静默退回 needs_mapping
    return (
        (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )


async def _stage_uploads(job_id: str, files: List[UploadFile], role: str, default_name: str):
    """把上传文件落盘到 STAGE_DIR/<job_id>/ · 返回 input_ref 片段。"""
    stage_dir = worker.stage_dir_for(job_id)
    os.makedirs(stage_dir, exist_ok=True)
    refs = []
    for i, f in enumerate(files):
        content = await f.read()
        fname = f.filename or f"{default_name}_{i}"
        # 落盘名加序号防同名覆盖 · input_ref 里保留原始 filename 供解析/展示
        disk_name = f"{role}_{i}_{os.path.basename(fname)}"
        path = os.path.join(stage_dir, disk_name)
        with open(path, "wb") as out:
            out.write(content)
        refs.append({"path": path, "filename": fname, "role": role})
    return refs


def _credits_precheck(user_id: str, tenant_id, est_pages: int):
    """复刻原 run 接口的 credits 前置检查 · 返回 billing dict(含 is_exempt)· 不够余额则抛 402。"""
    billing = {"is_exempt": True, "pages_used_this_month": 0}
    try:
        billing = db.get_billing_status_combined(str(user_id), tenant_id)
        if not billing.get("allowed") and not billing.get("is_exempt"):
            est_cost = float(
                db.estimate_pdf_cost_thb(billing.get("pages_used_this_month", 0), est_pages)
            )
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": billing.get("balance_thb", 0.0),
                    "estimated_cost": est_cost,
                    "pages_used_this_month": billing.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[recon-submit.credits] pre-check skip: {e}")
    return billing


def _cleanup_on_fail(job_id: str):
    try:
        worker._cleanup_stage(job_id)
    except Exception:  # noqa: BLE001
        pass


_EXCEL_EXTS = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv"}  # S6a · CSV/TSV 也走表格预检


# BUG-FIX-RECON-GLCSV(2026-05-25):GL 预检纳入 CSV/TSV(与 stmt 侧 _EXCEL_EXTS 对称)。
# 此前 GL CSV 跳过同步预检 → 直接进异步 worker · 无 AI 学不到模板 → 必 needs_mapping →
# worker 把整侧失败静默存成 done 0 行任务(委托回归 P0-1/P0-2)。纳入后 GL CSV 走和 xlsx
# 一样的路径:能 AI/本地推断 → 同步学模板 + 后台解析出行;推不准 → 同步弹『确认列对应』。
_GL_EXTS = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv"}


def _preflight_stmt_mapping(input_ref, scope_id, api_key=""):
    """ADR-006 submit 同步预检:暂存的 Excel/CSV 账单(stmt)+ Excel 总账(gl)是否需确认列对应。

    返回 needs_mapping 响应 dict(交前端弹"确认列对应")· 或 None(都能理解 · 继续 enqueue)。
    PDF/图片不预检(走现有 OCR)· 本地推断毫秒级、不烧 Gemini。账单先于总账检查。

    ADR-006 S7 · 本地拿不准时,这里(同步阶段)传 allow_ai=True + api_key 让解析层调一次
    Gemini 要列映射(余额链/形状把关 · 过才用 + 存)· 异步 worker 不传 → 永不在后台烧钱。
    """
    try:
        from services.recon.bank_recon_v2 import parse_bank_stmt_xlsx_direct, parse_gl_excel
    except Exception:  # noqa: BLE001
        return None

    def _ext(fn):
        return ("." + fn.lower().rsplit(".", 1)[-1]) if "." in (fn or "") else ""

    # 1) 账单(stmt)· Excel + CSV/TSV
    for ref in input_ref or []:
        if ref.get("role") != "stmt":
            continue
        fn = ref.get("filename") or ""
        if _ext(fn) not in _EXCEL_EXTS:
            continue
        try:
            with open(ref["path"], "rb") as f:
                res = parse_bank_stmt_xlsx_direct(
                    f.read(), fn, tenant_id=scope_id, allow_ai=True, api_key=api_key
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[preflight] stmt {fn} skip: {e}")
            continue
        if res.get("needs_mapping"):
            return {
                "ok": False,
                "needs_mapping": True,
                "file": fn,
                **(res.get("mapping_request") or {}),
            }

    # 2) 总账(gl)· 仅 Excel(S6b)
    for ref in input_ref or []:
        if ref.get("role") != "gl":
            continue
        fn = ref.get("filename") or ""
        if _ext(fn) not in _GL_EXTS:
            continue
        try:
            with open(ref["path"], "rb") as f:
                res = parse_gl_excel(
                    f.read(), fn, tenant_id=scope_id, allow_ai=True, api_key=api_key
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[preflight] gl {fn} skip: {e}")
            continue
        if res.get("needs_mapping"):
            return {
                "ok": False,
                "needs_mapping": True,
                "file": fn,
                **(res.get("mapping_request") or {}),
            }
    return None


# ════ M4 银行对账 submit ════
@router.post("/api/recon/bank-v2/submit")
async def bank_v2_submit(
    request: Request,
    stmt_files: List[UploadFile] = File(...),
    gl_files: List[UploadFile] = File(...),
    gl_account: str = Form(""),
    lang: str = Form("th"),
    stmt_opening_override: Optional[float] = Form(None),
    gl_opening_override: Optional[float] = Form(None),
    gl_closing_override: Optional[float] = Form(None),
    stmt_closing_override: Optional[float] = Form(None),
):
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if not stmt_files or not gl_files:
        raise HTTPException(422, "请上传银行账单与 GL 文件")

    tenant_id = user.get("tenant_id")
    billing = _credits_precheck(user["id"], tenant_id, len(stmt_files) + len(gl_files))

    job_id = str(uuid.uuid4())
    try:
        input_ref = await _stage_uploads(job_id, stmt_files, "stmt", "statement.pdf")
        input_ref += await _stage_uploads(job_id, gl_files, "gl", "gl.xlsx")
        # ADR-006 · 同步预检:新模板 Excel 账单先确认列对应(不建任务)· S7 本地拿不准时
        # 在此同步阶段调一次 Gemini(allow_ai)· 异步 worker 不烧钱。
        _scope = str(tenant_id or user["id"])
        nm = _preflight_stmt_mapping(input_ref, _scope, api_key=_user_key(user))
        if nm:
            _cleanup_on_fail(job_id)
            return nm
        _ws = wc.active_workspace_for_request(request, _tid(user))
        params = {
            "user_id": str(user["id"]),
            "tenant_id": tenant_id,
            "workspace_client_id": _ws,  # PO-6d · 套账随 job 行/params 存
            "api_key": _user_key(user),
            "is_exempt": bool(billing.get("is_exempt", True)),
            "lang": lang,
            "gl_account": gl_account,
            "stmt_opening_override": stmt_opening_override,
            "gl_opening_override": gl_opening_override,
            "gl_closing_override": gl_closing_override,
            "stmt_closing_override": stmt_closing_override,
        }
        rid = store.enqueue(
            "bank",
            str(user["id"]),
            tenant_id,
            params,
            input_ref,
            job_id=job_id,
            workspace_client_id=_ws,
        )
        if not rid:
            _cleanup_on_fail(job_id)
            raise HTTPException(500, "任务创建失败,请稍后重试")
        return {"ok": True, "job_id": rid}
    except HTTPException:
        _cleanup_on_fail(job_id)
        raise


# ════ M3 收入对账 submit ════
@router.post("/api/recon/gl-vat/submit")
async def gl_vat_submit(
    request: Request,
    gl_file: Optional[UploadFile] = File(None),
    vat_file: Optional[UploadFile] = File(None),
    gl_files: Optional[List[UploadFile]] = File(None),
    vat_files: Optional[List[UploadFile]] = File(None),
    revenue_prefix: str = Form("4"),
    lang: str = Form("th"),
):
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")

    gl_list: List[UploadFile] = list(gl_files or [])
    vat_list: List[UploadFile] = list(vat_files or [])
    if gl_file is not None:
        gl_list.append(gl_file)
    if vat_file is not None:
        vat_list.append(vat_file)
    if not gl_list or not vat_list:
        raise HTTPException(422, "请上传 GL 与销项税报告文件")

    tenant_id = user.get("tenant_id")
    # M3-3 修(2026-05-25):收入对账与银行对账一致 · submit 前置 credits 检查(余额不足直接 402 ·
    #   不让付费 OCR/Gemini 先跑再失败)· is_exempt 透传给 worker 决定是否扣费。
    billing = _credits_precheck(user["id"], tenant_id, len(gl_list) + len(vat_list))
    job_id = str(uuid.uuid4())
    try:
        input_ref = await _stage_uploads(job_id, gl_list, "gl", "gl.pdf")
        input_ref += await _stage_uploads(job_id, vat_list, "vat", "vat.pdf")
        _ws = wc.active_workspace_for_request(request, _tid(user))
        params = {
            "user_id": str(user["id"]),
            "tenant_id": tenant_id,
            "workspace_client_id": _ws,  # PO-6d
            "api_key": _user_key(user),
            "is_exempt": bool(billing.get("is_exempt", True)),
            "revenue_prefix": revenue_prefix or "4",
            "lang": lang,
        }
        rid = store.enqueue(
            "glvat",
            str(user["id"]),
            tenant_id,
            params,
            input_ref,
            job_id=job_id,
            workspace_client_id=_ws,
        )
        if not rid:
            _cleanup_on_fail(job_id)
            raise HTTPException(500, "任务创建失败,请稍后重试")
        return {"ok": True, "job_id": rid}
    except HTTPException:
        _cleanup_on_fail(job_id)
        raise


# ════ M2 销项税 submit ════
@router.post("/api/vat_excel/submit")
async def vat_excel_submit(
    request: Request,
    invoices: List[UploadFile] = File(default=[]),
    reports: List[UploadFile] = File(default=[]),
    lang: str = Form("th"),
):
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if len(invoices) == 0 or len(reports) == 0:
        raise HTTPException(400, "至少上传 1 张发票 + 1 份 VAT 报告")

    tenant_id = user.get("tenant_id")
    billing = _credits_precheck(user["id"], tenant_id, len(invoices) + len(reports))

    job_id = str(uuid.uuid4())
    try:
        input_ref = await _stage_uploads(job_id, invoices, "invoice", "invoice.pdf")
        input_ref += await _stage_uploads(job_id, reports, "report", "report.pdf")
        _ws = wc.active_workspace_for_request(request, _tid(user))
        params = {
            "user_id": str(user["id"]),
            "tenant_id": tenant_id,
            "workspace_client_id": _ws,  # PO-6d
            "api_key": _user_key(user),
            "is_exempt": bool(billing.get("is_exempt", True)),
            "lang": lang,
        }
        rid = store.enqueue(
            "salesvat",
            str(user["id"]),
            tenant_id,
            params,
            input_ref,
            job_id=job_id,
            workspace_client_id=_ws,
        )
        if not rid:
            _cleanup_on_fail(job_id)
            raise HTTPException(500, "任务创建失败,请稍后重试")
        return {"ok": True, "job_id": rid}
    except HTTPException:
        _cleanup_on_fail(job_id)
        raise


# ════ 统一状态查询(三个对账共用)════
@router.get("/api/recon/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    job = store.get(job_id, user_id=str(user["id"]), tenant_id=user.get("tenant_id"))
    if not job:
        raise HTTPException(404, "任务不存在")
    _progress = job.get("progress") or {}
    return {
        "ok": True,
        "job_id": job["id"],
        "job_type": job.get("job_type"),
        "status": job.get("status"),
        "progress": _progress,
        # S8 · needs_review 时携带核对载荷(前端据此弹逐行核对面板)
        "review": _progress.get("review") if job.get("status") == "needs_review" else None,
        # BUG-FIX-RECON-GLCSV · needs_mapping 时携带列映射载荷(前端据此弹『确认列对应』面板 ·
        #   shape 与 submit 预检同源:{file, document_type, headers, preview_rows, suggested_mapping, …})
        "mapping": _progress.get("mapping") if job.get("status") == "needs_mapping" else None,
        "result_table": job.get("result_table"),
        "result_id": job.get("result_id"),
        "error_code": job.get("error_code"),
        "created_at": job.get("created_at"),
        "finished_at": job.get("finished_at"),
    }


# ════ M4 银行对账 · S8 用户核对纠错后重对账 ════
@router.post("/api/recon/bank-v2/confirm-rows/{job_id}")
async def bank_v2_confirm_rows(job_id: str, request: Request):
    """ADR-006 S8 · 用户在核对面板改完 OCR 行 → 用修正行重对账(不重 OCR、不重扣费)。

    body: {"rows": [review-row dict...]}。复制原任务暂存的 gl 文件到新任务暂存(自包含)·
    新任务注入 confirmed_stmt_rows → handler 跳过 stmt OCR · gl 仍正常解析 · 照旧对账落库。
    """
    import shutil

    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    body = await request.json()
    rows = body.get("rows") or []
    if not rows:
        raise HTTPException(422, "无修正行")
    orig = store.get(job_id, user_id=str(user["id"]), tenant_id=user.get("tenant_id"))
    if not orig:
        raise HTTPException(404, "任务不存在")
    if orig.get("status") != "needs_review":
        raise HTTPException(400, "该任务无需核对")
    review = (orig.get("progress") or {}).get("review") or {}

    new_job = str(uuid.uuid4())
    new_dir = worker.stage_dir_for(new_job)
    os.makedirs(new_dir, exist_ok=True)
    new_input: List[dict] = []
    for r in orig.get("input_ref") or []:
        if r.get("role") != "gl":
            continue
        src = r.get("path")
        if not src or not os.path.exists(src):
            continue
        dst = os.path.join(new_dir, os.path.basename(src))
        try:
            shutil.copy2(src, dst)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[confirm-rows] copy gl skip: {e}")
            continue
        new_input.append({"path": dst, "filename": r.get("filename"), "role": "gl"})

    params = dict(orig.get("params") or {})
    params["confirmed_stmt_rows"] = rows
    params["confirmed_opening"] = review.get("opening", 0.0)
    rid = store.enqueue(
        "bank",
        str(user["id"]),
        user.get("tenant_id"),
        params,
        new_input,
        job_id=new_job,
        workspace_client_id=params.get("workspace_client_id"),  # PO-6d · 沿用原任务套账
    )
    # 原暂存清理(gl 已复制到新任务)
    worker._cleanup_stage(job_id)
    if not rid:
        worker._cleanup_stage(new_job)
        raise HTTPException(500, "重对账任务创建失败,请稍后重试")
    return {"ok": True, "job_id": rid}
