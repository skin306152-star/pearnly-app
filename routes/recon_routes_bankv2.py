# -*- coding: utf-8 -*-
"""Bank-v2 对账 CRUD 路由组（/api/recon/bank-v2/* · list/get/export/delete/batch）。

recon_routes 拆分·verbatim 抽出·聚合 run 子路由对外暴露 bankv2_router。"""

import io
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import db
from core import workspace_context as wc
from core.route_helpers import _tid
from services.authz.deps import require_perm
from routes.recon_routes_bankv2_helpers import (
    _brv2_err,
    bank_summary_from_json,
    export_bank_recon_excel,
    rows_from_json,
)
from routes.recon_routes_bankv2_run import bankv2_run_router

logger = logging.getLogger(__name__)

bankv2_router = APIRouter()


@bankv2_router.get("/bank-v2/tasks")
async def bank_v2_list_tasks(request: Request):
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, "未登录")
    tasks = db.list_bank_recon_v2_tasks(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        limit=50,
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
    )
    return {"ok": True, "tasks": tasks}


@bankv2_router.get("/bank-v2/{task_id}")
async def bank_v2_get_task(task_id: int, request: Request):
    """v118.35.0.29 P0 隔离 (体检 2026-05-21 风险 2) · 镜像 gl_vat 修复"""
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, "未登录")
    task = db.get_bank_recon_v2_task(
        task_id,
        str(user["id"]),
        user.get("tenant_id"),
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
    )
    if not task:
        raise HTTPException(404, _brv2_err("task_not_found", "th"))
    import json as _j

    def _safe_json(v):
        if isinstance(v, str):
            try:
                return _j.loads(v)
            except:
                return v
        return v

    summary = _safe_json(task.get("summary_json")) or {}
    summary = summary if isinstance(summary, dict) else {}
    # BUG-FIX-RECON-ASYNC #16 · 把 run 响应里的顶层 stats / parse_info / warnings 从 summary_json
    # 还原出来 · 让"按 id 取结果"(异步完成 + 历史载入)渲染跟同步跑一模一样(不丢解析诊断表/
    # 警告条/未匹配 KPI)· summary_json = asdict(BankReconSummary),含所有 *_count 字段。
    return {
        "ok": True,
        "task_id": task["id"],
        "bank_code": task.get("bank_code"),
        "gl_account": task.get("gl_account"),
        "stmt_files": task.get("stmt_files"),
        "gl_files": task.get("gl_files"),
        "stmt_row_count": task.get("stmt_row_count"),
        "gl_row_count": task.get("gl_row_count"),
        "stats": {
            "matched": summary.get("matched_count", task.get("matched_count") or 0),
            "gl_debit_only": summary.get("gl_debit_only_count", 0),
            "gl_credit_only": summary.get("gl_credit_only_count", 0),
            "stmt_withdrawal_only": summary.get("stmt_withdrawal_only_count", 0),
            "stmt_deposit_only": summary.get("stmt_deposit_only_count", 0),
            "total": (task.get("matched_count") or 0)
            + (task.get("unmatched_gl") or 0)
            + (task.get("unmatched_stmt") or 0),
            "formula_diff": summary.get("formula_diff", task.get("formula_diff") or 0),
            # 兼容老调用方(历史抽屉等可能读旧字段名)
            "unmatched_gl": task.get("unmatched_gl") or 0,
            "unmatched_stmt": task.get("unmatched_stmt") or 0,
        },
        # 顶层 parse_info / warnings(renderResults 从顶层读)· 落库时存在 summary 里
        "parse_info": summary.get("_parse_info"),
        "warnings": summary.get("_brv2_warnings") or [],
        "stmt_opening": float(task.get("stmt_opening") or 0),
        "stmt_closing": float(task.get("stmt_closing") or 0),
        "gl_opening": float(task.get("gl_opening") or 0),
        "gl_closing": float(task.get("gl_closing") or 0),
        "formula_diff": float(task.get("formula_diff") or 0),
        "detail": _safe_json(task.get("detail_json")),
        "summary": summary,
        "created_at": str(task.get("created_at") or ""),
    }


@bankv2_router.get("/bank-v2/{task_id}/export")
async def bank_v2_export(task_id: int, request: Request, lang: str = "th"):
    """Export reconciliation result as Excel."""
    import json as _j
    import urllib.parse

    user = require_perm(request, "recon.export")
    if not user:
        raise HTTPException(401, "未登录")
    if lang not in ("th", "zh", "en", "ja"):
        lang = "th"

    # v118.35.0.29 P0 隔离修复(体检风险 2) · 强制 user_id + tenant_id scope
    task = db.get_bank_recon_v2_task(
        task_id,
        str(user["id"]),
        user.get("tenant_id"),
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
    )
    if not task:
        raise HTTPException(404, "任务不存在")

    def _sj(v):
        if isinstance(v, str):
            try:
                return _j.loads(v)
            except:
                return []
        return v or []

    detail_raw = _sj(task.get("detail_json"))
    summary_raw = (
        _sj(task.get("summary_json")) if isinstance(_sj(task.get("summary_json")), dict) else {}
    )

    recon_rows = rows_from_json(detail_raw)
    summary = bank_summary_from_json(summary_raw)

    # v118.33.13.3 · Use the real parse_info that was saved at run time if available,
    # otherwise fall back to the old reconstruction (which is bogus — every file
    # shows the TOTAL row count and the OVERALL bank_code).
    saved_parse_info = summary_raw.get("_parse_info") if isinstance(summary_raw, dict) else None
    if saved_parse_info and isinstance(saved_parse_info, dict):
        task_parse_info = saved_parse_info
    else:
        task_parse_info = {
            "stmt_files": [
                {
                    "file": f.strip(),
                    "rows": task.get("stmt_row_count", 0),
                    "ok": True,
                    "bank_code": task.get("bank_code", ""),
                }
                for f in (task.get("stmt_files") or "").split(";")
                if f.strip()
            ],
            "gl_files": [
                {
                    "file": f.strip(),
                    "rows": task.get("gl_row_count", 0),
                    "ok": True,
                    "accounts": [task.get("gl_account") or ""],
                }
                for f in (task.get("gl_files") or "").split(";")
                if f.strip()
            ],
        }
    # P0.2 BUG-B-T2 v118.35.0.38 · summary_raw 还含 _anchor_overrides + _anchor_ocr · 单独传给 export
    # bank_summary_from_json 过滤掉 `_` 开头字段 · 所以这里要从原 summary_raw 拿
    _ao = summary_raw.get("_anchor_overrides") if isinstance(summary_raw, dict) else None
    _aocr = summary_raw.get("_anchor_ocr") if isinstance(summary_raw, dict) else None
    _warns = summary_raw.get("_brv2_warnings") if isinstance(summary_raw, dict) else None
    excel_bytes = export_bank_recon_excel(
        recon_rows,
        summary,
        lang=lang,
        task_info=task,
        parse_info=task_parse_info,
        anchor_overrides=_ao,
        anchor_ocr=_aocr,
        warnings=_warns,
    )

    bank_code = task.get("bank_code") or "bank"
    ascii_name = f"BankRecon_v2_{task_id}_{bank_code.upper()}.xlsx"
    utf8_name = urllib.parse.quote(ascii_name)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={ascii_name}; filename*=UTF-8''{utf8_name}"
        },
    )


@bankv2_router.delete("/bank-v2/{task_id}")
async def bank_v2_delete(task_id: int, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    ok = db.delete_bank_recon_v2_task(task_id, str(user["id"]), user.get("tenant_id"))
    if not ok:
        raise HTTPException(404, "任务不存在或无权删除")
    return {"ok": True}


class _BankV2BatchDeleteBody(BaseModel):
    ids: List[int]


@bankv2_router.post("/bank-v2/tasks/batch_delete")
async def bank_v2_batch_delete(body: _BankV2BatchDeleteBody, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    if not body.ids:
        return {"deleted": 0}
    deleted = db.delete_bank_recon_v2_tasks_batch(body.ids, str(user["id"]), user.get("tenant_id"))
    return {"deleted": int(deleted)}


# 聚合 run 子路由(POST /bank-v2/run)→ 对外单一 bankv2_router
bankv2_router.include_router(bankv2_run_router)
