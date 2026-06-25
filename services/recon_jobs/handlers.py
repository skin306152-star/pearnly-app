# -*- coding: utf-8 -*-
"""对账重活处理函数(ADR-005 · #14)· facade。

三个对账 run 重活(submit 接口落盘后由后台工人调用):
    run_bank_recon → bank_handler  ·  run_glvat / run_salesvat 留本模块
辅助(_read_inputs/_parallel 等)在 _handler_common。0 改识别/对账/计费逻辑。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

from ._handler_common import _read_inputs, _noop, _parallel, _resolve_api_key, ProgressCb
from .bank_handler import run_bank_recon
from services.export.archive import run_export

logger = logging.getLogger("recon_jobs.handlers")


# ════════════════════════════════════════════════════════════════════
# glvat · M3 收入对账(原 recon_routes.gl_vat_run 解析→对账→落库段)
# ════════════════════════════════════════════════════════════════════
def run_glvat(
    params: dict, input_ref: List[dict], progress_cb: Optional[ProgressCb] = None
) -> Tuple[str, Any]:
    progress_cb = progress_cb or _noop
    from core import db
    from routes.recon_routes import (
        parse_gl,
        parse_vat_report,
        reconcile_gl_vat,
        detail_to_json,
        summary_to_json,
        _pdf_billing_units,
    )

    revenue_prefix = params.get("revenue_prefix") or "4"
    api_key = _resolve_api_key(params)
    user_id = str(params.get("user_id"))
    tenant_id = params.get("tenant_id")
    is_exempt = bool(params.get("is_exempt", True))

    gl_data = _read_inputs(input_ref, "gl")
    vat_data = _read_inputs(input_ref, "vat")
    total = len(gl_data) + len(vat_data)
    progress_cb({"stage": "parse", "stage_done": 0, "stage_total": total})

    # 1. 并行解析 GL + 合并 rows
    gl_results = _parallel(lambda bf: parse_gl(bf[0], bf[1], revenue_prefix), gl_data)
    progress_cb({"stage": "parse", "stage_done": len(gl_data), "stage_total": total})
    # M3-2 修(2026-05-25 收入对账回归):已知业务失败返回 __failed__ sentinel 带明确 error_code ·
    #   worker 据此置 job failed + error_code(不再被统一吞成 processing_error)· 前端映射成 4 语文案。
    gl_errors = [r.get("error") for r in gl_results if not r.get("ok") and r.get("error")]
    if gl_errors and not any(r.get("rows") for r in gl_results):
        return ("__failed__", {"error_code": "gl_parse_failed"})
    merged_gl_rows: list = []
    for r in gl_results:
        merged_gl_rows.extend(r.get("rows") or [])
    if not merged_gl_rows:
        return ("__failed__", {"error_code": "gl_no_revenue_rows"})
    gl_row_count = sum(r.get("row_count") or 0 for r in gl_results)

    # 2. 并行解析 VAT + 合并 rows
    vat_results = _parallel(lambda bf: parse_vat_report(bf[0], bf[1], api_key=api_key), vat_data)
    progress_cb({"stage": "parse", "stage_done": total, "stage_total": total})
    vat_errors = [r.get("error") for r in vat_results if not r.get("ok") and r.get("error")]
    if vat_errors and not any(r.get("rows") for r in vat_results):
        return ("__failed__", {"error_code": "vat_parse_failed"})
    merged_vat_rows: list = []
    for r in vat_results:
        merged_vat_rows.extend(r.get("rows") or [])
    if not merged_vat_rows:
        return ("__failed__", {"error_code": "vat_no_rows"})
    vat_row_count = sum(r.get("row_count") or 0 for r in vat_results)

    # M3-3 修(2026-05-25 收入对账成本回归):此前 GL-VAT 完全不扣费 → 图片/PDF VAT 报告用了
    #   Gemini/OCR 却免费(成本泄漏)。改为与 run_bank/run_salesvat 一致的统一按量计费:
    #   图片/PDF 按 OCR 页 · Excel/CSV 本地解析按字符估算 · 各格式各费率 · 豁免账号不扣。
    if not is_exempt:
        try:
            from services.ocr.pdf_utils import count_pdf_pages as _count_pages

            _excel_exts = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}
            _pdf_units = 0
            _excel_units = 0
            for r, (b, fn) in list(zip(gl_results, gl_data)) + list(zip(vat_results, vat_data)):
                if not r.get("ok"):
                    continue
                row_count = len(r.get("rows") or [])
                if row_count == 0:
                    continue
                ext = "." + (fn or "").lower().rsplit(".", 1)[-1] if "." in (fn or "") else ""
                if ext in _excel_exts:
                    _excel_units += db._excel_char_count_estimate(b, fn)
                else:
                    _pdf_units += _pdf_billing_units(_count_pages(b) or 1, row_count)
            if _pdf_units > 0:
                db.charge_ocr_async(
                    user_id, tenant_id, "pdf", _pdf_units, None, f"收入对账 PDF · {_pdf_units} 页"
                )
            if _excel_units > 0:
                db.charge_ocr_async(
                    user_id,
                    tenant_id,
                    "excel",
                    _excel_units,
                    None,
                    f"收入对账 Excel · {_excel_units} 字符",
                )
        except Exception as _ce:  # noqa: BLE001
            logger.warning(f"💳 glvat async charge skip: {_ce}")

    # 3. 对账
    progress_cb({"stage": "reconcile", "stage_done": 0, "stage_total": 1})
    detail, summary = reconcile_gl_vat(merged_gl_rows, merged_vat_rows)
    matched = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) == 0)
    diff_cnt = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) != 0)
    unmatched = sum(1 for r in detail if r.gl_amount is None)

    # 5. 落库
    progress_cb({"stage": "persist", "stage_done": 0, "stage_total": 1})
    gl_name = "; ".join(fn for _, fn in gl_data)
    vat_name = "; ".join(fn for _, fn in vat_data)
    task_id = db.create_gl_vat_task(
        user_id=user_id,
        tenant_id=tenant_id,
        gl_filename=gl_name,
        vat_filename=vat_name,
        gl_row_count=gl_row_count or len(merged_gl_rows),
        vat_row_count=vat_row_count or len(merged_vat_rows),
        detail_json=detail_to_json(detail),
        summary_json=summary_to_json(summary),
        matched_count=matched,
        unmatched_count=unmatched,
        diff_count=diff_cnt,
    )
    progress_cb({"stage": "done", "stage_done": 1, "stage_total": 1})
    return ("gl_vat_task", task_id)


# ════════════════════════════════════════════════════════════════════
# salesvat · M2 销项税(原 vat_excel_routes.build_excel_endpoint 解析→生成→存库段)
# ════════════════════════════════════════════════════════════════════
def run_salesvat(
    params: dict, input_ref: List[dict], progress_cb: Optional[ProgressCb] = None
) -> Tuple[str, Any]:
    progress_cb = progress_cb or _noop
    import time
    from core import db
    from services.vat.vat_excel_export import (
        extract_invoices_parallel,
        extract_invoices_batched_parallel,
        merge_vat_reports,
        build_excel,
    )
    from routes.vat_excel_routes import _save_excel_file

    lang = params.get("lang") or "th"
    api_key = _resolve_api_key(params)
    user_id = str(params.get("user_id"))
    tenant_id = params.get("tenant_id")
    workspace_client_id = params.get("workspace_client_id")  # PO-6d · 套账随 job 行存
    is_exempt = bool(params.get("is_exempt", True))

    invoices = _read_inputs(input_ref, "invoice")
    reports = _read_inputs(input_ref, "report")
    t0 = time.time()

    # 报告先合并
    progress_cb({"stage": "report", "stage_done": 0, "stage_total": 1})
    report_files = [{"filename": fn, "bytes": b} for b, fn in reports]
    rep_result = merge_vat_reports(report_files, api_key)
    if not rep_result.get("ok"):
        raise ValueError(rep_result.get("error", "报告解析失败"))

    # 发票分流:xlsx/csv(标准模板/系统导出)走行项直读 —— 零成本零误差免 OCR;图片/PDF 走 OCR。
    from services.vat.vat_report_parser import STRUCTURED_INVOICE_EXTS, parse_structured_invoices

    struct_inv = [
        (b, fn) for b, fn in invoices if (fn or "").lower().endswith(STRUCTURED_INVOICE_EXTS)
    ]
    ocr_inv = [
        (b, fn) for b, fn in invoices if not (fn or "").lower().endswith(STRUCTURED_INVOICE_EXTS)
    ]

    parsed_invoices: List[dict] = []
    if ocr_inv:
        ocr_files = [{"filename": fn, "bytes": b} for b, fn in ocr_inv]
        progress_cb({"stage": "parse", "stage_done": 0, "stage_total": len(ocr_files)})
        if len(ocr_files) >= 10:
            parsed_invoices += extract_invoices_batched_parallel(
                ocr_files, api_key=api_key, batch_size=5, max_workers=4
            )
        else:
            parsed_invoices += extract_invoices_parallel(ocr_files, api_key, 10)
    if struct_inv:
        parsed_invoices += parse_structured_invoices(struct_inv, api_key=api_key)
    ok_invoices = [r for r in parsed_invoices if r.get("ok")]
    progress_cb({"stage": "parse", "stage_done": len(invoices), "stage_total": len(invoices)})

    # 异步扣费(原路由 create_task · 此处同步)· 失败发票不扣
    if not is_exempt:
        try:
            _billed_pages = len(ok_invoices) + len(reports)
            if _billed_pages > 0:
                db.charge_ocr_async(
                    user_id,
                    tenant_id,
                    "pdf",
                    _billed_pages,
                    None,
                    f"VAT 对账 · {len(ok_invoices)} 张发票 + {len(reports)} 份报告",
                )
        except Exception as _ce:  # noqa: BLE001
            logger.warning(f"💳 salesvat async charge skip: {_ce}")

    # 生成 Excel
    progress_cb({"stage": "build", "stage_done": 0, "stage_total": 1})
    xlsx_bytes, task_summary = build_excel(
        ok_invoices,
        rep_result["rows"],
        rep_result.get("seller_name", ""),
        rep_result.get("seller_tax_id", ""),
        rep_result.get("period_year"),
        rep_result.get("period_month"),
        lang,
    )
    elapsed = round(time.time() - t0, 2)

    # 成本记录(原路由 v4.10.14 · 不阻断)
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
        except Exception:  # noqa: BLE001
            _calib = 1.10
        _cost_usd = (
            _total_in * db.OCR_PRICING["input_per_m_usd"]
            + _total_out * db.OCR_PRICING["output_per_m_usd"]
        ) / 1_000_000
        _cost_thb = _cost_usd * db.OCR_PRICING["usd_thb"] * _calib
        db.log_ocr_cost(
            user_id=user_id,
            tenant_id=str(tenant_id) if tenant_id else None,
            history_id=None,
            engine="gemini-vex",
            pages=len(ok_invoices) + len(report_files),
            input_tokens=_total_in,
            output_tokens=_total_out,
            cost_thb=round(_cost_thb, 4),
            elapsed_ms=int(elapsed * 1000),
        )
    except Exception as _ce:  # noqa: BLE001
        logger.warning(f"[salesvat] cost log failed (non-blocking): {_ce}")

    # 存库(写现有 vat_recon_tasks + 落盘 excel · 前端用 /tasks/{id}/download 取)
    progress_cb({"stage": "persist", "stage_done": 0, "stage_total": 1})
    py = rep_result.get("period_year") or 0
    pm = rep_result.get("period_month") or 0
    seller_short = (rep_result.get("seller_name", "")[:20] or "client").strip()
    period_label = f"{py}-{pm:02d}" if (py and pm) else ""
    raw_data = {
        "invoices": ok_invoices,
        "report_rows": rep_result["rows"],
        "seller_name": rep_result.get("seller_name", ""),
        "seller_tax_id": rep_result.get("seller_tax_id", ""),
        "period_year": rep_result.get("period_year"),
        "period_month": rep_result.get("period_month"),
        "lang": lang,
        # P1-4(2026-05-25):解析层 OCR 计数 · 前端只读这些显示"OCR 失败"· 不再用对账差异
        #   (n_total-n_ok)误推。invoice_ocr_failed_count = 上传发票数 − OCR 成功数。
        "invoice_file_count": len(invoices),
        "invoice_ocr_ok_count": len(ok_invoices),
        "invoice_ocr_failed_count": max(0, len(invoices) - len(ok_invoices)),
        "invoice_failed_files": [
            (r.get("filename") or "?") for r in parsed_invoices if not r.get("ok")
        ],
        **task_summary,
    }
    task_id = db.create_vat_recon_task(
        tenant_id=tenant_id,
        user_id=user_id,
        workspace_client_id=workspace_client_id,
        client_name=seller_short,
        period=period_label,
        invoice_count=len(ok_invoices),
        report_count=rep_result.get("row_count", 0),
        matched=task_summary["n_ok"],
        mismatched=task_summary["n_diff"],
        mismatch_amount=task_summary["diff_amount_total"],
        elapsed_seconds=elapsed,
        excel_path=None,
        raw_data_json=raw_data,
        lang=lang,
    )
    if task_id:
        excel_path = _save_excel_file(tenant_id, task_id, xlsx_bytes)
        if excel_path:
            try:
                with db.get_cursor_rls(bypass=True, commit=True) as cur:
                    cur.execute(
                        "UPDATE vat_recon_tasks SET excel_path=%s WHERE id=%s::uuid",
                        (excel_path, task_id),
                    )
            except Exception as _e:  # noqa: BLE001
                logger.warning(f"[salesvat] excel_path 更新失败: {_e}")
    progress_cb({"stage": "done", "stage_done": 1, "stage_total": 1})
    return ("vat_recon_tasks", task_id)


# ── import 即注册(worker.bootstrap_handlers 触发)─────────────────
def _register() -> None:
    from . import worker

    worker.register_handler("bank", run_bank_recon)
    worker.register_handler("glvat", run_glvat)
    worker.register_handler("salesvat", run_salesvat)
    worker.register_handler("export", run_export)


_register()
