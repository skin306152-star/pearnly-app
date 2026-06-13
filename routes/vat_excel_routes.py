# -*- coding: utf-8 -*-
"""
v118.32.4.10.0 · Excel 公式对账 · 路由层
全网开放(撤 email gate) · 任务持久化(vat_recon_tasks)
"""

import io
import os
import time
import asyncio
import logging
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import StreamingResponse, FileResponse

from core import db
from core import workspace_context as wc
from core.auth import get_current_user_from_request
from services.vat.vat_excel_export import (
    extract_invoices_parallel,
    extract_invoices_batched_parallel,  # v118.32.5 · 批量OCR 性能优化 B
    merge_vat_reports,
    build_excel,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vat_excel", tags=["vat-excel"])

# 上限
MAX_INVOICES = 1000
MAX_REPORTS = 30

# Excel 存储根目录(服务器端)
EXCEL_STORE_DIR = "/opt/mrpilot/uploads/vat_recon"

# 4 语文件名前缀（th→en→zh→ja · GTM 优先级顺序）
_FNAME_PREFIX = {
    "th": "รายงานกระทบยอดภาษีขาย",
    "en": "Output_VAT_Reconciliation",
    "zh": "销项税对账表",
    "ja": "売上VAT照合表",
}

from services.vat.vat_excel_helpers import _require_user, _user_key, _tenant_user  # noqa: F401


def _save_excel_file(tenant_id, task_id: str, xlsx_bytes: bytes) -> Optional[str]:
    """把 xlsx bytes 写到磁盘 · 返回 path · 失败返回 None"""
    try:
        folder_key = str(tenant_id) if tenant_id else "no_tenant"
        folder = os.path.join(EXCEL_STORE_DIR, folder_key)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{task_id}.xlsx")
        with open(path, "wb") as f:
            f.write(xlsx_bytes)
        return path
    except Exception as e:
        logger.error(f"[vex] save_excel_file failed: {e}")
        return None


# ════ /check — 前端探测(兼容旧版 · 全网开放后直接返回 allowed=True) ════
@router.get("/check")
async def check_access(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return {"ok": False, "allowed": False}
    return {"ok": True, "allowed": True}


# ════ /build — 核心对账 endpoint ════
@router.post("/build")
async def build_excel_endpoint(
    request: Request,
    invoices: List[UploadFile] = File(default=[]),
    reports: List[UploadFile] = File(default=[]),
    lang: str = Form("th"),
):
    """接发票 + 报告 → 并行 OCR → 生成 Excel + 存任务记录"""
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)

    if len(invoices) == 0 or len(reports) == 0:
        raise HTTPException(400, "至少上传 1 张发票 + 1 份 VAT 报告")
    if len(invoices) > MAX_INVOICES:
        raise HTTPException(413, f"单次最多 {MAX_INVOICES} 张发票")
    if len(reports) > MAX_REPORTS:
        raise HTTPException(413, f"单次最多 {MAX_REPORTS} 份 VAT 报告 PDF")
    if lang not in ("th", "zh", "en", "ja"):
        lang = "th"

    # v118.35.0.21 · Credits 前置检查(1 次 SELECT · 异步扣费)
    _billing_vex = {"is_exempt": True, "pages_used_this_month": 0}
    try:
        _billing_vex = db.get_billing_status_combined(str(user_id), tenant_id)
        if not _billing_vex.get("allowed") and not _billing_vex.get("is_exempt"):
            _est_pages = len(invoices) + len(reports)
            _est_cost = float(
                db.estimate_pdf_cost_thb(_billing_vex.get("pages_used_this_month", 0), _est_pages)
            )
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": _billing_vex.get("balance_thb", 0.0),
                    "estimated_cost": _est_cost,
                    "pages_used_this_month": _billing_vex.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as _be:
        logger.warning(f"[vex.credits] pre-check skip: {_be}")

    api_key = _user_key(user)
    t0 = time.time()

    # 报告先合并
    report_files = []
    for f in reports:
        b = await f.read()
        report_files.append({"filename": f.filename or "report.pdf", "bytes": b})

    loop = asyncio.get_event_loop()
    rep_result = await loop.run_in_executor(None, merge_vat_reports, report_files, api_key)
    if not rep_result.get("ok"):
        raise HTTPException(422, rep_result.get("error", "报告解析失败"))

    logger.info(
        f"[vex.build] 报告合并 OK · {len(report_files)} 份 → "
        f"{rep_result['row_count']} 行 · seller={rep_result.get('seller_tax_id')}"
    )

    # 发票分流:xlsx/csv(标准模板/系统导出)行项直读免 OCR;图片/PDF 走 OCR。
    from services.vat.vat_report_parser import STRUCTURED_INVOICE_EXTS, parse_structured_invoices

    struct_inv = []
    ocr_files = []
    for f in invoices:
        b = await f.read()
        fn = f.filename or "invoice.pdf"
        if fn.lower().endswith(STRUCTURED_INVOICE_EXTS):
            struct_inv.append((b, fn))
        else:
            ocr_files.append({"filename": fn, "bytes": b})

    parsed_invoices = []
    if ocr_files:
        # v118.32.5 · 发票 ≥ 10 张启用批量 OCR(5/批 · 4 并行)· 减少 5x API 调用
        if len(ocr_files) >= 10:
            logger.info(f"[vex.build] 发票 {len(ocr_files)} 张 · 启用批量OCR(5/批 · 4并行)")
            parsed_invoices += await loop.run_in_executor(
                None,
                lambda: extract_invoices_batched_parallel(
                    ocr_files, api_key=api_key, batch_size=5, max_workers=4
                ),
            )
        else:
            parsed_invoices += await loop.run_in_executor(
                None, extract_invoices_parallel, ocr_files, api_key, 10
            )
    if struct_inv:
        parsed_invoices += await loop.run_in_executor(
            None, parse_structured_invoices, struct_inv, api_key
        )

    ok_invoices = [r for r in parsed_invoices if r.get("ok")]
    fail_invoices = [r for r in parsed_invoices if not r.get("ok")]
    logger.info(
        f"[vex.build] 发票 OCR · ok={len(ok_invoices)} fail={len(fail_invoices)} "
        f"· 总耗时 {time.time()-t0:.1f}s"
    )

    # v118.35.0.21 · 异步扣费 · 失败发票不扣 · 豁免账号自动跳过
    if not _billing_vex.get("is_exempt"):
        try:
            _billed_pages = len(ok_invoices) + len(reports)
            if _billed_pages > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        db.charge_ocr_async,
                        str(user_id),
                        tenant_id,
                        "pdf",
                        _billed_pages,
                        None,
                        f"VAT 对账 · {len(ok_invoices)} 张发票 + {len(reports)} 份报告",
                    )
                )
        except Exception as _ce:
            logger.warning(f"💳 vex.build async charge skip: {_ce}")

    # 生成 Excel (返回 tuple)
    xlsx_bytes, task_summary = await loop.run_in_executor(
        None,
        build_excel,
        ok_invoices,
        rep_result["rows"],
        rep_result.get("seller_name", ""),
        rep_result.get("seller_tax_id", ""),
        rep_result.get("period_year"),
        rep_result.get("period_month"),
        lang,
    )

    elapsed = round(time.time() - t0, 2)

    # v4.10.14 · VEX OCR 成本记录(真实 token · 统一 OCR_PRICING 口径)
    try:
        _inv_in = sum(int(r.get("_input_tokens") or 0) for r in ok_invoices)
        _inv_out = sum(int(r.get("_output_tokens") or 0) for r in ok_invoices)
        _rep_in = int(rep_result.get("_input_tokens") or 0)
        _rep_out = int(rep_result.get("_output_tokens") or 0)
        _total_in = _inv_in + _rep_in
        _total_out = _inv_out + _rep_out
        try:
            _bal = db.get_latest_balance()
            _calib = float((_bal.get("calibration_factor") or 1.10)) if _bal else 1.10
        except Exception:
            _calib = 1.10
        # v4.10.14 过渡 · calib 校准系数 v4.10.15 admin 改造时统一砍
        _cost_usd = (
            _total_in * db.OCR_PRICING["input_per_m_usd"]
            + _total_out * db.OCR_PRICING["output_per_m_usd"]
        ) / 1_000_000
        _cost_thb = _cost_usd * db.OCR_PRICING["usd_thb"] * _calib
        db.log_ocr_cost(
            user_id=str(user_id),
            tenant_id=str(tenant_id) if tenant_id else None,
            history_id=None,
            engine="gemini-vex",
            pages=len(ok_invoices) + len(report_files),
            input_tokens=_total_in,
            output_tokens=_total_out,
            cost_thb=round(_cost_thb, 4),
            elapsed_ms=int(elapsed * 1000),
        )
        logger.info(
            f"[vex] 成本记录 · inv_in={_inv_in} rep_in={_rep_in} out={_total_out} · ≈THB {_cost_thb:.4f}"
        )
    except Exception as _ce:
        logger.warning(f"[vex] cost log failed (non-blocking): {_ce}")

    # 文件名
    py = rep_result.get("period_year") or 0
    pm = rep_result.get("period_month") or 0
    period_str = f"{py}-{pm:02d}" if (py and pm) else "unknown"
    seller_short = (rep_result.get("seller_name", "")[:20] or "client").strip()
    fname_prefix = _FNAME_PREFIX.get(lang, "销项税对账表")
    fname = f"{fname_prefix}_{seller_short}_{period_str}.xlsx"
    fname_clean = "".join(c if c not in '/\\:*?"<>|' else "_" for c in fname)
    fname_encoded = quote(fname_clean.encode("utf-8"))
    content_disposition = (
        f'attachment; filename="vat_recon.xlsx"; ' f"filename*=UTF-8''{fname_encoded}"
    )

    # ── 异步存库(try/except · 不阻断下载) ──
    task_id = None
    try:
        period_label = f"{py}-{pm:02d}" if (py and pm) else ""
        raw_data = {
            "invoices": ok_invoices,
            "report_rows": rep_result["rows"],
            "seller_name": rep_result.get("seller_name", ""),
            "seller_tax_id": rep_result.get("seller_tax_id", ""),
            "period_year": rep_result.get("period_year"),
            "period_month": rep_result.get("period_month"),
            "lang": lang,
            **task_summary,  # n_total / n_ok / n_diff / diff_amount_total / rows
        }
        task_id = db.create_vat_recon_task(
            tenant_id=tenant_id,
            user_id=str(user_id),
            workspace_client_id=wc.active_workspace_for_request(request, tenant_id),
            client_name=seller_short,
            period=period_label,
            invoice_count=len(ok_invoices),
            report_count=rep_result.get("row_count", 0),
            matched=task_summary["n_ok"],
            mismatched=task_summary["n_diff"],
            mismatch_amount=task_summary["diff_amount_total"],
            elapsed_seconds=elapsed,
            excel_path=None,  # 先 None · 文件写好后更新
            raw_data_json=raw_data,
            lang=lang,
        )
        if task_id:
            excel_path = _save_excel_file(tenant_id, task_id, xlsx_bytes)
            if excel_path:
                # 更新 excel_path
                try:
                    with db.get_cursor(commit=True) as cur:
                        cur.execute(
                            "UPDATE vat_recon_tasks SET excel_path=%s WHERE id=%s::uuid",
                            (excel_path, task_id),
                        )
                except Exception as _e:
                    logger.warning(f"[vex] excel_path 更新失败: {_e}")
            logger.info(f"[vex.build] 任务存库 OK · task_id={task_id}")
    except Exception as e:
        logger.error(f"[vex.build] 任务存库失败(不影响下载): {e}")

    headers = {
        "Content-Disposition": content_disposition,
        "X-Vex-Invoices-Ok": str(len(ok_invoices)),
        "X-Vex-Invoices-Fail": str(len(fail_invoices)),
        "X-Vex-Report-Rows": str(rep_result.get("row_count", 0)),
        "X-Vex-Elapsed-Ms": str(int(elapsed * 1000)),
        "X-Vex-Task-Id": task_id or "",
    }
    if fail_invoices:
        import base64
        import json as _json

        fail_brief = [{"f": r.get("filename"), "e": r.get("error", "")[:80]} for r in fail_invoices]
        b64 = base64.b64encode(_json.dumps(fail_brief).encode("utf-8")).decode("ascii")
        headers["X-Vex-Fail-List-B64"] = b64

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# ════ 任务下载 ════
@router.get("/tasks/{task_id}/download")
async def download_task(task_id: str, request: Request):
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)
    task = db.get_vat_recon_task(
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=str(user_id),
        workspace_client_id=wc.active_workspace_for_request(request, tenant_id),
    )
    if not task:
        raise HTTPException(404, "任务不存在")

    lang = task.get("lang") or "th"
    excel_path = task.get("excel_path")

    # 热存文件存在 → 直接 serve
    if excel_path and os.path.exists(excel_path):
        client_name = (task.get("client_name") or "client")[:20]
        period = task.get("period") or "unknown"
        fname_prefix = _FNAME_PREFIX.get(lang, "销项税对账表")
        fname = f"{fname_prefix}_{client_name}_{period}.xlsx"
        fname_clean = "".join(c if c not in '/\\:*?"<>|' else "_" for c in fname)
        fname_encoded = quote(fname_clean.encode("utf-8"))
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="vat_recon.xlsx"; ' f"filename*=UTF-8''{fname_encoded}"
                )
            },
        )

    # 文件不存在 → 从 raw_data_json 重新生成
    raw = task.get("raw_data_json") or {}
    invoices_data = raw.get("invoices") or []
    report_rows_data = raw.get("report_rows") or []
    if not invoices_data or not report_rows_data:
        raise HTTPException(410, "对账数据已过期 · 请重新对账")

    loop = asyncio.get_event_loop()
    xlsx_bytes, _ = await loop.run_in_executor(
        None,
        build_excel,
        invoices_data,
        report_rows_data,
        raw.get("seller_name", ""),
        raw.get("seller_tax_id", ""),
        raw.get("period_year"),
        raw.get("period_month"),
        lang,
    )

    client_name = (task.get("client_name") or "client")[:20]
    period = task.get("period") or "unknown"
    fname_prefix = _FNAME_PREFIX.get(lang, "销项税对账表")
    fname = f"{fname_prefix}_{client_name}_{period}.xlsx"
    fname_clean = "".join(c if c not in '/\\:*?"<>|' else "_" for c in fname)
    fname_encoded = quote(fname_clean.encode("utf-8"))

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f'attachment; filename="vat_recon.xlsx"; ' f"filename*=UTF-8''{fname_encoded}"
            )
        },
    )


# ════ 重新生成对账表(用已存 raw_data 重建 xlsx · 不重跑 OCR) ════
@router.post("/tasks/{task_id}/regenerate")
async def regenerate_task(task_id: str, request: Request):
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)
    task = db.get_vat_recon_task(
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=str(user_id),
        workspace_client_id=wc.active_workspace_for_request(request, tenant_id),
    )
    if not task:
        raise HTTPException(404, "任务不存在")
    raw = task.get("raw_data_json") or {}
    invoices_data = raw.get("invoices") or []
    report_rows_data = raw.get("report_rows") or []
    if not invoices_data or not report_rows_data:
        raise HTTPException(410, "对账数据已过期 · 请重新对账")

    lang = task.get("lang") or "th"
    loop = asyncio.get_event_loop()
    t0 = time.time()
    xlsx_bytes, task_summary = await loop.run_in_executor(
        None,
        build_excel,
        invoices_data,
        report_rows_data,
        raw.get("seller_name", ""),
        raw.get("seller_tax_id", ""),
        raw.get("period_year"),
        raw.get("period_month"),
        lang,
    )
    elapsed = round(time.time() - t0, 2)

    # 更新文件 + summary
    try:
        excel_path = _save_excel_file(tenant_id, task_id, xlsx_bytes)
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE vat_recon_tasks
                SET excel_path=%s, matched=%s, mismatched=%s, mismatch_amount=%s,
                    elapsed_seconds=%s, updated_at=NOW()
                WHERE id=%s::uuid
            """,
                (
                    excel_path,
                    task_summary["n_ok"],
                    task_summary["n_diff"],
                    task_summary["diff_amount_total"],
                    elapsed,
                    task_id,
                ),
            )
    except Exception as e:
        logger.error(f"[vex.regen] 更新任务失败: {e}")

    client_name = (task.get("client_name") or "client")[:20]
    period = task.get("period") or "unknown"
    fname_prefix = _FNAME_PREFIX.get(lang, "销项税对账表")
    fname = f"{fname_prefix}_{client_name}_{period}.xlsx"
    fname_clean = "".join(c if c not in '/\\:*?"<>|' else "_" for c in fname)
    fname_encoded = quote(fname_clean.encode("utf-8"))

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f'attachment; filename="vat_recon.xlsx"; ' f"filename*=UTF-8''{fname_encoded}"
            ),
            "X-Vex-Elapsed-Ms": str(int(elapsed * 1000)),
        },
    )


# R22 · 任务列表/删除路由下沉 vat_excel_tasks_routes · 此处 include_router 聚合(承本 router 的 /api/vat_excel 前缀)
from routes.vat_excel_tasks_routes import router as _tasks_router  # noqa: E402

router.include_router(_tasks_router)
