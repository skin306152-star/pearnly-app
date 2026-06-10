# -*- coding: utf-8 -*-
"""
v118.32.2 · Pearnly · 销项税对账完整路由
"""

import io
import json
import time
import logging
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import db
from core import workspace_context as wc
from services.authz.deps import require_perm
from services.vat.vat_report_parser import parse_vat_report  # noqa: F401  re-export (handlers)
from services.recon.reconciliation_matcher import run_matching
from services.recon.field_comparator import compare_all_fields
from services.vat.vat_excel_exporter import export_recon_task
from services.vat.vat_ai_analyzer import analyze_diff

# P1.2-M2 · 发票侧字段级用户校正(铁律 #21 独立 service)
from services.recon.field_override import record_field_override, ALLOWED_FIELDS as _OVERRIDE_FIELDS

# 跨组共享 helper · moved to recon_routes_shared.py
from routes.recon_routes_shared import (  # noqa: F401  re-export + facade-internal
    _user_key,
    _pdf_billing_units,
    _ROWS_PER_PAGE_BILLING,
)

# 进度子系统 · moved to recon_routes_progress.py
from routes.recon_routes_progress import (  # noqa: F401  re-export + facade-internal
    _progress_init,
    _progress_update,
    _progress_gc,
    _progress_store,
    _PROGRESS_TTL_SEC,
)

# v118.32.5 · GL vs 销项税报告 对账 · re-export(recon_jobs/handlers.py 运行时 import + tests)
from services.recon.gl_vat_reconciler import (  # noqa: F401  re-export
    parse_gl,
    reconcile_gl_vat,
    export_gl_vat_excel,
    detail_to_json,
    summary_to_json,
    detail_from_json,
    summary_from_json,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recon", tags=["recon"])


@router.get("/progress/{pid}")
async def get_progress(pid: str, request: Request):
    """v118.32.4 · C · 前端轮询拿当前阶段+当前文件+剩余预估"""
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, "未登录")
    p = _progress_store.get(pid)
    if not p:
        return {"ok": True, "stage": "unknown", "found": False}
    elapsed = time.time() - p.get("started_at", time.time())
    # 预估剩余秒数:基于本阶段已完成比例
    done = p.get("stage_done") or 0
    total = p.get("stage_total") or 0
    eta_sec = None
    if done > 0 and total > done and elapsed > 0:
        eta_sec = int(elapsed / done * (total - done))
    return {
        "ok": True,
        "found": True,
        "stage": p.get("stage", "upload"),
        "stage_done": done,
        "stage_total": total,
        "current_file": p.get("current_file", ""),
        "elapsed_sec": int(elapsed),
        "eta_sec": eta_sec,
        "stats": p.get("stats"),
        "error": p.get("error", ""),
    }


def _missing_fields(row: Dict, is_report: bool) -> List[str]:
    """v118.32.4.9 · OCR 完整性检查 · 7 字段任一缺失则返回缺失字段名列表
    散客(无 buyer_tax_id)允许跳过 buyer_tax_id / buyer_branch 两项"""
    if is_report:
        required = [
            "report_date",
            "report_invoice_no",
            "report_buyer_name",
            "report_amount_pre_vat",
            "report_vat_amount",
        ]
        tax_key = "report_buyer_tax_id"
        branch_key = "report_buyer_branch"
    else:
        required = ["invoice_date", "invoice_no", "buyer_name", "amount_pre_vat", "vat_amount"]
        tax_key = "buyer_tax_id"
        branch_key = "buyer_branch"
    miss = [k for k in required if row.get(k) in (None, "")]
    # 有税号的算公司客户 · 必须有税号 + 分公司
    if row.get(tax_key) and row.get(branch_key) in (None, ""):
        miss.append(branch_key)
    return miss


def _run_match_and_save(task_id, invoice_rows, report_rows):
    """跑配对 + 字段对比 + 写入 row · 返回 stats"""
    match = run_matching(invoice_rows, report_rows)
    to_insert = []
    for pair in match["pairs"]:
        inv = invoice_rows[pair["invoice_idx"]]
        rep = report_rows[pair["report_idx"]]
        skip_buyer = not bool(inv.get("buyer_tax_id") or rep.get("report_buyer_tax_id"))
        diff = compare_all_fields(inv, rep, skip_buyer=skip_buyer)
        # v118.32.4.9 · OCR 完整性检查 · 缺字段则加 ocr_incomplete 类
        cats = list(diff["categories"])
        if _missing_fields(inv, is_report=False) or _missing_fields(rep, is_report=True):
            if "ocr_incomplete" not in cats:
                cats.append("ocr_incomplete")
        to_insert.append(
            {
                "task_id": task_id,
                "invoice_id": pair["invoice_id"],
                "report_row_no": pair["report_row_no"],
                "pair_confidence": pair["pair_confidence"],
                "status": "matched" if not diff["has_diff"] else "mismatched",
                "diff_fields": diff["fields"],
                "diff_categories": ",".join(cats),
            }
        )
    for inv_id in match["invoice_orphans"]:
        # 反查发票行做 OCR 完整性检查
        inv_row = next((r for r in invoice_rows if r.get("id") == inv_id), {})
        cats = ["invoice_orphan"]
        if _missing_fields(inv_row, is_report=False):
            cats.append("ocr_incomplete")
        to_insert.append(
            {
                "task_id": task_id,
                "invoice_id": inv_id,
                "report_row_no": None,
                "pair_confidence": None,
                "status": "invoice_orphan",
                "diff_fields": {},
                "diff_categories": ",".join(cats),
            }
        )
    for rep_no in match["report_orphans"]:
        rep_row = next((r for r in report_rows if r.get("row_no") == rep_no), {})
        cats = ["report_orphan"]
        if _missing_fields(rep_row, is_report=True):
            cats.append("ocr_incomplete")
        to_insert.append(
            {
                "task_id": task_id,
                "invoice_id": None,
                "report_row_no": rep_no,
                "pair_confidence": None,
                "status": "report_orphan",
                "diff_fields": {},
                "diff_categories": ",".join(cats),
            }
        )
    db.bulk_insert_recon_rows(to_insert)
    stats = match["stats"]
    db.update_recon_task_completed(
        task_id,
        {
            "status": "completed",
            "matched_count": sum(1 for r in to_insert if r["status"] == "matched"),
            "mismatched_count": sum(1 for r in to_insert if r["status"] == "mismatched"),
            "invoice_orphan_count": stats["invoice_orphan_count"],
            "report_orphan_count": stats["report_orphan_count"],
            "invoice_count_archived": stats["total_invoices"],
            "report_row_count": stats["total_report_rows"],
        },
    )
    return stats


# ======================================================================
# 屏 A
# ======================================================================


class CreateTaskBody(BaseModel):
    client_id: int
    period_year: int
    period_month: int
    vat_report_id: int


@router.post("/task")
async def create_task(body: CreateTaskBody, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    task_id = db.create_recon_task(
        tenant_id=user.get("tenant_id"),
        user_id=str(user["id"]),
        client_id=body.client_id,
        period_year=body.period_year,
        period_month=body.period_month,
        vat_report_id=body.vat_report_id,
    )
    if not task_id:
        raise HTTPException(409, "该客户本月已有进行中的对账任务")
    return {"ok": True, "task_id": task_id}


@router.post("/run/{task_id}")
async def run_recon(
    task_id: int, request: Request, progress_id: Optional[str] = None, is_last: int = 0
):
    """v118.32.4 · 可带 progress_id 上报 match 阶段;is_last=1 时标记 done"""
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    task = db.get_recon_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    # 套账隔离:取当前请求的活动主体,只对账本主体的识别记录(ocr_history 读侧已隔离,
    # 这里是对账源查询的同一过滤)。rollout-safe:解析不到 → None → 旧行为不变。
    ws = wc.active_workspace_for_request(request, task.get("tenant_id"))
    # v118.32.4.3 · 屏 B 流程优先按 source_ref=task_id 取本次任务关联的发票(隔离历史 OCR 缓存)
    # 无结果(屏 A 流程:用户手动跑对账)再按 客户+期间 老逻辑
    invoice_rows = db.list_invoices_for_recon(
        tenant_id=task.get("tenant_id"),
        client_id=task["client_id"],
        period_year=task["period_year"],
        period_month=task["period_month"],
        source_ref=str(task_id),
        workspace_client_id=ws,
    )
    if not invoice_rows:
        invoice_rows = db.list_invoices_for_recon(
            tenant_id=task.get("tenant_id"),
            client_id=task["client_id"],
            period_year=task["period_year"],
            period_month=task["period_month"],
            workspace_client_id=ws,
        )
    report = db.get_vat_report(task["vat_report_id"])
    report_rows = (report or {}).get("parsed_rows") or []
    db.update_recon_task_status(task_id, "running")
    try:
        # 上报当前正在匹配哪个客户
        if progress_id and progress_id in _progress_store:
            client = db.get_client_by_id(task["client_id"]) if task.get("client_id") else {}
            _progress_update(
                progress_id, current_file=(client or {}).get("name", "") or f"task {task_id}"
            )
        import asyncio

        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None, _run_match_and_save, task_id, invoice_rows, report_rows
        )
        if progress_id and progress_id in _progress_store:
            cur = _progress_store[progress_id]
            cur_done = (cur.get("stage_done") or 0) + 1
            _progress_update(progress_id, stage_done=cur_done)
            if is_last:
                # 累计 stats(简单累加)
                acc = cur.get("stats") or {
                    "matched": 0,
                    "mismatched": 0,
                    "invoice_orphans": 0,
                    "report_orphans": 0,
                }
                # 注:这里只能拿到本任务的 stats · 总 stats 由前端聚合也行
                _progress_update(progress_id, stage="done", stats=acc)
        return {"ok": True, "task_id": task_id, "stats": stats}
    except Exception as e:
        logger.error(f"run_recon: {e}")
        db.update_recon_task_status(task_id, "failed")
        if progress_id and progress_id in _progress_store:
            _progress_update(progress_id, error=str(e)[:200])
        raise HTTPException(500, str(e))


@router.get("/result/{task_id}")
async def get_result(task_id: int, request: Request):
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, "未登录")
    task = db.get_recon_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    rows = db.list_recon_rows_detailed(task_id)
    # v118.32.2.5 · 补 client 给屏 C 头部用
    client = db.get_client_by_id(task["client_id"]) if task.get("client_id") else {}
    return {"ok": True, "task": task, "rows": rows, "client": client or {}}


@router.post("/row/{row_id}/analyze")
async def row_ai(row_id: int, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    row = db.get_recon_row(row_id)
    if not row:
        raise HTTPException(404, "行不存在")
    if row.get("ai_analysis"):
        ai = row["ai_analysis"]
        if isinstance(ai, str):
            try:
                ai = json.loads(ai)
            except:
                pass
        return {"ok": True, "analysis": ai, "ai": ai, "cached": True}

    result = analyze_diff(row, api_key=_user_key(user))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "AI 分析失败"))
    db.update_recon_row_ai_analysis(row_id, result)
    return {"ok": True, "analysis": result, "ai": result, "cached": False}


class RowActionBody(BaseModel):
    action: str
    notes: Optional[str] = None
    source: Optional[str] = (
        None  # v118.32.4.8 "invoice"|"report" + v118.32.4.9 "both" (两边都对 · 同一笔)
    )


@router.post("/row/{row_id}/action")
async def row_action(row_id: int, body: RowActionBody, request: Request):
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    if body.action not in ("pending", "resolved", "customer_issue", "accepted_diff"):
        raise HTTPException(400, "invalid action")
    # 把 source 拼进 notes(不改 db schema · 用 "source=invoice|report|both" 前缀)
    notes_payload = body.notes or ""
    if body.source in ("invoice", "report", "both"):
        prefix = f"source={body.source}"
        notes_payload = prefix + (" · " + body.notes if body.notes else "")
    db.update_recon_row_action(row_id, body.action, notes_payload or None)
    return {"ok": True}


class FieldOverrideBody(BaseModel):
    field: str
    user_value: Optional[str] = None  # 空/None = 撤销该字段校正(还原 OCR)


@router.patch("/row/{row_id}/field")
async def row_field_override(row_id: int, body: FieldOverrideBody, request: Request):
    """P1.2-M2 · 用户校正发票侧 OCR 字段 · 记 OCR 原值 vs 用户值到 field_overrides"""
    user = require_perm(request, "recon.create")
    if not user:
        raise HTTPException(401, "未登录")
    if body.field not in _OVERRIDE_FIELDS:
        raise HTTPException(400, "field not allowed")
    result = record_field_override(row_id, body.field, body.user_value)
    if not result.get("ok"):
        err = result.get("error", "update failed")
        raise HTTPException(404 if err == "row_not_found" else 400, err)
    return {"ok": True, "field_overrides": result["field_overrides"]}


# ======================================================================
# 任务列表 · Excel 导出
# ======================================================================


@router.get("/tasks")
async def list_tasks(request: Request, client_id: Optional[int] = None):
    user = require_perm(request, "recon.view")
    if not user:
        raise HTTPException(401, "未登录")
    tasks = db.list_recon_tasks(
        tenant_id=user.get("tenant_id"), user_id=str(user["id"]), client_id=client_id
    )
    return {"ok": True, "tasks": tasks}


@router.get("/export/{task_id}")
async def export_excel(task_id: int, request: Request, lang: str = "th"):
    """v118.32.3 · F2 · lang 参数接收前端当前界面语言(th/zh/en/ja)· 默认泰文给税局"""
    user = require_perm(request, "recon.export")
    if not user:
        raise HTTPException(401, "未登录")
    if lang not in ("th", "zh", "en", "ja"):
        lang = "th"
    task = db.get_recon_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    rows = db.list_recon_rows_detailed(task_id)
    client = {}
    if task.get("client_id"):
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT id, name, tax_id, address FROM clients WHERE id = %s", (task["client_id"],)
            )
            r = cur.fetchone()
            if r:
                client = dict(r)

    vat_report = db.get_vat_report(task["vat_report_id"]) if task.get("vat_report_id") else {}
    excel_bytes = export_recon_task(task, rows, client, vat_report or {}, lang=lang)

    period_str = f"{task['period_year']}{task['period_month']:02d}"
    filename = f"VAT_recon_{client.get('name','client')}_{period_str}.xlsx"
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={safe_name}"},
    )


# 批量识别 + 任务删除路由组 · moved to recon_routes_v1_batch.py(verbatim 抽出)
from routes.recon_routes_v1_batch import v1batch_router  # noqa: E402

router.include_router(v1batch_router)


# ════════════════════════════════════════════════════════════════════
# GL-VAT 对账路由组 · moved to recon_routes_glvat.py(verbatim 抽出)
# ════════════════════════════════════════════════════════════════════
from routes.recon_routes_glvat import glvat_router  # noqa: E402

router.include_router(glvat_router)


# ════════════════════════════════════════════════════════════════════
# Bank-v2 对账路由组 · moved to recon_routes_bankv2*.py(verbatim 抽出)
# ════════════════════════════════════════════════════════════════════
from routes.recon_routes_bankv2 import bankv2_router  # noqa: E402

# re-export bank-v2 surface · recon_jobs/handlers.py 运行时 `from recon_routes import ...`
# 拉这批名字(原 bank_v2_run 解析段同名函数)+ 测试 patch recon_routes.X / 直接调 handler。
# verbatim 搬出后必须保契约,否则 worker import 崩 + monkeypatch 失效。
from routes.recon_routes_bankv2_helpers import (  # noqa: F401,E402  re-export (handlers/tests)
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
)
from routes.recon_routes_bankv2_run import bank_v2_run  # noqa: F401,E402  re-export
from routes.recon_routes_bankv2 import (  # noqa: F401,E402  re-export (tests 直接调 handler)
    bank_v2_get_task,
    bank_v2_export,
    bank_v2_list_tasks,
    bank_v2_delete,
    bank_v2_batch_delete,
)

router.include_router(bankv2_router)
