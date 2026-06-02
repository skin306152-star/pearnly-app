# -*- coding: utf-8 -*-
"""对账重活 · M4 银行对账 handler(run_bank_recon)· ADR-005。"""

from __future__ import annotations

import logging
import os
from typing import Any, List, Optional, Tuple

from ._handler_common import _read_inputs, _noop, _side_fail_signal, _parallel, ProgressCb

logger = logging.getLogger("recon_jobs.handlers")


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
