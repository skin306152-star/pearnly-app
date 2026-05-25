# -*- coding: utf-8 -*-
"""
对账重活处理函数(ADR-005 · BUG-FIX-RECON-ASYNC · #14)。

把三个对账 run 接口里『解析 + 对账 + 写结果表』那一段,**原样**抽成可被后台工人
调用的纯函数:

    run_bank_recon(params, input_ref, progress_cb) -> (result_table, result_id)
    run_glvat(params, input_ref, progress_cb)       -> (result_table, result_id)
    run_salesvat(params, input_ref, progress_cb)    -> (result_table, result_id)

铁律(ADR-005 §3 ④ / §7):
  - **0 改识别逻辑**:解析/Gemini/对账函数原样调用 · 准确率零影响。
  - 结果照写**现有**结果表(bank_recon_v2_task / gl_vat_task / vat_recon_tasks)·
    历史/导出/KPI 全不动。
  - 鉴权 / credits 前置检查留在 submit 接口(#15)· 这里只跑重活。

输入约定(submit 接口落盘后传进来):
  params: dict —— 业务参数 + 归属(user_id / tenant_id / api_key / is_exempt / lang 等)
  input_ref: list —— 暂存文件描述 [{"path", "filename", "role"}, ...]
             role ∈ {stmt, gl}(bank)/ {gl, vat}(glvat)/ {invoice, report}(salesvat)
  progress_cb: callable(dict) —— 写进度(stage / stage_done / stage_total / current_file)

并行:工人已在线程里跑本函数(store.claim → asyncio.to_thread(_run_one))· 这里用
ThreadPoolExecutor 复刻原路由 asyncio.gather 的多文件并行解析 · 不引事件循环。
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional, Tuple

logger = logging.getLogger("recon_jobs.handlers")

ProgressCb = Callable[[dict], None]


# ── 暂存文件读取 ────────────────────────────────────────────────────
def _read_inputs(input_ref: List[dict], role: str) -> List[Tuple[bytes, str]]:
    """从暂存目录按 role 读出 (bytes, filename) 列表 · 保序。"""
    out: List[Tuple[bytes, str]] = []
    for item in input_ref or []:
        if (item or {}).get("role") != role:
            continue
        path = item.get("path")
        fname = item.get("filename") or os.path.basename(path or "") or "file"
        with open(path, "rb") as f:
            out.append((f.read(), fname))
    return out


def _noop(_p: dict) -> None:
    pass


def _side_fail_signal(stmt_results, stmt_data, gl_results, gl_data, failed_id):
    """整侧解析全失败 → 给 worker 的非 done 信号(BUG-FIX-RECON-GLCSV · 失败分流)。

    ① 任一失败结果带 mapping_request(读到了表格结构 · 有 headers/preview · 只是不认识列)
       → ("__needs_mapping__", …)· worker 置 needs_mapping · 前端弹『确认列对应』让用户指认。
    ② 否则(连表格结构都没读出:PDF/OCR 失败 / 空 / 损坏 / 无 headers)
       → ("__failed__", …)· worker 置 failed · 前端显示明确失败原因。
    result_id 指向已存的诊断任务(#16:历史/GET 仍能看解析诊断表)。
    """
    paired = list(zip(stmt_results, stmt_data)) + list(zip(gl_results, gl_data))
    # ① 有 mapping_request 的优先(stmt 先 gl 后)· 可现场弹面板修
    for r, (_, fn) in paired:
        if r.get("ok"):
            continue
        if r.get("needs_mapping") and r.get("mapping_request"):
            return (
                "__needs_mapping__",
                {
                    "mapping": {"file": fn, **(r.get("mapping_request") or {})},
                    "result_table": "bank_recon_v2_task",
                    "result_id": failed_id,
                    "error_code": "needs_mapping",
                },
            )
    # ② 无表格结构可修 → 明确失败 · 取第一条失败结果的 error_code(前端翻译成友好文案)
    code = "parse_failed"
    for r, _ in paired:
        if not r.get("ok"):
            code = r.get("error_code") or "parse_failed"
            break
    return (
        "__failed__",
        {
            "result_table": "bank_recon_v2_task",
            "result_id": failed_id,
            "error_code": code,
        },
    )


def _parallel(fn: Callable, items: List, max_workers: int = 4) -> List:
    """并行映射 · 保持输入顺序(复刻原路由 asyncio.gather 行为)。"""
    if not items:
        return []
    if len(items) == 1:
        return [fn(items[0])]
    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as ex:
        return list(ex.map(fn, items))


# ════════════════════════════════════════════════════════════════════
# bank · M4 银行对账(原 recon_routes.bank_v2_run 解析→对账→落库段)
# ════════════════════════════════════════════════════════════════════
def run_bank_recon(
    params: dict, input_ref: List[dict], progress_cb: Optional[ProgressCb] = None
) -> Tuple[str, Any]:
    progress_cb = progress_cb or _noop
    import db
    from recon_routes import (
        parse_bank_statement_pdf,
        parse_gl_v2,
        merge_statements,
        merge_gl_files,
        bank_reconcile,
        rows_to_json,
        bank_summary_to_json,
        _apply_anchor_overrides,
        _detect_recon_mismatch,
        _brv2_warn,
        _completeness_details,
        _pdf_billing_units,
    )

    lang = params.get("lang") or "th"
    gl_account = params.get("gl_account") or ""
    api_key = (params.get("api_key") or os.environ.get("GEMINI_API_KEY", "")).strip()
    user_id = str(params.get("user_id"))
    tenant_id = params.get("tenant_id")
    is_exempt = bool(params.get("is_exempt", True))

    # ADR-006 S8 · 用户核对纠错后的重对账:注入修正行 → 跳过 stmt OCR(不重读、不重扣费)
    confirmed_rows = params.get("confirmed_stmt_rows")

    stmt_data = _read_inputs(input_ref, "stmt")
    gl_data = _read_inputs(input_ref, "gl")
    total = len(stmt_data) + len(gl_data)
    progress_cb({"stage": "parse", "stage_done": 0, "stage_total": total})

    # 1. 解析(并行)· ADR-006 模板学习层作用域 = 租户优先,无租户退回 user_id
    #    (必须与 submit 预检 / save-mapping 用同一作用域,否则确认过的映射 worker 找不到)
    _scope = tenant_id or user_id
    if confirmed_rows:
        from services.importer.stmt_review import review_rows_to_statement_rows

        _srows = review_rows_to_statement_rows(confirmed_rows)
        _last_bal = _srows[-1].balance if _srows else 0.0
        stmt_results = [
            {
                "ok": True,
                "rows": _srows,
                "opening": float(params.get("confirmed_opening") or 0.0),
                "closing": _last_bal,
                "bank_code": params.get("confirmed_bank_code") or "generic",
                "completeness": {"ok": True},
            }
        ]
    else:
        stmt_results = _parallel(
            lambda bf: parse_bank_statement_pdf(bf[0], bf[1], api_key, tenant_id=_scope), stmt_data
        )
    progress_cb({"stage": "parse", "stage_done": len(stmt_data), "stage_total": total})
    gl_results = _parallel(
        lambda bf: parse_gl_v2(bf[0], bf[1], gl_account, api_key, tenant_id=_scope), gl_data
    )
    progress_cb({"stage": "parse", "stage_done": total, "stage_total": total})

    # 异步扣费 · 按扩展名分 pdf/excel(原路由 create_task · 此处工人线程内同步调用)
    # S8 · 确认重对账不重扣费(首次 OCR 已扣)
    if not is_exempt and not confirmed_rows:
        try:
            from services.ocr.pdf_utils import count_pdf_pages as _count_pages

            _excel_exts = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}
            _pdf_units = 0
            _excel_units = 0
            for r, (b, fn) in list(zip(stmt_results, stmt_data)) + list(zip(gl_results, gl_data)):
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
                    user_id, tenant_id, "pdf", _pdf_units, None, f"银行对账 PDF · {_pdf_units} 页"
                )
            if _excel_units > 0:
                db.charge_ocr_async(
                    user_id,
                    tenant_id,
                    "excel",
                    _excel_units,
                    None,
                    f"银行对账 Excel · {_excel_units} 字符",
                )
        except Exception as _ce:  # noqa: BLE001
            logger.warning(f"💳 bank async charge skip: {_ce}")

    # ADR-006 S8 · 核对闸:PDF/图片账单 OCR 低信心或完整性不过 → 暂停等用户逐行核对纠错
    #   (干净 OCR / Excel / 确认重跑 → 不触发 · 照旧对账)· 守铁律「低信心主动喊停·不静默出错」
    if not confirmed_rows:
        try:
            from services.importer import stmt_review as _sr

            _review = _sr.build_bank_review_payload(stmt_results, [fn for _, fn in stmt_data])
            if _review:
                logger.info(
                    f"[bank] needs_review · files={_review.get('files')} "
                    f"rows={_review.get('row_count')} low_conf={_review.get('low_conf_count')}"
                )
                return ("__needs_review__", _review)
        except Exception as _re:  # noqa: BLE001
            logger.warning(f"[bank] review gate skip(tolerated): {_re}")

    parse_info = {
        "stmt_files": [
            {
                "file": fn,
                "rows": len(r.get("rows") or []),
                "ok": r.get("ok", False),
                "error": r.get("error"),
                "error_code": r.get("error_code"),
                "bank_code": r.get("bank_code", ""),
            }
            for r, (_, fn) in zip(stmt_results, stmt_data)
        ],
        "gl_files": [
            {
                "file": fn,
                "rows": len(r.get("rows") or []),
                "ok": r.get("ok", False),
                "error": r.get("error"),
                "error_code": r.get("error_code"),
                "accounts": r.get("accounts", []),
            }
            for r, (_, fn) in zip(gl_results, gl_data)
        ],
    }
    stmt_file_names = "; ".join(fn for _, fn in stmt_data)
    gl_file_names = "; ".join(fn for _, fn in gl_data)

    def _save_failed_task(bc="", stmt_rc=0, gl_rc=0):
        try:
            return db.create_bank_recon_v2_task(
                user_id=user_id,
                tenant_id=tenant_id,
                bank_code=bc,
                gl_account=gl_account,
                stmt_files=stmt_file_names,
                gl_files=gl_file_names,
                stmt_row_count=stmt_rc,
                gl_row_count=gl_rc,
                matched_count=0,
                unmatched_gl=0,
                unmatched_stmt=0,
                stmt_opening=0,
                stmt_closing=0,
                gl_opening=0,
                gl_closing=0,
                formula_diff=0,
                detail_json=[],
                # #16 · 存 parse_info 进 summary · 让失败任务的 GET 也能显示解析诊断表
                #       (前端按 id 取结果时 renderResults 从 summary._parse_info 还原)
                summary_json={"_parse_info": parse_info},
            )
        except Exception:  # noqa: BLE001
            return None

    # 部分文件失败容错(原路由 v118.35.0.53):整侧全失败才真失败。
    # BUG-FIX-RECON-GLCSV(2026-05-25):整侧全失败**不再**静默存 done 任务 —— 否则前端按
    #   "完成"渲染 0 行结果(委托回归 P0-1/P0-2)。守铁律「低信心主动喊停·不静默出错」· 失败分流:
    #     ① 读到表格结构(有 headers/preview · needs_mapping)→ 弹『确认列对应』让用户指认列;
    #     ② 连表格都没读出(PDF/OCR 失败 / 空 / 损坏 / 无 headers)→ 明确失败(status=failed)。
    #   两种都存诊断任务(#16:失败任务的 GET/历史仍能看解析诊断表)· 但 job 绝不进 done。
    stmt_ok_n = sum(1 for r in stmt_results if r.get("ok"))
    gl_ok_n = sum(1 for r in gl_results if r.get("ok"))
    if stmt_ok_n == 0 or gl_ok_n == 0:
        failed_id = _save_failed_task()
        return _side_fail_signal(stmt_results, stmt_data, gl_results, gl_data, failed_id)

    progress_cb({"stage": "reconcile", "stage_done": 0, "stage_total": 1})

    # 3. 合并
    stmt_rows, stmt_opening, stmt_closing, bank_code = merge_statements(list(stmt_results))
    gl_rows, gl_accounts, gl_opening, gl_closing = merge_gl_files(list(gl_results), gl_account)

    # anchor 覆盖(原路由 BUG-B v118.35.0.36)
    (
        stmt_opening,
        gl_opening,
        gl_closing,
        stmt_closing,
        _anchor_ocr_snapshot,
        _anchor_used,
    ) = _apply_anchor_overrides(
        stmt_opening,
        gl_opening,
        gl_closing,
        stmt_closing,
        params.get("stmt_opening_override"),
        params.get("gl_opening_override"),
        params.get("gl_closing_override"),
        params.get("stmt_closing_override"),
    )

    if not stmt_rows or not gl_rows:
        failed_id = _save_failed_task(bc=bank_code, stmt_rc=len(stmt_rows), gl_rc=len(gl_rows))
        # 解析 ok 但合并后 0 行(罕见)· 无 mapping_request 可弹 → 明确失败 · 绝不显示完成
        return (
            "__failed__",
            {
                "result_table": "bank_recon_v2_task",
                "result_id": failed_id,
                "error_code": "no_rows",
            },
        )

    # 4. 对账
    recon_rows, summary = bank_reconcile(
        stmt_rows,
        gl_rows,
        stmt_opening=stmt_opening,
        gl_opening=gl_opening,
        stmt_closing=stmt_closing,
        gl_closing=gl_closing,
        bank_code=bank_code,
        gl_account_code=gl_account,
    )

    # 警告:输入不匹配 + 多账户 + 完整性(原路由 v118.35.0.54/61/63)
    brv2_warnings = _detect_recon_mismatch(stmt_rows, gl_rows, summary.matched_count, lang)
    _stmt_accts: list = []
    for _r in stmt_results:
        if _r.get("ok") and _r.get("multi_account"):
            _stmt_accts.extend(_r.get("account_codes") or [])
    if len(_stmt_accts) > 1:
        _seen = list(dict.fromkeys(_stmt_accts))
        brv2_warnings.append(
            _brv2_warn("multi_account", lang, n=len(_seen), codes="、".join(_seen))
        )
    _comp_details = []
    for _r in stmt_results:
        comp = _r.get("completeness") if _r.get("ok") else None
        if comp and not comp.get("ok"):
            _comp_details.extend(_completeness_details(comp["issues"], lang))
    if _comp_details:
        brv2_warnings.append(_brv2_warn("completeness", lang, detail="；".join(_comp_details[:4])))

    # 5. 序列化
    detail_j = rows_to_json(recon_rows)
    summary_j = bank_summary_to_json(summary)
    if isinstance(summary_j, dict):
        summary_j["_parse_info"] = parse_info
        summary_j["_anchor_ocr"] = _anchor_ocr_snapshot
        if _anchor_used:
            summary_j["_anchor_overrides"] = _anchor_used
        if brv2_warnings:
            summary_j["_brv2_warnings"] = brv2_warnings

    progress_cb({"stage": "persist", "stage_done": 0, "stage_total": 1})

    # 6. 落库(写现有结果表)
    unmatched_gl = summary.gl_debit_only_count + summary.gl_credit_only_count
    unmatched_stmt = summary.stmt_withdrawal_only_count + summary.stmt_deposit_only_count
    task_id = db.create_bank_recon_v2_task(
        user_id=user_id,
        tenant_id=tenant_id,
        bank_code=bank_code,
        gl_account=gl_account,
        stmt_files=stmt_file_names,
        gl_files=gl_file_names,
        stmt_row_count=len(stmt_rows),
        gl_row_count=len(gl_rows),
        matched_count=summary.matched_count,
        unmatched_gl=unmatched_gl,
        unmatched_stmt=unmatched_stmt,
        stmt_opening=stmt_opening,
        stmt_closing=stmt_closing,
        gl_opening=gl_opening,
        gl_closing=gl_closing,
        formula_diff=summary.formula_diff,
        detail_json=detail_j,
        summary_json=summary_j,
    )
    progress_cb({"stage": "done", "stage_done": 1, "stage_total": 1})
    return ("bank_recon_v2_task", task_id)


# ════════════════════════════════════════════════════════════════════
# glvat · M3 收入对账(原 recon_routes.gl_vat_run 解析→对账→落库段)
# ════════════════════════════════════════════════════════════════════
def run_glvat(
    params: dict, input_ref: List[dict], progress_cb: Optional[ProgressCb] = None
) -> Tuple[str, Any]:
    progress_cb = progress_cb or _noop
    import db
    from recon_routes import (
        parse_gl,
        parse_vat_report,
        reconcile_gl_vat,
        detail_to_json,
        summary_to_json,
        _pdf_billing_units,
    )

    revenue_prefix = params.get("revenue_prefix") or "4"
    api_key = params.get("api_key")
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
    import db
    from vat_excel_export import (
        extract_invoices_parallel,
        extract_invoices_batched_parallel,
        merge_vat_reports,
        build_excel,
    )
    from vat_excel_routes import _save_excel_file

    lang = params.get("lang") or "th"
    api_key = params.get("api_key")
    user_id = str(params.get("user_id"))
    tenant_id = params.get("tenant_id")
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

    # 发票并行 OCR(≥10 张走批量)
    invoice_files = [{"filename": fn, "bytes": b} for b, fn in invoices]
    progress_cb({"stage": "parse", "stage_done": 0, "stage_total": len(invoice_files)})
    if len(invoice_files) >= 10:
        parsed_invoices = extract_invoices_batched_parallel(
            invoice_files, api_key=api_key, batch_size=5, max_workers=4
        )
    else:
        parsed_invoices = extract_invoices_parallel(invoice_files, api_key, 10)
    ok_invoices = [r for r in parsed_invoices if r.get("ok")]
    progress_cb(
        {"stage": "parse", "stage_done": len(invoice_files), "stage_total": len(invoice_files)}
    )

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
        "invoice_file_count": len(invoice_files),
        "invoice_ocr_ok_count": len(ok_invoices),
        "invoice_ocr_failed_count": max(0, len(invoice_files) - len(ok_invoices)),
        "invoice_failed_files": [
            (r.get("filename") or "?") for r in parsed_invoices if not r.get("ok")
        ],
        **task_summary,
    }
    task_id = db.create_vat_recon_task(
        tenant_id=tenant_id,
        user_id=user_id,
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
                with db.get_cursor(commit=True) as cur:
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


_register()
