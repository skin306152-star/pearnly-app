# -*- coding: utf-8 -*-
"""Bank-v2 对账执行路由 POST /api/recon/bank-v2/run（含计费主路径·铁律#26）。

recon_routes 拆分·bank_v2_run verbatim 抽出·0 逻辑改(仅装饰器对象名)。"""

import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request

from core import db
from core import workspace_context as wc
from core.route_helpers import _tid
from services.authz.deps import require_perm
from routes.recon_routes_shared import _user_key, _pdf_billing_units
from routes.recon_routes_bankv2_helpers import (
    _BANK_V2_OK,
    parse_bank_statement_pdf,
    parse_gl_v2,
    merge_statements,
    merge_gl_files,
    bank_reconcile,
    bank_summary_to_json,
    rows_to_json,
    _apply_anchor_overrides,
    _brv2_err,
    _brv2_warn,
    _completeness_details,
    _detect_recon_mismatch,
)

logger = logging.getLogger(__name__)

bankv2_run_router = APIRouter()


@bankv2_run_router.post("/bank-v2/run")
async def bank_v2_run(
    request: Request,
    stmt_files: List[UploadFile] = File(...),
    gl_files: List[UploadFile] = File(...),
    gl_account: str = Form(""),
    lang: str = Form("th"),
    # BUG-B v118.35.0.36 (2026-05-22) · OCR 抽 3 个 anchor 余额不准时 · 前端用户手动录入兜底
    # 任意一个 override 非 None · 用 override 替换 OCR/parse 抽到的值传给 bank_reconcile
    # 整顿期 (铁律 #18) Zihao 拍板破例做 · 业务等式锚点错位会让整张对账报告废 · 算紧急
    # BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing(Statement 期末)· 客户反馈
    stmt_opening_override: Optional[float] = Form(None),
    gl_opening_override: Optional[float] = Form(None),
    gl_closing_override: Optional[float] = Form(None),
    stmt_closing_override: Optional[float] = Form(None),
):
    """
    Upload bank statement PDF(s) + GL file(s), run reconciliation.
    Returns {ok, task_id, stats, detail, summary, gl_accounts}
    """
    if not _BANK_V2_OK:
        raise HTTPException(503, "Bank Recon v2 module not available on this server")
    import asyncio

    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, _brv2_err("auth_required", lang))

    if not stmt_files:
        raise HTTPException(422, _brv2_err("no_stmt_files", lang))
    if not gl_files:
        raise HTTPException(422, _brv2_err("no_gl_files", lang))

    # v118.35.0.21 · Credits 前置检查(1 次 SELECT · 异步扣费)
    _billing_bv2 = {"is_exempt": True, "pages_used_this_month": 0}
    try:
        from core import db as _db_credit

        _tid_bv2 = user.get("tenant_id")
        _billing_bv2 = _db_credit.get_billing_status_combined(str(user.get("id")), _tid_bv2)
        if not _billing_bv2.get("allowed") and not _billing_bv2.get("is_exempt"):
            _est_cost = float(
                _db_credit.estimate_pdf_cost_thb(
                    _billing_bv2.get("pages_used_this_month", 0), len(stmt_files) + len(gl_files)
                )
            )
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": _billing_bv2.get("balance_thb", 0.0),
                    "estimated_cost": _est_cost,
                    "pages_used_this_month": _billing_bv2.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as _be:
        import logging as _lg_pre

        _lg_pre.getLogger("recon").warning(f"[bank_v2.credits] pre-check skip: {_be}")

    # v118.33.12.1 · use _user_key (gemini_api_key OR custom_gemini_api_key)
    # to match the rest of the system; fall back to env GEMINI_API_KEY.
    import os as _os
    import logging as _lg

    api_key = (_user_key(user) or _os.environ.get("GEMINI_API_KEY", "")).strip()
    _lg.getLogger("recon").info(
        f"[bank_v2_run] api_key_present={bool(api_key)} user_id={user.get('id')}"
    )
    loop = asyncio.get_event_loop()

    # 1. Read all uploaded files
    stmt_data = []
    for f in stmt_files:
        content = await f.read()
        stmt_data.append((content, f.filename or "statement.pdf"))

    gl_data = []
    for f in gl_files:
        content = await f.read()
        gl_data.append((content, f.filename or "gl.xlsx"))

    # 2. Parse statement files (parallel) · ADR-006 透传 tenant_id 给模板学习层
    _tid_stmt = user.get("tenant_id")

    async def _parse_stmt(b, fname):
        return await loop.run_in_executor(
            None, lambda: parse_bank_statement_pdf(b, fname, api_key, tenant_id=_tid_stmt)
        )

    async def _parse_gl(b, fname):
        return await loop.run_in_executor(
            None, lambda: parse_gl_v2(b, fname, gl_account, api_key, tenant_id=_tid_stmt)
        )

    stmt_results = await asyncio.gather(*[_parse_stmt(b, fn) for b, fn in stmt_data])
    gl_results = await asyncio.gather(*[_parse_gl(b, fn) for b, fn in gl_data])

    # v118.35.0.21 · 异步扣费 · 按文件扩展名分 pdf/excel 两种 kind
    if not _billing_bv2.get("is_exempt"):
        try:
            from core import db as _db_chg
            from services.ocr.pdf_utils import count_pdf_pages as _count_pages_chg

            _tid_chg = user.get("tenant_id")
            _excel_exts = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}
            # v118.35.0.58 · BUG 修复:PDF/图片改按『页』计费(对齐 ฿1.5/页规则)· 此前误按交易行数收 · 超收 10-34 倍
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
                    _excel_units += _db_chg._excel_char_count_estimate(b, fn)
                else:
                    _pdf_units += _pdf_billing_units(_count_pages_chg(b) or 1, row_count)
            if _pdf_units > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        _db_chg.charge_ocr_async,
                        str(user.get("id")),
                        _tid_chg,
                        "pdf",
                        _pdf_units,
                        None,
                        f"银行对账 PDF · {_pdf_units} 页",
                    )
                )
            if _excel_units > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        _db_chg.charge_ocr_async,
                        str(user.get("id")),
                        _tid_chg,
                        "excel",
                        _excel_units,
                        None,
                        f"银行对账 Excel · {_excel_units} 字符",
                    )
                )
        except Exception as _ce:
            import logging as _lg_ce

            _lg_ce.getLogger("recon").warning(f"💳 bank_v2 async charge skip: {_ce}")

    # v118.35.0.19 · per-file parse diagnostics 带 error_code 字段 · 前端用它做 i18n 翻译
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
                user_id=str(user["id"]),
                tenant_id=user.get("tenant_id"),
                workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
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
                summary_json={},
            )
        except Exception:
            return None

    # v118.35.0.53 · 部分文件失败容错:一个坏文件不再拖垮整批。
    # merge_statements/merge_gl_files 本就跳过 not-ok 的结果 · 这里只在『某一侧全部失败』时硬报错。
    # 部分失败 → 跳过坏文件、用成功的继续 · 失败文件在 parse_info 里逐个标出(前端可显示)。
    stmt_ok_n = sum(1 for r in stmt_results if r.get("ok"))
    gl_ok_n = sum(1 for r in gl_results if r.get("ok"))
    stmt_errors = [r.get("error") for r in stmt_results if not r.get("ok")]
    gl_errors = [r.get("error") for r in gl_results if not r.get("ok")]
    skipped_files = [fn for r, (_, fn) in zip(stmt_results, stmt_data) if not r.get("ok")] + [
        fn for r, (_, fn) in zip(gl_results, gl_data) if not r.get("ok")
    ]
    if stmt_ok_n == 0 or gl_ok_n == 0:
        # 整侧全失败才真失败(对账单全坏 或 GL 全坏)
        err_key = "stmt_parse_fail" if stmt_ok_n == 0 else "gl_parse_fail"
        err_msg = _brv2_err(err_key, lang, e="; ".join(filter(None, (stmt_errors + gl_errors)[:2])))
        failed_id = _save_failed_task()
        return {
            "ok": False,
            "error": err_msg,
            "task_id": failed_id,
            "parse_info": parse_info,
            "stats": {},
            "detail": [],
            "summary": {},
            "gl_accounts": [],
        }

    # 3. Merge multi-file data
    stmt_rows, stmt_opening, stmt_closing, bank_code = merge_statements(list(stmt_results))
    gl_rows, gl_accounts, gl_opening, gl_closing = merge_gl_files(list(gl_results), gl_account)

    # BUG-B v118.35.0.36 · 用户在前端 anchor TEXT BOX 填了值就用用户的 · OCR 的降级成参考
    # P0.1 BUG-B-T1 v118.35.0.37 · 抽成 _apply_anchor_overrides 纯函数 · 总是 snapshot OCR 给前端预填用
    # BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing
    stmt_opening, gl_opening, gl_closing, stmt_closing, _anchor_ocr_snapshot, _anchor_used = (
        _apply_anchor_overrides(
            stmt_opening,
            gl_opening,
            gl_closing,
            stmt_closing,
            stmt_opening_override,
            gl_opening_override,
            gl_closing_override,
            stmt_closing_override,
        )
    )
    if _anchor_used:
        logger.info(
            f"[bank_v2_run] anchor overrides applied: {_anchor_used} · " f"user_id={user.get('id')}"
        )

    # No rows found → save diagnostic task, return 200 ok:false (not 422)
    if not stmt_rows or not gl_rows:
        err_key = "stmt_no_rows" if not stmt_rows else "gl_no_rows"
        err_msg = _brv2_err(err_key, lang)
        failed_id = _save_failed_task(
            bc=bank_code,
            stmt_rc=len(stmt_rows),
            gl_rc=len(gl_rows),
        )
        return {
            "ok": False,
            "error": err_msg,
            "task_id": failed_id,
            "parse_info": parse_info,
            "stats": {},
            "detail": [],
            "summary": {},
            "gl_accounts": list(gl_accounts),
        }

    # 4. Reconcile
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

    # v118.35.0.54 · 输入不匹配检测(期间/科目/规模对不上)· 主动警告 · 不让用户看不懂差额
    brv2_warnings = _detect_recon_mismatch(stmt_rows, gl_rows, summary.matched_count, lang)

    # v118.35.0.61 · 多账户文件检测(一个文件塞多个账户 · 每 sheet 一个)· 已分账户独立校验
    # · 主动提示『需 GL 对应单一账户』· 避免用户拿多账户文件对单账户 GL 还以为系统坏了。
    _stmt_accts: list = []
    for _r in stmt_results:
        if _r.get("ok") and _r.get("multi_account"):
            _stmt_accts.extend(_r.get("account_codes") or [])
    if len(_stmt_accts) > 1:
        _seen = list(dict.fromkeys(_stmt_accts))  # 去重保序
        brv2_warnings.append(
            _brv2_warn("multi_account", lang, n=len(_seen), codes="、".join(_seen))
        )

    # v118.35.0.63 · 完整性交叉校验:提取行 vs 账单印刷合计/笔数/期末对不上 → 主动提示漏行
    _comp_details = []
    for _r in stmt_results:
        comp = _r.get("completeness") if _r.get("ok") else None
        if comp and not comp.get("ok"):
            _comp_details.extend(_completeness_details(comp["issues"], lang))
    if _comp_details:
        brv2_warnings.append(_brv2_warn("completeness", lang, detail="；".join(_comp_details[:4])))

    # 5. Serialize
    detail_j = rows_to_json(recon_rows)
    summary_j = bank_summary_to_json(summary)
    # v118.33.13.3 · embed real per-file parse_info into summary_json so the
    # Excel "File Info" sheet shows accurate per-file rows/bank when exporting
    # from history (previously it reconstructed bogus data using totals).
    # summary_from_json filters out unknown keys, so this is non-invasive.
    if isinstance(summary_j, dict):
        summary_j["_parse_info"] = parse_info
        # P0.1 BUG-B-T1 v118.35.0.37 · 总是落库 OCR snapshot · 给前端 localStorage 预填 + P0.3 历史详情对照用
        summary_j["_anchor_ocr"] = _anchor_ocr_snapshot
        # BUG-B v118.35.0.36 · 落库 anchor 覆盖痕迹 · 用户回查任务时能看出哪几个 anchor 是手填的
        if _anchor_used:
            summary_j["_anchor_overrides"] = _anchor_used
        # v118.35.0.61 · 落库输入不匹配警告 · 导出 Excel 时重传 · 让文件与前端提示同源
        if brv2_warnings:
            summary_j["_brv2_warnings"] = brv2_warnings

    # 6. Persist
    unmatched_gl = summary.gl_debit_only_count + summary.gl_credit_only_count
    unmatched_stmt = summary.stmt_withdrawal_only_count + summary.stmt_deposit_only_count

    task_id = db.create_bank_recon_v2_task(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
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

    return {
        "ok": True,
        "task_id": task_id,
        "bank_code": bank_code,
        "gl_accounts": gl_accounts,
        "stmt_row_count": len(stmt_rows),
        "gl_row_count": len(gl_rows),
        "skipped_files": skipped_files,  # v118.35.0.53 · 部分失败被跳过的文件 · 前端可提示
        "warnings": brv2_warnings,  # v118.35.0.54 · 输入不匹配警告(期间/规模)· 前端显示提示条
        "parse_info": parse_info,
        "stats": {
            "matched": summary.matched_count,
            "gl_debit_only": summary.gl_debit_only_count,
            "gl_credit_only": summary.gl_credit_only_count,
            "stmt_withdrawal_only": summary.stmt_withdrawal_only_count,
            "stmt_deposit_only": summary.stmt_deposit_only_count,
            "total": len(recon_rows),
            "formula_diff": summary.formula_diff,
        },
        "detail": detail_j,
        "summary": summary_j,
    }
