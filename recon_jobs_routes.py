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

import db
from auth import get_current_user_from_request
from services.recon_jobs import store, worker

logger = logging.getLogger("recon_jobs.routes")
router = APIRouter(tags=["recon-jobs"])


def _user_key(user) -> str:
    return (
        user.get("gemini_api_key") or user.get("custom_gemini_api_key") or ""
    ).strip() or os.environ.get("GEMINI_API_KEY", "").strip()


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


def _preflight_stmt_mapping(input_ref, scope_id):
    """ADR-006 submit 同步预检:暂存的 Excel 银行账单是否需用户确认列对应。

    返回 needs_mapping 响应 dict(交前端弹"确认列对应")· 或 None(都能理解 · 继续 enqueue)。
    只检 Excel 银行账单(stmt)· PDF/图片不预检(走现有 OCR)· 毫秒级、不烧 Gemini。
    """
    try:
        from bank_recon_v2 import parse_bank_stmt_xlsx_direct
    except Exception:  # noqa: BLE001
        return None
    for ref in input_ref or []:
        if ref.get("role") != "stmt":
            continue
        fn = ref.get("filename") or ""
        ext = ("." + fn.lower().rsplit(".", 1)[-1]) if "." in fn else ""
        if ext not in _EXCEL_EXTS:
            continue
        try:
            with open(ref["path"], "rb") as f:
                b = f.read()
            res = parse_bank_stmt_xlsx_direct(b, fn, tenant_id=scope_id)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[preflight] {fn} skip: {e}")
            continue
        if res.get("needs_mapping"):
            mr = res.get("mapping_request") or {}
            return {"ok": False, "needs_mapping": True, "file": fn, **mr}
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
        # ADR-006 · 同步预检:新模板 Excel 账单先确认列对应(不建任务 · 不烧 Gemini)
        _scope = str(tenant_id or user["id"])
        nm = _preflight_stmt_mapping(input_ref, _scope)
        if nm:
            _cleanup_on_fail(job_id)
            return nm
        params = {
            "user_id": str(user["id"]),
            "tenant_id": tenant_id,
            "api_key": _user_key(user),
            "is_exempt": bool(billing.get("is_exempt", True)),
            "lang": lang,
            "gl_account": gl_account,
            "stmt_opening_override": stmt_opening_override,
            "gl_opening_override": gl_opening_override,
            "gl_closing_override": gl_closing_override,
            "stmt_closing_override": stmt_closing_override,
        }
        rid = store.enqueue("bank", str(user["id"]), tenant_id, params, input_ref, job_id=job_id)
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
    job_id = str(uuid.uuid4())
    try:
        input_ref = await _stage_uploads(job_id, gl_list, "gl", "gl.pdf")
        input_ref += await _stage_uploads(job_id, vat_list, "vat", "vat.pdf")
        params = {
            "user_id": str(user["id"]),
            "tenant_id": tenant_id,
            "api_key": _user_key(user),
            "revenue_prefix": revenue_prefix or "4",
            "lang": lang,
        }
        rid = store.enqueue("glvat", str(user["id"]), tenant_id, params, input_ref, job_id=job_id)
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
        params = {
            "user_id": str(user["id"]),
            "tenant_id": tenant_id,
            "api_key": _user_key(user),
            "is_exempt": bool(billing.get("is_exempt", True)),
            "lang": lang,
        }
        rid = store.enqueue(
            "salesvat", str(user["id"]), tenant_id, params, input_ref, job_id=job_id
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
    return {
        "ok": True,
        "job_id": job["id"],
        "job_type": job.get("job_type"),
        "status": job.get("status"),
        "progress": job.get("progress") or {},
        "result_table": job.get("result_table"),
        "result_id": job.get("result_id"),
        "error_code": job.get("error_code"),
        "created_at": job.get("created_at"),
        "finished_at": job.get("finished_at"),
    }
