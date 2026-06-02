# -*- coding: utf-8 -*-
"""
v118.32.2 · Pearnly · 销项税对账完整路由
"""

import io
import json
import time
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import db
from auth import get_current_user_from_request
from vat_report_parser import parse_vat_report
from reconciliation_matcher import run_matching
from field_comparator import compare_all_fields
from vat_excel_exporter import export_recon_task
from vat_ai_analyzer import analyze_diff

# P1.2-M2 · 发票侧字段级用户校正(铁律 #21 独立 service)
from services.recon.field_override import record_field_override, ALLOWED_FIELDS as _OVERRIDE_FIELDS

# 跨组共享 helper · moved to recon_routes_shared.py
from recon_routes_shared import (  # noqa: F401  re-export + facade-internal
    _user_key,
    _pdf_billing_units,
    _ROWS_PER_PAGE_BILLING,
)

# v118.32.5 · GL vs 销项税报告 对账
from gl_vat_reconciler import (
    parse_gl,
    reconcile_gl_vat,
    export_gl_vat_excel,
    detail_to_json,
    summary_to_json,
    detail_from_json,
    summary_from_json,
)

# v118.32.5 · GL 对账错误消息 i18n（4 语言）
_GLV_ERR = {
    "auth_required": {
        "zh": "未登录",
        "en": "Not logged in",
        "th": "ยังไม่ได้เข้าสู่ระบบ",
        "ja": "未ログイン",
    },
    "gl_parse_failed": {
        "zh": "GL 解析失败：{e}",
        "en": "Failed to parse GL: {e}",
        "th": "อ่านไฟล์ GL ไม่สำเร็จ: {e}",
        "ja": "GL 解析失敗: {e}",
    },
    "gl_no_revenue_rows": {
        "zh": "在文件里没找到收入科目数据。请确认右侧上传的是『总账 GL』(Excel/CSV · 至少含日期/科目/借方/贷方列)· 如果你的收入科目不是 4 开头,请调右侧『收入科目前缀』",
        "en": "No revenue account rows found. Please upload a General Ledger file (Excel/CSV with Date/Account/Debit/Credit columns) · If your revenue accounts don't start with '4', adjust the 'Revenue Account Prefix' on the right",
        "th": "ไม่พบรายการบัญชีรายได้ในไฟล์ · กรุณาอัปโหลดบัญชีแยกประเภท GL (Excel/CSV ที่มีคอลัมน์ วันที่/รหัสบัญชี/เดบิต/เครดิต) · หากบัญชีรายได้ไม่ขึ้นต้นด้วย 4 ให้ปรับ 'รหัสนำหน้าบัญชีรายได้' ด้านขวา",
        "ja": "ファイルに収益科目データが見つかりません · 右側に『総勘定元帳 GL』(日付/科目/借方/貸方列のある Excel/CSV) をアップロードしてください · 収益科目が 4 以外で始まる場合は右側の『収益科目接頭辞』を変更してください",
    },
    "vat_parse_failed": {
        "zh": "销项税报告解析失败：{e}",
        "en": "Failed to parse VAT report: {e}",
        "th": "อ่านรายงานภาษีขายไม่สำเร็จ: {e}",
        "ja": "売上税報告解析失敗: {e}",
    },
    "vat_no_rows": {
        "zh": "销项税报告中未找到任何数据行",
        "en": "No data rows found in VAT report",
        "th": "ไม่พบรายการในรายงานภาษีขาย",
        "ja": "売上税報告にデータ行が見つかりません",
    },
    "task_not_found": {
        "zh": "任务不存在",
        "en": "Task not found",
        "th": "ไม่พบงาน",
        "ja": "タスクが見つかりません",
    },
}


def _glv_err(key: str, lang: str = "th", **fmt) -> str:
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    msg = (_GLV_ERR.get(key) or {}).get(lang) or _GLV_ERR.get(key, {}).get("en") or key
    return msg.format(**fmt) if fmt else msg


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recon", tags=["recon"])


# v118.32.4 · C 进度反馈业务化 · 内存进度存储(60 分钟 TTL)
# 5 个业务阶段:upload / parse_report / ocr_invoices / match / done
_progress_store: Dict[str, Dict[str, Any]] = {}
_PROGRESS_TTL_SEC = 3600


def _progress_init(pid: str, **kwargs):
    if not pid:
        return
    _progress_gc()
    _progress_store[pid] = {
        "stage": "upload",
        "stage_done": 0,
        "stage_total": 0,
        "current_file": "",
        "started_at": time.time(),
        "updated_at": time.time(),
        "stats": None,
        "error": "",
        **kwargs,
    }


def _progress_update(pid: str, **kwargs):
    if not pid or pid not in _progress_store:
        return
    _progress_store[pid].update(kwargs)
    _progress_store[pid]["updated_at"] = time.time()


def _progress_gc():
    now = time.time()
    stale = [
        k for k, v in _progress_store.items() if now - v.get("updated_at", 0) > _PROGRESS_TTL_SEC
    ]
    for k in stale:
        _progress_store.pop(k, None)


@router.get("/progress/{pid}")
async def get_progress(pid: str, request: Request):
    """v118.32.4 · C · 前端轮询拿当前阶段+当前文件+剩余预估"""
    user = get_current_user_from_request(request)
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
    user = get_current_user_from_request(request)
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
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    task = db.get_recon_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    # v118.32.4.3 · 屏 B 流程优先按 source_ref=task_id 取本次任务关联的发票(隔离历史 OCR 缓存)
    # 无结果(屏 A 流程:用户手动跑对账)再按 客户+期间 老逻辑
    invoice_rows = db.list_invoices_for_recon(
        tenant_id=task.get("tenant_id"),
        client_id=task["client_id"],
        period_year=task["period_year"],
        period_month=task["period_month"],
        source_ref=str(task_id),
    )
    if not invoice_rows:
        invoice_rows = db.list_invoices_for_recon(
            tenant_id=task.get("tenant_id"),
            client_id=task["client_id"],
            period_year=task["period_year"],
            period_month=task["period_month"],
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


# ======================================================================
# 屏 B · 批量智能识别
# ======================================================================


@router.post("/batch_process")
async def batch_process(
    request: Request,
    confirmed_groups_json: str = Form(...),
    files: List[UploadFile] = File(...),
    progress_id: Optional[str] = Form(None),
):
    """v118.32.2 · 屏 B · 用户确认分组后 · OCR 发票 + 解析报告 + 建任务
    v118.32.4 · 拆两阶段 + 进度上报 + parse_vat_report 走 run_in_executor 防阻塞"""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    api_key = _user_key(user)
    import asyncio

    loop = asyncio.get_event_loop()

    try:
        groups = json.loads(confirmed_groups_json)
    except Exception as e:
        raise HTTPException(400, f"分组数据解析失败: {e}")

    if not groups:
        raise HTTPException(400, "无分组")

    _progress_init(progress_id, stage="upload", stage_done=len(files), stage_total=len(files))

    file_map: Dict[str, bytes] = {}
    for f in files:
        file_map[f.filename or ""] = await f.read()

    task_results = []
    # ── 阶段 1:并行解析 VAT 报告 + 建任务 (v118.32.5.5.32 · 串行→并行 · max 3 并发)
    _progress_update(
        progress_id, stage="parse_report", stage_done=0, stage_total=len(groups), current_file=""
    )
    built = []  # [(g, task_id, client_id), ...] 给阶段 2 用
    sem_parse = asyncio.Semaphore(3)
    _parse_done = {"n": 0}

    async def _parse_group(g):
        client_id = g.get("client_id")
        tax_id = g.get("tax_id")
        if not client_id:
            return {"tax_id": tax_id, "ok": False, "error": "no_client_id"}
        year, month = int(g.get("year")), int(g.get("month"))
        report_files = g.get("report_filenames", [])
        if not report_files:
            return {"tax_id": tax_id, "client_id": client_id, "ok": False, "error": "no_report"}
        first = report_files[0]
        rb = file_map.get(first)
        if not rb:
            return {
                "tax_id": tax_id,
                "client_id": client_id,
                "ok": False,
                "error": "report_missing",
            }
        async with sem_parse:
            _progress_update(progress_id, current_file=first)
            try:
                parse_res = await asyncio.wait_for(
                    loop.run_in_executor(None, parse_vat_report, rb, first, api_key),
                    timeout=300.0,
                )
            except asyncio.TimeoutError:
                parse_res = {"ok": False, "error": "解析超时(>300秒)"}
            except Exception as e:
                parse_res = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:100]}"}
        _parse_done["n"] += 1
        _progress_update(progress_id, stage_done=_parse_done["n"])
        if not parse_res.get("ok"):
            return {
                "tax_id": tax_id,
                "client_id": client_id,
                "ok": False,
                "error": f"parse_fail: {parse_res.get('error','')}",
            }
        report_id = db.create_vat_report(
            tenant_id=user.get("tenant_id"),
            client_id=client_id,
            period_year=year,
            period_month=month,
            parsed_rows=parse_res["rows"],
            meta=parse_res.get("meta", {}),
            source_filename=first,
            parser_version=parse_res.get("parser_version", ""),
        )
        task_id = db.create_recon_task(
            tenant_id=user.get("tenant_id"),
            user_id=str(user["id"]),
            client_id=client_id,
            period_year=year,
            period_month=month,
            vat_report_id=report_id,
        )
        if not task_id:
            return {"tax_id": tax_id, "client_id": client_id, "ok": False, "error": "task_exists"}
        return {"tax_id": tax_id, "client_id": client_id, "ok": True, "_task_id": task_id, "_g": g}

    for r in await asyncio.gather(*[_parse_group(g) for g in groups]):
        task_id_p1 = r.pop("_task_id", None)
        g_p1 = r.pop("_g", None)
        if r.get("ok") and task_id_p1 and g_p1:
            built.append((g_p1, task_id_p1, r["client_id"]))
        else:
            task_results.append(r)

    # ── 阶段 2:OCR 全部发票(新 pipeline 唯一路径,跨组并行 · 进度按文件粒度)
    import hashlib

    total_invoices = sum(len(g.get("invoice_filenames", []) or []) for (g, _tid, _cid) in built)
    _progress_update(
        progress_id, stage="ocr_invoices", stage_done=0, stage_total=total_invoices, current_file=""
    )
    # v118.32.5 · 性能优化 C · 并发 10 → 20（文字层路径占比高时尤其见效）
    sem_ocr = asyncio.Semaphore(20)
    _done_counter = {"n": 0}
    failed_by_task: Dict[int, List[str]] = {}

    async def _ocr_one(fname, task_id, client_id):
        content_b = file_map.get(fname)
        if not content_b:
            return ("missing", fname, task_id)
        file_hash = hashlib.sha256(content_b).hexdigest()
        existing = db.find_ocr_by_hash(str(user["id"]), file_hash, tenant_id=user.get("tenant_id"))
        if existing:
            try:
                db.insert_ocr_history(
                    user_id=str(user["id"]),
                    filename=fname,
                    page_count=existing.get("page_count") or 1,
                    pages=existing.get("pages") or [],
                    confidence=existing.get("confidence") or "medium",
                    elapsed_ms=0,
                    file_size_kb=len(content_b) // 1024,
                    file_hash=file_hash,
                    source="vat_recon_batch_cached",
                    source_ref=str(task_id),
                    client_id=client_id,
                )
                return ("cached", fname, task_id)
            except Exception as e:
                logger.warning(f"cache copy fail {fname}: {e}")

        # 新 pipeline 唯一路径(text_path layer 0 + Vision + Flash-Lite + Flash · 100% 埋点)
        try:
            from services.ocr.pipeline import run_on_pdf_bytes as _pipeline_run
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

            _pipe_res = await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: _pipeline_run(content_b, max_pages=10, api_key=api_key)
                ),
                timeout=120.0,
            )
            _pipe_legacy = pipeline_result_to_legacy_dict(_pipe_res)
            _pages = _pipe_legacy.get("pages") or []
            _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
            _hid = db.insert_ocr_history(
                user_id=str(user["id"]),
                filename=fname,
                page_count=_pipe_res.page_count or 1,
                pages=_pages,
                confidence="high",  # pipeline 有 L3 视觉兜底
                elapsed_ms=_pipe_res.elapsed_ms,
                file_size_kb=len(content_b) // 1024,
                file_hash=file_hash,
                source="vat_recon_batch_pipeline_v1",
                source_ref=str(task_id),
                client_id=client_id,
            )
            # recon batch cost 埋点(量最大的入口 · 必须 100% 记录)
            try:
                _r_in = sum(int(p.get("input_tokens") or 0) for p in _pages)
                _r_out = sum(int(p.get("output_tokens") or 0) for p in _pages)
                db.log_ocr_cost(
                    user_id=str(user["id"]),
                    tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
                    history_id=_hid,
                    engine="pipeline_v1",
                    pages=_pipe_res.page_count or 1,
                    input_tokens=_r_in,
                    output_tokens=_r_out,
                    cost_thb=_pipeline_cost_thb,
                    elapsed_ms=_pipe_res.elapsed_ms,
                )
            except Exception as _ce:
                logger.warning(f"[recon] cost log failed (non-blocking): {_ce}")
            logger.info(
                f"🆕 [recon] pipeline_v1 · {fname} · pages={_pipe_res.page_count} "
                f"· cost=฿{_pipeline_cost_thb:.4f}"
            )
            return ("ok", fname, task_id)
        except Exception as e:
            logger.error(f"[recon] OCR fail {fname}: {type(e).__name__}: {e}")
            return ("fail", fname, task_id)

    async def _ocr_with_sem(fname, task_id, client_id):
        async with sem_ocr:
            _progress_update(progress_id, current_file=fname)
            r = await _ocr_one(fname, task_id, client_id)
            _done_counter["n"] += 1
            _progress_update(progress_id, stage_done=_done_counter["n"])
            return r

    ocr_jobs = []
    for g, task_id, client_id in built:
        for fn in g.get("invoice_filenames", []) or []:
            ocr_jobs.append(_ocr_with_sem(fn, task_id, client_id))
    ocr_results = await asyncio.gather(*ocr_jobs) if ocr_jobs else []
    for st, fn, tid in ocr_results:
        if st in ("missing", "fail"):
            failed_by_task.setdefault(tid, []).append(fn)

    for g, task_id, _cid in built:
        task_results.append(
            {
                "tax_id": g.get("tax_id"),
                "client_id": _cid,
                "task_id": task_id,
                "ok": True,
                "ocr_failed": failed_by_task.get(task_id, []),
            }
        )

    # match 阶段由前端在 /run/{task_id} 触发(带同一 progress_id)· 这里先标记完成本路由
    _progress_update(
        progress_id, stage="match", stage_done=0, stage_total=len(built), current_file=""
    )

    return {"ok": True, "tasks": task_results}


@router.get("/result/{task_id}")
async def get_result(task_id: int, request: Request):
    user = get_current_user_from_request(request)
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
    user = get_current_user_from_request(request)
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
    user = get_current_user_from_request(request)
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
    user = get_current_user_from_request(request)
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
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    tasks = db.list_recon_tasks(
        tenant_id=user.get("tenant_id"), user_id=str(user["id"]), client_id=client_id
    )
    return {"ok": True, "tasks": tasks}


# ======================================================================
# v118.32.3 · 任务删除(单条 + 批量) · 顺便清掉对应的 OCR 缓存
# ======================================================================
class _DeleteIdsBody(BaseModel):
    ids: List[int]


@router.post("/tasks/batch_delete")
async def batch_delete_tasks(body: _DeleteIdsBody, request: Request):
    """删除多个对账任务 · 同时清:
    - reconciliation_row(该任务的所有 diff 行)
    - reconciliation_task(任务本身)
    - ocr_history(本任务上传的发票 · 按 source_ref=task_id 关联)
    - vat_report(该任务的 VAT 报告解析结果 · 仅当无其他任务引用)
    """
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if not body.ids:
        return {"ok": True, "deleted_tasks": 0, "deleted_ocr": 0}
    uid = str(user["id"])

    deleted_tasks = 0
    deleted_ocr = 0
    try:
        ids_int = [int(i) for i in body.ids]
        with db.get_cursor(commit=True) as cur:
            # 权限校验:只允许删自己 tenant 内的任务
            cur.execute(
                """
                SELECT t.id AS tid, t.vat_report_id AS rid FROM reconciliation_task t
                WHERE t.id = ANY(%s)
                  AND t.user_id IN (
                      SELECT id FROM users
                      WHERE tenant_id = (SELECT tenant_id FROM users WHERE id = %s)
                        OR id::text = %s
                  )
            """,
                (ids_int, uid, uid),
            )
            owned = cur.fetchall()
            if not owned:
                raise HTTPException(403, "无权删除或任务不存在")
            # RealDictCursor 返回 dict · 用列名访问
            owned_ids = [r["tid"] for r in owned]
            report_ids = list({r["rid"] for r in owned if r.get("rid")})

            # 1. 清 OCR 缓存(按 source_ref = task_id)
            owned_ids_str = [str(tid) for tid in owned_ids]
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE source LIKE 'vat_recon_batch%%'
                  AND source_ref = ANY(%s)
            """,
                (owned_ids_str,),
            )
            deleted_ocr = cur.rowcount or 0

            # 2. 清 recon_row
            cur.execute("DELETE FROM reconciliation_row WHERE task_id = ANY(%s)", (owned_ids,))
            # 3. 清任务本身
            cur.execute("DELETE FROM reconciliation_task WHERE id = ANY(%s)", (owned_ids,))
            deleted_tasks = cur.rowcount or 0

            # 4. 清 vat_report(仅当无其他任务引用)
            for rid in report_ids:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM reconciliation_task WHERE vat_report_id = %s",
                    (rid,),
                )
                _row = cur.fetchone()
                if ((_row["cnt"] if _row else 0) or 0) == 0:
                    cur.execute("DELETE FROM vat_report WHERE id = %s", (rid,))

        return {"ok": True, "deleted_tasks": deleted_tasks, "deleted_ocr": deleted_ocr}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"batch_delete_tasks failed: {type(e).__name__}: {e}", exc_info=True)
        # 把详细错误回传给前端 · 便于排查
        raise HTTPException(500, f"{type(e).__name__}: {str(e)[:200]}")


@router.delete("/task/{task_id}")
async def delete_one_task(task_id: int, request: Request):
    """单条删除 · 复用批量逻辑"""
    return await batch_delete_tasks(_DeleteIdsBody(ids=[task_id]), request)


@router.get("/export/{task_id}")
async def export_excel(task_id: int, request: Request, lang: str = "th"):
    """v118.32.3 · F2 · lang 参数接收前端当前界面语言(th/zh/en/ja)· 默认泰文给税局"""
    user = get_current_user_from_request(request)
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


# ════════════════════════════════════════════════════════════════════
# v118.32.5 · GL vs 销项税报告 对账（新功能）
# ════════════════════════════════════════════════════════════════════


@router.post("/gl-vat/run")
async def gl_vat_run(
    request: Request,
    # v118.35.0.3 · 多文件 · 旧的 gl_file/vat_file 单文件字段保留兼容(老前端
    # 还在用 / 测试 fixture / 外部脚本)· 新前端发 gl_files/vat_files 列表
    gl_file: Optional[UploadFile] = File(None),
    vat_file: Optional[UploadFile] = File(None),
    gl_files: Optional[List[UploadFile]] = File(None),
    vat_files: Optional[List[UploadFile]] = File(None),
    revenue_prefix: str = Form("4"),
    lang: str = Form("th"),
):
    """
    上传 GL 总账 + 销项税报告(各支持多文件),立即跑对账。
    - gl_files / vat_files: Excel / PDF / 图片 / CSV / Word / TXT · 多份
    - 兼容旧调用方:gl_file + vat_file 单文件字段
    - revenue_prefix: 收入科目代码前缀(默认 "4")
    - lang: 错误消息语言 zh/en/th/ja
    """
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, _glv_err("auth_required", lang))

    # 合并新旧字段 · 至少各 1 份
    gl_list: List[UploadFile] = list(gl_files or [])
    vat_list: List[UploadFile] = list(vat_files or [])
    if gl_file is not None:
        gl_list.append(gl_file)
    if vat_file is not None:
        vat_list.append(vat_file)
    if not gl_list or not vat_list:
        raise HTTPException(422, _glv_err("gl_parse_failed", lang, e="missing files"))

    # M3-3 修(2026-05-25):收入对账旧同步路径补 credits 前置检查 + 按量扣费 · 闭掉免费入口
    #   (与 bank /run、async /submit 一致 · 余额不足直接 402 · 不让付费 OCR 先跑)。
    _billing_glv = {"is_exempt": True, "pages_used_this_month": 0}
    try:
        import db as _db_credit_glv

        _tid_glv = user.get("tenant_id")
        _billing_glv = _db_credit_glv.get_billing_status_combined(str(user.get("id")), _tid_glv)
        if not _billing_glv.get("allowed") and not _billing_glv.get("is_exempt"):
            _est_cost = float(
                _db_credit_glv.estimate_pdf_cost_thb(
                    _billing_glv.get("pages_used_this_month", 0), len(gl_list) + len(vat_list)
                )
            )
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": _billing_glv.get("balance_thb", 0.0),
                    "estimated_cost": _est_cost,
                    "pages_used_this_month": _billing_glv.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as _be:
        logger.warning(f"[gl-vat.credits] pre-check skip: {_be}")

    # 读所有字节
    gl_data: List[tuple] = []
    vat_data: List[tuple] = []
    for f in gl_list:
        gl_data.append((await f.read(), f.filename or "gl.pdf"))
    for f in vat_list:
        vat_data.append((await f.read(), f.filename or "vat.pdf"))

    gl_name = "; ".join(fn for _, fn in gl_data)
    vat_name = "; ".join(fn for _, fn in vat_data)
    api_key = _user_key(user)

    # 1. 并行解析所有 GL 文件 + 合并 rows
    import asyncio

    loop = asyncio.get_event_loop()
    gl_results = await asyncio.gather(
        *[
            loop.run_in_executor(None, lambda b=b, n=n: parse_gl(b, n, revenue_prefix or "4"))
            for b, n in gl_data
        ]
    )
    gl_errors = [r.get("error") for r in gl_results if not r.get("ok") and r.get("error")]
    if gl_errors and not any(r.get("rows") for r in gl_results):
        # 所有 GL 都解析失败
        raise HTTPException(
            422, _glv_err("gl_parse_failed", lang, e="; ".join(filter(None, gl_errors))[:200])
        )
    merged_gl_rows = []
    for r in gl_results:
        merged_gl_rows.extend(r.get("rows") or [])
    if not merged_gl_rows:
        logger.warning(
            f"[gl-vat] GL parsed but 0 revenue rows · files={gl_name} · " f"prefix={revenue_prefix}"
        )
        raise HTTPException(422, _glv_err("gl_no_revenue_rows", lang))
    gl_result = {
        "ok": True,
        "rows": merged_gl_rows,
        "row_count": sum(r.get("row_count") or 0 for r in gl_results),
    }

    # 2. 并行解析所有 VAT 报表 + 合并 rows
    vat_results = await asyncio.gather(
        *[
            loop.run_in_executor(None, lambda b=b, n=n: parse_vat_report(b, n, api_key=api_key))
            for b, n in vat_data
        ]
    )
    vat_errors = [r.get("error") for r in vat_results if not r.get("ok") and r.get("error")]
    if vat_errors and not any(r.get("rows") for r in vat_results):
        raise HTTPException(
            422, _glv_err("vat_parse_failed", lang, e="; ".join(filter(None, vat_errors))[:200])
        )
    merged_vat_rows = []
    for r in vat_results:
        merged_vat_rows.extend(r.get("rows") or [])
    if not merged_vat_rows:
        raise HTTPException(422, _glv_err("vat_no_rows", lang))
    vat_result = {
        "ok": True,
        "rows": merged_vat_rows,
        "row_count": sum(r.get("row_count") or 0 for r in vat_results),
    }

    # M3-3 · 按量扣费(图片/PDF 按 OCR 页 · Excel/CSV 按字符估算 · 各格式各费率)· 豁免账号不扣
    if not _billing_glv.get("is_exempt"):
        try:
            import db as _db_chg_glv
            from services.ocr.pdf_utils import count_pdf_pages as _count_pages_glv

            _tid_chg_glv = user.get("tenant_id")
            _excel_exts = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}
            _pdf_units = 0
            _excel_units = 0
            for r, (b, fn) in list(zip(gl_results, gl_data)) + list(zip(vat_results, vat_data)):
                if not r.get("ok"):
                    continue
                if len(r.get("rows") or []) == 0:
                    continue
                ext = "." + (fn or "").lower().rsplit(".", 1)[-1] if "." in (fn or "") else ""
                if ext in _excel_exts:
                    _excel_units += _db_chg_glv._excel_char_count_estimate(b, fn)
                else:
                    _pdf_units += _pdf_billing_units(
                        _count_pages_glv(b) or 1, len(r.get("rows") or [])
                    )
            if _pdf_units > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        _db_chg_glv.charge_ocr_async,
                        str(user.get("id")),
                        _tid_chg_glv,
                        "pdf",
                        _pdf_units,
                        None,
                        f"收入对账 PDF · {_pdf_units} 页",
                    )
                )
            if _excel_units > 0:
                asyncio.create_task(
                    asyncio.to_thread(
                        _db_chg_glv.charge_ocr_async,
                        str(user.get("id")),
                        _tid_chg_glv,
                        "excel",
                        _excel_units,
                        None,
                        f"收入对账 Excel · {_excel_units} 字符",
                    )
                )
        except Exception as _ce:  # noqa: BLE001
            logger.warning(f"💳 gl-vat sync charge skip: {_ce}")

    # 3. 对账
    detail, summary = reconcile_gl_vat(gl_result["rows"], vat_result["rows"])

    # 4. 统计
    matched = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) == 0)
    diff_cnt = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) != 0)
    unmatched = sum(1 for r in detail if r.gl_amount is None)

    # 5. 落库
    detail_j = detail_to_json(detail)
    summary_j = summary_to_json(summary)
    task_id = db.create_gl_vat_task(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        gl_filename=gl_name,
        vat_filename=vat_name,
        gl_row_count=gl_result.get("row_count") or len(gl_result["rows"]),
        vat_row_count=vat_result.get("row_count") or len(vat_result["rows"]),
        detail_json=detail_j,
        summary_json=summary_j,
        matched_count=matched,
        unmatched_count=unmatched,
        diff_count=diff_cnt,
    )

    return {
        "ok": True,
        "task_id": task_id,
        "gl_row_count": len(gl_result["rows"]),
        "vat_row_count": len(vat_result["rows"]),
        "stats": {
            "matched": matched,
            "diff": diff_cnt,
            "unmatched": unmatched,
            "total": len(detail),
        },
        "detail": detail_j,
        "summary": summary_j,
    }


@router.get("/gl-vat/tasks")
async def gl_vat_list_tasks(request: Request):
    """列出最近 GL 对账任务"""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    tasks = db.list_gl_vat_tasks(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        limit=50,
    )
    return {"ok": True, "tasks": tasks}


@router.get("/gl-vat/{task_id}")
async def gl_vat_get_task(task_id: int, request: Request):
    """读取一份完整的 GL 对账结果（含明细 JSON）

    v118.35.0.29 P0 隔离 (体检 2026-05-21 风险 1):
    旧 db.get_gl_vat_task(task_id) 无任何权限校验 · 改成强制传 user_id + tenant_id ·
    跨 tenant 用户拿不到 task · 自然 404 (跟 task 不存在一样的响应 · 防枚举侧信道)
    """
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, _glv_err("auth_required", "th"))
    task = db.get_gl_vat_task(task_id, str(user["id"]), user.get("tenant_id"))
    if not task:
        raise HTTPException(404, _glv_err("task_not_found", "th"))
    return {
        "ok": True,
        "task_id": task["id"],
        "gl_filename": task.get("gl_filename"),
        "vat_filename": task.get("vat_filename"),
        "gl_row_count": task.get("gl_row_count"),
        "vat_row_count": task.get("vat_row_count"),
        "stats": {
            "matched": task.get("matched_count") or 0,
            "diff": task.get("diff_count") or 0,
            "unmatched": task.get("unmatched_count") or 0,
        },
        "detail": task.get("detail_json") or [],
        "summary": task.get("summary_json") or {},
        "created_at": str(task.get("created_at") or ""),
    }


@router.get("/gl-vat/{task_id}/export")
async def gl_vat_export(task_id: int, request: Request, lang: str = "th"):
    """下载 GL 对账 Excel · 表头按 lang 切换 zh/en/th/ja"""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if lang not in ("th", "zh", "en", "ja"):
        lang = "th"

    # v118.35.0.29 P0 隔离修复(体检风险 1) · 强制 user_id + tenant_id scope
    task = db.get_gl_vat_task(task_id, str(user["id"]), user.get("tenant_id"))
    if not task:
        raise HTTPException(404, "任务不存在")

    detail = detail_from_json(task.get("detail_json") or [])
    summary = summary_from_json(task.get("summary_json") or {})
    excel_bytes = export_gl_vat_excel(detail, summary, lang=lang)

    # v118.32.5.5.2 · filename 走 ASCII safe + RFC 5987 utf-8 编码(兼容泰文/中文文件名)
    import urllib.parse

    base_vat = (task.get("vat_filename") or "vat").rsplit(".", 1)[0]
    ascii_safe = (
        "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in base_vat)[
            :40
        ].strip("_")
        or f"task_{task_id}"
    )
    ascii_name = f"GL_VAT_recon_{task_id}_{ascii_safe}.xlsx"
    utf8_quoted = urllib.parse.quote(f"GL_VAT_recon_{task_id}_{base_vat}.xlsx")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={ascii_name}; filename*=UTF-8''{utf8_quoted}"
        },
    )


@router.delete("/gl-vat/{task_id}")
async def gl_vat_delete(task_id: int, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    ok = db.delete_gl_vat_task(task_id, str(user["id"]))
    if not ok:
        raise HTTPException(404, "任务不存在或无权删除")
    return {"ok": True}


# v118.32.5.5.20 · 批量删除 GL 对账任务
class _GlBatchDeleteBody(BaseModel):
    ids: List[int]


@router.post("/gl-vat/tasks/batch_delete")
async def gl_vat_batch_delete(body: _GlBatchDeleteBody, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if not body.ids:
        return {"deleted": 0}
    deleted = db.delete_gl_vat_tasks_batch(body.ids, str(user["id"]))
    return {"deleted": int(deleted)}


# ════════════════════════════════════════════════════════════════════
# Bank-v2 对账路由组 · moved to recon_routes_bankv2*.py(verbatim 抽出)
# ════════════════════════════════════════════════════════════════════
from recon_routes_bankv2 import bankv2_router  # noqa: E402

# re-export bank-v2 surface · recon_jobs/handlers.py 运行时 `from recon_routes import ...`
# 拉这批名字(原 bank_v2_run 解析段同名函数)+ 测试 patch recon_routes.X / 直接调 handler。
# verbatim 搬出后必须保契约,否则 worker import 崩 + monkeypatch 失效。
from recon_routes_bankv2_helpers import (  # noqa: F401,E402  re-export (handlers/tests)
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
from recon_routes_bankv2_run import bank_v2_run  # noqa: F401,E402  re-export
from recon_routes_bankv2 import (  # noqa: F401,E402  re-export (tests 直接调 handler)
    bank_v2_get_task,
    bank_v2_export,
    bank_v2_list_tasks,
    bank_v2_delete,
    bank_v2_batch_delete,
)

router.include_router(bankv2_router)
