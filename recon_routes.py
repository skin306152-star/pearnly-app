# -*- coding: utf-8 -*-
"""
v118.32.2 · Pearnly · 销项税对账完整路由
"""
import os
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
from vat_file_classifier import classify_file
from vat_excel_exporter import export_recon_task
from vat_ai_analyzer import analyze_diff
# v118.32.5 · GL vs 销项税报告 对账
from gl_vat_reconciler import (
    parse_gl, reconcile_gl_vat, export_gl_vat_excel,
    detail_to_json, summary_to_json,
    detail_from_json, summary_from_json,
)


# v118.32.5 · GL 对账错误消息 i18n（4 语言）
_GLV_ERR = {
    "auth_required": {
        "zh": "未登录", "en": "Not logged in",
        "th": "ยังไม่ได้เข้าสู่ระบบ", "ja": "未ログイン",
    },
    "gl_parse_failed": {
        "zh": "GL 解析失败：{e}", "en": "Failed to parse GL: {e}",
        "th": "อ่านไฟล์ GL ไม่สำเร็จ: {e}", "ja": "GL 解析失敗: {e}",
    },
    "gl_no_revenue_rows": {
        "zh": "GL 文件中未找到任何收入类科目数据 · 请检查文件或科目前缀",
        "en": "No revenue account rows found in GL · check file or account prefix",
        "th": "ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบไฟล์หรือรหัสนำหน้าบัญชี",
        "ja": "GL に収益科目データが見つかりません · ファイルまたは科目接頭辞を確認",
    },
    "vat_parse_failed": {
        "zh": "销项税报告解析失败：{e}", "en": "Failed to parse VAT report: {e}",
        "th": "อ่านรายงานภาษีขายไม่สำเร็จ: {e}", "ja": "売上税報告解析失敗: {e}",
    },
    "vat_no_rows": {
        "zh": "销项税报告中未找到任何数据行",
        "en": "No data rows found in VAT report",
        "th": "ไม่พบรายการในรายงานภาษีขาย",
        "ja": "売上税報告にデータ行が見つかりません",
    },
    "task_not_found": {
        "zh": "任务不存在", "en": "Task not found",
        "th": "ไม่พบงาน", "ja": "タスクが見つかりません",
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
    stale = [k for k, v in _progress_store.items()
             if now - v.get("updated_at", 0) > _PROGRESS_TTL_SEC]
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
    return {"ok": True, "found": True,
            "stage": p.get("stage", "upload"),
            "stage_done": done, "stage_total": total,
            "current_file": p.get("current_file", ""),
            "elapsed_sec": int(elapsed),
            "eta_sec": eta_sec,
            "stats": p.get("stats"),
            "error": p.get("error", "")}


def _user_key(user):
    return (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip() or None


def _missing_fields(row: Dict, is_report: bool) -> List[str]:
    """v118.32.4.9 · OCR 完整性检查 · 7 字段任一缺失则返回缺失字段名列表
    散客(无 buyer_tax_id)允许跳过 buyer_tax_id / buyer_branch 两项"""
    if is_report:
        required = ["report_date", "report_invoice_no", "report_buyer_name",
                    "report_amount_pre_vat", "report_vat_amount"]
        tax_key = "report_buyer_tax_id"
        branch_key = "report_buyer_branch"
    else:
        required = ["invoice_date", "invoice_no", "buyer_name",
                    "amount_pre_vat", "vat_amount"]
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
        to_insert.append({
            "task_id": task_id, "invoice_id": pair["invoice_id"],
            "report_row_no": pair["report_row_no"],
            "pair_confidence": pair["pair_confidence"],
            "status": "matched" if not diff["has_diff"] else "mismatched",
            "diff_fields": diff["fields"],
            "diff_categories": ",".join(cats),
        })
    for inv_id in match["invoice_orphans"]:
        # 反查发票行做 OCR 完整性检查
        inv_row = next((r for r in invoice_rows if r.get("id") == inv_id), {})
        cats = ["invoice_orphan"]
        if _missing_fields(inv_row, is_report=False):
            cats.append("ocr_incomplete")
        to_insert.append({"task_id": task_id, "invoice_id": inv_id,
                          "report_row_no": None, "pair_confidence": None,
                          "status": "invoice_orphan", "diff_fields": {},
                          "diff_categories": ",".join(cats)})
    for rep_no in match["report_orphans"]:
        rep_row = next((r for r in report_rows if r.get("row_no") == rep_no), {})
        cats = ["report_orphan"]
        if _missing_fields(rep_row, is_report=True):
            cats.append("ocr_incomplete")
        to_insert.append({"task_id": task_id, "invoice_id": None,
                          "report_row_no": rep_no, "pair_confidence": None,
                          "status": "report_orphan", "diff_fields": {},
                          "diff_categories": ",".join(cats)})
    db.bulk_insert_recon_rows(to_insert)
    stats = match["stats"]
    db.update_recon_task_completed(task_id, {
        "status": "completed",
        "matched_count": sum(1 for r in to_insert if r["status"] == "matched"),
        "mismatched_count": sum(1 for r in to_insert if r["status"] == "mismatched"),
        "invoice_orphan_count": stats["invoice_orphan_count"],
        "report_orphan_count": stats["report_orphan_count"],
        "invoice_count_archived": stats["total_invoices"],
        "report_row_count": stats["total_report_rows"],
    })
    return stats


# ======================================================================
# 屏 A
# ======================================================================

@router.post("/upload_report")
async def upload_report(request: Request, file: UploadFile = File(...),
                        client_id: int = Form(...),
                        period_year: int = Form(...),
                        period_month: int = Form(...)):
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    fb = await file.read()
    import asyncio as _aio
    result = await _aio.get_event_loop().run_in_executor(
        None, parse_vat_report, fb, file.filename or "", _user_key(user))
    if not result.get("ok"):
        raise HTTPException(422, result.get("error", "解析失败"))
    report_id = db.create_vat_report(
        tenant_id=user.get("tenant_id"), client_id=client_id,
        period_year=period_year, period_month=period_month,
        parsed_rows=result["rows"], meta=result.get("meta", {}),
        source_filename=file.filename or "",
        parser_version=result.get("parser_version", ""))
    if not report_id: raise HTTPException(500, "报告存储失败")
    return {"ok": True, "report_id": report_id,
            "row_count": result["row_count"],
            "warnings": result.get("warnings", []),
            "method": result.get("method", "")}


class CreateTaskBody(BaseModel):
    client_id: int
    period_year: int
    period_month: int
    vat_report_id: int


@router.post("/task")
async def create_task(body: CreateTaskBody, request: Request):
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    task_id = db.create_recon_task(
        tenant_id=user.get("tenant_id"), user_id=str(user["id"]),
        client_id=body.client_id, period_year=body.period_year,
        period_month=body.period_month, vat_report_id=body.vat_report_id)
    if not task_id:
        raise HTTPException(409, "该客户本月已有进行中的对账任务")
    return {"ok": True, "task_id": task_id}


@router.post("/run/{task_id}")
async def run_recon(task_id: int, request: Request,
                     progress_id: Optional[str] = None,
                     is_last: int = 0):
    """v118.32.4 · 可带 progress_id 上报 match 阶段;is_last=1 时标记 done"""
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    task = db.get_recon_task(task_id)
    if not task: raise HTTPException(404, "任务不存在")
    # v118.32.4.3 · 屏 B 流程优先按 source_ref=task_id 取本次任务关联的发票(隔离历史 OCR 缓存)
    # 无结果(屏 A 流程:用户手动跑对账)再按 客户+期间 老逻辑
    invoice_rows = db.list_invoices_for_recon(
        tenant_id=task.get("tenant_id"), client_id=task["client_id"],
        period_year=task["period_year"], period_month=task["period_month"],
        source_ref=str(task_id))
    if not invoice_rows:
        invoice_rows = db.list_invoices_for_recon(
            tenant_id=task.get("tenant_id"), client_id=task["client_id"],
            period_year=task["period_year"], period_month=task["period_month"])
    report = db.get_vat_report(task["vat_report_id"])
    report_rows = (report or {}).get("parsed_rows") or []
    db.update_recon_task_status(task_id, "running")
    try:
        # 上报当前正在匹配哪个客户
        if progress_id and progress_id in _progress_store:
            client = db.get_client_by_id(task["client_id"]) if task.get("client_id") else {}
            _progress_update(progress_id,
                             current_file=(client or {}).get("name", "") or f"task {task_id}")
        import asyncio
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None, _run_match_and_save, task_id, invoice_rows, report_rows)
        if progress_id and progress_id in _progress_store:
            cur = _progress_store[progress_id]
            cur_done = (cur.get("stage_done") or 0) + 1
            _progress_update(progress_id, stage_done=cur_done)
            if is_last:
                # 累计 stats(简单累加)
                acc = cur.get("stats") or {"matched": 0, "mismatched": 0,
                                            "invoice_orphans": 0, "report_orphans": 0}
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

@router.post("/batch_classify")
async def batch_classify(request: Request,
                          files: List[UploadFile] = File(...)):
    """v118.32.2 · 屏 B · N 个文件 → 分类 + 按税号分组 + 自动找/建客户"""
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    api_key = _user_key(user)

    # v118.32.3 · 并行 10 路调 AI + timing log + 30s 单文件超时
    import asyncio, time
    sem = asyncio.Semaphore(10)
    loop = asyncio.get_event_loop()
    t_start = time.time()
    logger.info(f"[batch_classify] 开始 · 文件数={len(files)}")

    async def _classify_one(f):
        async with sem:
            t0 = time.time()
            try:
                content_bytes = await f.read()
                # 30s 超时保护 · 防单文件卡死整批
                info = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, classify_file, content_bytes, f.filename or "", api_key
                    ),
                    timeout=30.0
                )
                elapsed = time.time() - t0
                logger.info(f"[batch_classify] OK {f.filename} · {elapsed:.1f}s · type={info.get('type')}")
                return {
                    "filename": f.filename, "size": len(content_bytes),
                    "type":       info.get("type", "unknown"),
                    "confidence": info.get("confidence", 0),
                    "tax_id":     info.get("tax_id", ""),
                    "name":       info.get("name", ""),
                    "year":       info.get("year"),
                    "month":      info.get("month"),
                    "method":     info.get("method", ""),
                    "error":      info.get("error", ""),
                    "elapsed_ms": int(elapsed * 1000),
                }
            except asyncio.TimeoutError:
                logger.error(f"[batch_classify] TIMEOUT {f.filename} · >30s")
                return {
                    "filename": f.filename, "size": 0, "type": "unknown",
                    "confidence": 0, "tax_id": "", "name": "",
                    "year": None, "month": None, "method": "timeout",
                    "error": "识别超时(>30 秒)",
                }
            except Exception as e:
                logger.error(f"[batch_classify] FAIL {f.filename} · {type(e).__name__}: {e}")
                return {
                    "filename": f.filename, "size": 0, "type": "unknown",
                    "confidence": 0, "tax_id": "", "name": "",
                    "year": None, "month": None, "method": "error",
                    "error": f"{type(e).__name__}: {str(e)[:100]}",
                }

    classified = await asyncio.gather(*[_classify_one(f) for f in files])
    logger.info(f"[batch_classify] 完成 · 总耗时={time.time()-t_start:.1f}s · 成功={sum(1 for r in classified if r['type']!='unknown')}/{len(classified)}")
    # v118.32.4.5 · 诊断:每个文件识别出的 type/tax_id/year/month
    for _r in classified:
        logger.info(f"[batch_classify] · {_r.get('filename','?')[:30]} type={_r.get('type')} tax={_r.get('tax_id')} year={_r.get('year')} month={_r.get('month')}")

    # ── 先扫一遍报告 · 拿到每个报告的 (税号, 期间) · 给同税号发票套用
    report_periods = {}
    for r in classified:
        if r["type"] == "vat_report" and r.get("tax_id") and r.get("year") and r.get("month"):
            report_periods[r["tax_id"]] = (r["year"], r["month"])

    # v118.32.4.9.1 · 单一报告 = 真理源 · 整批只有 1 份 VAT 报告时
    # 所有发票强制归到该报告组(忽略发票自己抽到的卖方/期间)
    # 业务语义:1 份报告内的发票理应同卖方同期间 · OCR 抽错不影响分组
    all_reports = [r for r in classified
                   if r["type"] == "vat_report"
                   and r.get("tax_id") and r.get("year") and r.get("month")]
    single_report = all_reports[0] if len(all_reports) == 1 else None
    if single_report:
        logger.info(f"[batch_classify] 单一报告模式 · 强制所有发票归 "
                    f"{single_report['tax_id']}_{single_report['year']}_{single_report['month']}")

    # 按 (税号, 期间) 分组
    groups_map: Dict[str, Dict[str, Any]] = {}
    unassigned_extras = []
    for r in classified:
        if r["type"] == "invoice":
            tid   = r.get("tax_id", "")
            year  = r.get("year")
            month = r.get("month")
            # v118.32.4.9.1 · 单一报告模式:强制归报告组
            if single_report:
                tid   = single_report["tax_id"]
                year  = single_report["year"]
                month = single_report["month"]
            else:
                # 发票缺期间 → 套用同税号报告的期间
                if tid and (not year or not month) and tid in report_periods:
                    year, month = report_periods[tid]
                if not tid:
                    unassigned_extras.append({**r, "reason_code": "no_seller_tax_id"})
                    continue
                if not year or not month:
                    unassigned_extras.append({**r, "reason_code": "no_invoice_date"})
                    continue
        elif r["type"] == "vat_report":
            tid   = r.get("tax_id", "")
            year  = r.get("year")
            month = r.get("month")
            if not tid:
                unassigned_extras.append({**r, "reason_code": "no_issuer_tax_id"})
                continue
            if not year or not month:
                unassigned_extras.append({**r, "reason_code": "no_period"})
                continue
        else:
            continue
        key = f"{tid}_{year}_{month}"
        g = groups_map.setdefault(key, {
            "tax_id": tid,
            "client_name": r.get("name") or "",
            "year": year, "month": month,
            "client_id": None, "new_client": False,
            "min_conf": 1.0,
            "invoices": [], "reports": [],
        })
        item = {"filename": r["filename"], "confidence": r.get("confidence", 0)}
        (g["invoices"] if r["type"] == "invoice" else g["reports"]).append(item)
        if not g["client_name"] and r.get("name"):
            g["client_name"] = r["name"]
        g["min_conf"] = min(g["min_conf"], r.get("confidence", 0) or 0)

    # v118.32.4.7 · OCR 容错合并 · 同年月 + 税号差≤2位 → 合并(去掉互补要求)
    # 主组按"文件数最多"判定(主组留下) · OCR 读错 1-2 位的零散组合并进来
    def _hamming(a, b):
        if not a or not b or len(a) != len(b): return 99
        return sum(1 for x, y in zip(a, b) if x != y)

    def _group_size(g):
        return len(g.get("invoices", [])) + len(g.get("reports", []))

    _changed = True
    while _changed:
        _changed = False
        # 每轮按文件数从多到少排序 · 大组优先吸收小组
        _items = sorted(groups_map.items(),
                        key=lambda kv: _group_size(kv[1]), reverse=True)
        _keys_ordered = [k for k, _ in _items]
        _merged_this_round = set()
        for _i, _k1 in enumerate(_keys_ordered):
            if _k1 in _merged_this_round: continue
            _g1 = groups_map.get(_k1)
            if _g1 is None: continue
            for _k2 in _keys_ordered[_i+1:]:
                if _k2 in _merged_this_round: continue
                _g2 = groups_map.get(_k2)
                if _g2 is None: continue
                if _g1["year"] != _g2["year"] or _g1["month"] != _g2["month"]:
                    continue
                if _hamming(_g1["tax_id"], _g2["tax_id"]) > 2:
                    continue
                # 合并 g2 → g1(主组) · 主组的 tax_id/name 留下(更可靠)
                if len(_g2.get("client_name", "")) > len(_g1.get("client_name", "")):
                    _g1["client_name"] = _g2["client_name"]
                _g1["invoices"].extend(_g2["invoices"])
                _g1["reports"].extend(_g2["reports"])
                _g1["min_conf"] = min(_g1["min_conf"], _g2["min_conf"])
                _merged_this_round.add(_k2)
                _changed = True
                logger.info(f"[batch_classify] 合并 {_k2} → {_k1} · 税号容错")
        for _k in _merged_this_round:
            groups_map.pop(_k, None)

    # v118.32.4.7 · 空税号发票兜底 · 唯一年月一致主组时自动归入
    _rescued = []
    for _u in list(unassigned_extras):
        if _u.get("reason_code") != "no_seller_tax_id": continue
        if _u.get("type") != "invoice": continue
        _yr, _mo = _u.get("year"), _u.get("month")
        if not _yr or not _mo: continue
        _candidates = [g for g in groups_map.values()
                       if g.get("year") == _yr and g.get("month") == _mo]
        if len(_candidates) != 1: continue
        _g = _candidates[0]
        _g["invoices"].append({"filename": _u["filename"],
                                "confidence": _u.get("confidence", 0)})
        _g["min_conf"] = min(_g["min_conf"], _u.get("confidence", 0) or 0)
        _rescued.append(_u)
        logger.info(f"[batch_classify] 空税号发票兜底归入 {_u['filename'][:30]} → {_g['tax_id']}_{_yr}_{_mo}")
    for _u in _rescued:
        unassigned_extras.remove(_u)

    # 为每组找/建客户(自动建客户 · 铁律 v118.32.2 方案 1)
    groups_list = []
    for key, g in groups_map.items():
        existing_id = db.find_or_create_client_by_tax_id(
            user_id=str(user["id"]), tenant_id=user.get("tenant_id"),
            tax_id=g["tax_id"], name=g["client_name"],
        )
        if existing_id:
            # 判断是不是新建的(简化:看名字是不是 fallback 格式)
            g["client_id"] = existing_id
            # 检查是否本次自动建的(用 created_at 接近 now 判)
            try:
                with db.get_cursor() as cur:
                    cur.execute("SELECT created_at FROM clients WHERE id = %s", (existing_id,))
                    row = cur.fetchone()
                    if row:
                        from datetime import datetime, timezone, timedelta
                        delta = datetime.now(timezone.utc) - row["created_at"]
                        g["new_client"] = delta < timedelta(seconds=10)
            except Exception:
                g["new_client"] = False
        groups_list.append(g)

    unknown_files = [r for r in classified if r["type"] not in ("invoice", "vat_report")]
    for u in unknown_files:
        u["reason_code"] = "ai_cannot_classify"
        if u.get("error"): u["reason_extra"] = u["error"]
    unassigned = unknown_files + unassigned_extras
    return {
        "ok": True,
        "files": classified,
        "groups": groups_list,
        "unassigned": unassigned,
        "stats": {
            "total_files": len(classified),
            "invoices": sum(1 for r in classified if r["type"] == "invoice"),
            "reports":  sum(1 for r in classified if r["type"] == "vat_report"),
            "unknown":  len(unassigned),
            "groups":   len(groups_list),
        }
    }


@router.post("/batch_process")
async def batch_process(request: Request,
                         confirmed_groups_json: str = Form(...),
                         files: List[UploadFile] = File(...),
                         progress_id: Optional[str] = Form(None)):
    """v118.32.2 · 屏 B · 用户确认分组后 · OCR 发票 + 解析报告 + 建任务
    v118.32.4 · 拆两阶段 + 进度上报 + parse_vat_report 走 run_in_executor 防阻塞"""
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    api_key = _user_key(user)
    import asyncio
    loop = asyncio.get_event_loop()

    try: groups = json.loads(confirmed_groups_json)
    except Exception as e: raise HTTPException(400, f"分组数据解析失败: {e}")

    if not groups: raise HTTPException(400, "无分组")

    _progress_init(progress_id, stage="upload",
                   stage_done=len(files), stage_total=len(files))

    file_map: Dict[str, bytes] = {}
    for f in files:
        file_map[f.filename or ""] = await f.read()

    task_results = []
    # ── 阶段 1:并行解析 VAT 报告 + 建任务 (v118.32.5.5.32 · 串行→并行 · max 3 并发)
    _progress_update(progress_id, stage="parse_report",
                     stage_done=0, stage_total=len(groups),
                     current_file="")
    built = []  # [(g, task_id, client_id), ...] 给阶段 2 用
    sem_parse = asyncio.Semaphore(3)
    _parse_done = {"n": 0}

    async def _parse_group(g):
        client_id = g.get("client_id")
        tax_id    = g.get("tax_id")
        if not client_id:
            return {"tax_id": tax_id, "ok": False, "error": "no_client_id"}
        year, month = int(g.get("year")), int(g.get("month"))
        report_files = g.get("report_filenames", [])
        if not report_files:
            return {"tax_id": tax_id, "client_id": client_id, "ok": False, "error": "no_report"}
        first = report_files[0]
        rb = file_map.get(first)
        if not rb:
            return {"tax_id": tax_id, "client_id": client_id, "ok": False, "error": "report_missing"}
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
            return {"tax_id": tax_id, "client_id": client_id, "ok": False,
                    "error": f"parse_fail: {parse_res.get('error','')}"}
        report_id = db.create_vat_report(
            tenant_id=user.get("tenant_id"), client_id=client_id,
            period_year=year, period_month=month,
            parsed_rows=parse_res["rows"], meta=parse_res.get("meta", {}),
            source_filename=first, parser_version=parse_res.get("parser_version", ""))
        task_id = db.create_recon_task(
            tenant_id=user.get("tenant_id"), user_id=str(user["id"]),
            client_id=client_id, period_year=year, period_month=month,
            vat_report_id=report_id)
        if not task_id:
            return {"tax_id": tax_id, "client_id": client_id, "ok": False, "error": "task_exists"}
        return {"tax_id": tax_id, "client_id": client_id, "ok": True,
                "_task_id": task_id, "_g": g}

    for r in await asyncio.gather(*[_parse_group(g) for g in groups]):
        task_id_p1 = r.pop("_task_id", None)
        g_p1       = r.pop("_g", None)
        if r.get("ok") and task_id_p1 and g_p1:
            built.append((g_p1, task_id_p1, r["client_id"]))
        else:
            task_results.append(r)

    # ── 阶段 2:OCR 全部发票(新 pipeline 唯一路径,跨组并行 · 进度按文件粒度)
    import hashlib
    total_invoices = sum(len(g.get("invoice_filenames", []) or []) for (g, _tid, _cid) in built)
    _progress_update(progress_id, stage="ocr_invoices",
                     stage_done=0, stage_total=total_invoices,
                     current_file="")
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
                    user_id=str(user["id"]), filename=fname,
                    page_count=existing.get("page_count") or 1,
                    pages=existing.get("pages") or [],
                    confidence=existing.get("confidence") or "medium",
                    elapsed_ms=0, file_size_kb=len(content_b)//1024,
                    file_hash=file_hash, source="vat_recon_batch_cached",
                    source_ref=str(task_id), client_id=client_id)
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
                user_id=str(user["id"]), filename=fname,
                page_count=_pipe_res.page_count or 1, pages=_pages,
                confidence="high",  # pipeline 有 L3 视觉兜底
                elapsed_ms=_pipe_res.elapsed_ms,
                file_size_kb=len(content_b)//1024, file_hash=file_hash,
                source="vat_recon_batch_pipeline_v1",
                source_ref=str(task_id), client_id=client_id)
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
    for (g, task_id, client_id) in built:
        for fn in g.get("invoice_filenames", []) or []:
            ocr_jobs.append(_ocr_with_sem(fn, task_id, client_id))
    ocr_results = await asyncio.gather(*ocr_jobs) if ocr_jobs else []
    for (st, fn, tid) in ocr_results:
        if st in ("missing", "fail"):
            failed_by_task.setdefault(tid, []).append(fn)

    for (g, task_id, _cid) in built:
        task_results.append({"tax_id": g.get("tax_id"), "client_id": _cid,
                             "task_id": task_id, "ok": True,
                             "ocr_failed": failed_by_task.get(task_id, [])})

    # match 阶段由前端在 /run/{task_id} 触发(带同一 progress_id)· 这里先标记完成本路由
    _progress_update(progress_id, stage="match",
                     stage_done=0, stage_total=len(built),
                     current_file="")

    return {"ok": True, "tasks": task_results}


@router.get("/result/{task_id}")
async def get_result(task_id: int, request: Request):
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    task = db.get_recon_task(task_id)
    if not task: raise HTTPException(404, "任务不存在")
    rows = db.list_recon_rows_detailed(task_id)
    # v118.32.2.5 · 补 client 给屏 C 头部用
    client = db.get_client_by_id(task["client_id"]) if task.get("client_id") else {}
    return {"ok": True, "task": task, "rows": rows, "client": client or {}}


@router.post("/row/{row_id}/analyze")
async def row_ai(row_id: int, request: Request):
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    row = db.get_recon_row(row_id)
    if not row: raise HTTPException(404, "行不存在")
    if row.get("ai_analysis"):
        ai = row["ai_analysis"]
        if isinstance(ai, str):
            try: ai = json.loads(ai)
            except: pass
        return {"ok": True, "analysis": ai, "ai": ai, "cached": True}

    result = analyze_diff(row, api_key=_user_key(user))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "AI 分析失败"))
    db.update_recon_row_ai_analysis(row_id, result)
    return {"ok": True, "analysis": result, "ai": result, "cached": False}


class RowActionBody(BaseModel):
    action: str
    notes: Optional[str] = None
    source: Optional[str] = None  # v118.32.4.8 "invoice"|"report" + v118.32.4.9 "both" (两边都对 · 同一笔)


@router.post("/row/{row_id}/action")
async def row_action(row_id: int, body: RowActionBody, request: Request):
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    if body.action not in ("pending", "resolved", "customer_issue", "accepted_diff"):
        raise HTTPException(400, "invalid action")
    # 把 source 拼进 notes(不改 db schema · 用 "source=invoice|report|both" 前缀)
    notes_payload = body.notes or ""
    if body.source in ("invoice", "report", "both"):
        prefix = f"source={body.source}"
        notes_payload = prefix + (" · " + body.notes if body.notes else "")
    db.update_recon_row_action(row_id, body.action, notes_payload or None)
    return {"ok": True}


# ======================================================================
# 任务列表 · Excel 导出
# ======================================================================

@router.get("/tasks")
async def list_tasks(request: Request, client_id: Optional[int] = None):
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
    tasks = db.list_recon_tasks(tenant_id=user.get("tenant_id"),
                                 user_id=str(user["id"]),
                                 client_id=client_id)
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
    if not user: raise HTTPException(401, "未登录")
    if not body.ids: return {"ok": True, "deleted_tasks": 0, "deleted_ocr": 0}
    uid = str(user["id"])

    deleted_tasks = 0
    deleted_ocr = 0
    try:
        ids_int = [int(i) for i in body.ids]
        with db.get_cursor(commit=True) as cur:
            # 权限校验:只允许删自己 tenant 内的任务
            cur.execute("""
                SELECT t.id AS tid, t.vat_report_id AS rid FROM reconciliation_task t
                WHERE t.id = ANY(%s)
                  AND t.user_id IN (
                      SELECT id FROM users
                      WHERE tenant_id = (SELECT tenant_id FROM users WHERE id = %s)
                        OR id::text = %s
                  )
            """, (ids_int, uid, uid))
            owned = cur.fetchall()
            if not owned:
                raise HTTPException(403, "无权删除或任务不存在")
            # RealDictCursor 返回 dict · 用列名访问
            owned_ids = [r["tid"] for r in owned]
            report_ids = list({r["rid"] for r in owned if r.get("rid")})

            # 1. 清 OCR 缓存(按 source_ref = task_id)
            owned_ids_str = [str(tid) for tid in owned_ids]
            cur.execute("""
                DELETE FROM ocr_history
                WHERE source LIKE 'vat_recon_batch%%'
                  AND source_ref = ANY(%s)
            """, (owned_ids_str,))
            deleted_ocr = cur.rowcount or 0

            # 2. 清 recon_row
            cur.execute("DELETE FROM reconciliation_row WHERE task_id = ANY(%s)", (owned_ids,))
            # 3. 清任务本身
            cur.execute("DELETE FROM reconciliation_task WHERE id = ANY(%s)", (owned_ids,))
            deleted_tasks = cur.rowcount or 0

            # 4. 清 vat_report(仅当无其他任务引用)
            for rid in report_ids:
                cur.execute("SELECT COUNT(*) AS cnt FROM reconciliation_task WHERE vat_report_id = %s", (rid,))
                _row = cur.fetchone()
                if ((_row["cnt"] if _row else 0) or 0) == 0:
                    cur.execute("DELETE FROM vat_report WHERE id = %s", (rid,))

        return {"ok": True, "deleted_tasks": deleted_tasks, "deleted_ocr": deleted_ocr}
    except HTTPException: raise
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
    if not user: raise HTTPException(401, "未登录")
    if lang not in ("th", "zh", "en", "ja"): lang = "th"
    task = db.get_recon_task(task_id)
    if not task: raise HTTPException(404, "任务不存在")

    rows = db.list_recon_rows_detailed(task_id)
    client = {}
    if task.get("client_id"):
        with db.get_cursor() as cur:
            cur.execute("SELECT id, name, tax_id, address FROM clients WHERE id = %s",
                        (task["client_id"],))
            r = cur.fetchone()
            if r: client = dict(r)

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
    gl_file: UploadFile = File(...),
    vat_file: UploadFile = File(...),
    revenue_prefix: str = Form("4"),
    lang: str = Form("th"),
):
    """
    上传 GL 总账 + 销项税报告，立即跑对账，返回明细 + 汇总 + task_id
    - gl_file:  Excel 或 PDF
    - vat_file: Excel / PDF / 图片
    - revenue_prefix: 收入科目代码前缀（默认 "4"）
    - lang: 错误消息语言 zh/en/th/ja（默认 th）
    """
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, _glv_err("auth_required", lang))

    gl_bytes  = await gl_file.read()
    vat_bytes = await vat_file.read()
    gl_name   = gl_file.filename or "gl.pdf"
    vat_name  = vat_file.filename or "vat.pdf"

    # 1. 解析 GL
    import asyncio
    loop = asyncio.get_event_loop()
    gl_result = await loop.run_in_executor(
        None, lambda: parse_gl(gl_bytes, gl_name, revenue_prefix or "4")
    )
    if not gl_result.get("ok"):
        raise HTTPException(422, _glv_err("gl_parse_failed", lang,
                                          e=gl_result.get("error", "unknown")))
    if not gl_result.get("rows"):
        logger.warning(f"[gl-vat] GL parsed but 0 revenue rows · file={gl_name} · "
                       f"prefix={revenue_prefix} · diag={gl_result.get('diag')}")
        raise HTTPException(422, _glv_err("gl_no_revenue_rows", lang))

    # 2. 解析 VAT 报表
    vat_result = await loop.run_in_executor(
        None, lambda: parse_vat_report(vat_bytes, vat_name, api_key=_user_key(user))
    )
    if not vat_result.get("ok"):
        raise HTTPException(422, _glv_err("vat_parse_failed", lang,
                                          e=vat_result.get("error", "unknown")))
    if not vat_result.get("rows"):
        raise HTTPException(422, _glv_err("vat_no_rows", lang))

    # 3. 对账
    detail, summary = reconcile_gl_vat(gl_result["rows"], vat_result["rows"])

    # 4. 统计
    matched   = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) == 0)
    diff_cnt  = sum(1 for r in detail if r.gl_amount is not None and (r.diff or 0) != 0)
    unmatched = sum(1 for r in detail if r.gl_amount is None)

    # 5. 落库
    detail_j  = detail_to_json(detail)
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
    """读取一份完整的 GL 对账结果（含明细 JSON）"""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, _glv_err("auth_required", "th"))
    task = db.get_gl_vat_task(task_id)
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
            "matched":   task.get("matched_count") or 0,
            "diff":      task.get("diff_count") or 0,
            "unmatched": task.get("unmatched_count") or 0,
        },
        "detail":  task.get("detail_json") or [],
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

    task = db.get_gl_vat_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    detail = detail_from_json(task.get("detail_json") or [])
    summary = summary_from_json(task.get("summary_json") or {})
    excel_bytes = export_gl_vat_excel(detail, summary, lang=lang)

    # v118.32.5.5.2 · filename 走 ASCII safe + RFC 5987 utf-8 编码(兼容泰文/中文文件名)
    import urllib.parse
    base_vat = (task.get("vat_filename") or "vat").rsplit(".", 1)[0]
    ascii_safe = "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_"
                          for c in base_vat)[:40].strip("_") or f"task_{task_id}"
    ascii_name = f"GL_VAT_recon_{task_id}_{ascii_safe}.xlsx"
    utf8_quoted = urllib.parse.quote(f"GL_VAT_recon_{task_id}_{base_vat}.xlsx")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":
                 f"attachment; filename={ascii_name}; filename*=UTF-8''{utf8_quoted}"},
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
# v118.33.6 · Bank Statement vs GL Reconciliation v2
# ════════════════════════════════════════════════════════════════════
try:
    from bank_recon_v2 import (
        parse_bank_statement_pdf, parse_gl as parse_gl_v2,
        merge_statements, merge_gl_files,
        reconcile as bank_reconcile,
        export_bank_recon_excel,
        rows_to_json, rows_from_json,
        summary_to_json as bank_summary_to_json,
        summary_from_json as bank_summary_from_json,
    )
    _BANK_V2_OK = True
except ImportError as _brv2_import_err:
    logger.warning(f"[bank-v2] bank_recon_v2 not available: {_brv2_import_err}")
    _BANK_V2_OK = False

_BRV2_ERR = {
    "auth_required": {"zh": "未登录", "en": "Not logged in", "th": "ยังไม่ได้เข้าสู่ระบบ", "ja": "未ログイン"},
    "no_stmt_files":  {"zh": "请上传银行账单", "en": "Please upload bank statement files",
                       "th": "กรุณาอัปโหลดไฟล์บัญชีธนาคาร", "ja": "銀行明細ファイルをアップロードしてください"},
    "no_gl_files":    {"zh": "请上传GL文件", "en": "Please upload GL files",
                       "th": "กรุณาอัปโหลดไฟล์ GL", "ja": "GLファイルをアップロードしてください"},
    "stmt_parse_fail": {"zh": "账单解析失败: {e}", "en": "Statement parse failed: {e}",
                        "th": "อ่านไฟล์บัญชีไม่สำเร็จ: {e}", "ja": "明細解析失敗: {e}"},
    "gl_parse_fail":   {"zh": "GL解析失败: {e}", "en": "GL parse failed: {e}",
                        "th": "อ่านไฟล์ GL ไม่สำเร็จ: {e}", "ja": "GL解析失敗: {e}"},
    "stmt_no_rows":    {"zh": "账单中未找到交易记录", "en": "No transactions found in bank statement",
                        "th": "ไม่พบรายการในบัญชีธนาคาร", "ja": "銀行明細に取引が見つかりません"},
    "gl_no_rows":      {"zh": "GL中未找到记录", "en": "No rows found in GL",
                        "th": "ไม่พบรายการใน GL", "ja": "GLにデータが見つかりません"},
    "task_not_found":  {"zh": "任务不存在", "en": "Task not found",
                        "th": "ไม่พบงาน", "ja": "タスクが見つかりません"},
}


def _brv2_err(key: str, lang: str = "th", **fmt) -> str:
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    msg = (_BRV2_ERR.get(key) or {}).get(lang) or (_BRV2_ERR.get(key) or {}).get("en") or key
    return msg.format(**fmt) if fmt else msg


@router.post("/bank-v2/run")
async def bank_v2_run(
    request: Request,
    stmt_files: List[UploadFile] = File(...),
    gl_files: List[UploadFile] = File(...),
    gl_account: str = Form(""),
    lang: str = Form("th"),
):
    """
    Upload bank statement PDF(s) + GL file(s), run reconciliation.
    Returns {ok, task_id, stats, detail, summary, gl_accounts}
    """
    if not _BANK_V2_OK:
        raise HTTPException(503, "Bank Recon v2 module not available on this server")
    import asyncio
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, _brv2_err("auth_required", lang))

    if not stmt_files:
        raise HTTPException(422, _brv2_err("no_stmt_files", lang))
    if not gl_files:
        raise HTTPException(422, _brv2_err("no_gl_files", lang))

    # v118.33.12.1 · use _user_key (gemini_api_key OR custom_gemini_api_key)
    # to match the rest of the system; fall back to env GEMINI_API_KEY.
    import os as _os, logging as _lg
    api_key = (_user_key(user) or _os.environ.get('GEMINI_API_KEY', '')).strip()
    _lg.getLogger('recon').info(
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

    # 2. Parse statement files (parallel)
    async def _parse_stmt(b, fname):
        return await loop.run_in_executor(
            None, lambda: parse_bank_statement_pdf(b, fname, api_key)
        )

    async def _parse_gl(b, fname):
        return await loop.run_in_executor(
            None, lambda: parse_gl_v2(b, fname, gl_account, api_key)
        )

    stmt_results = await asyncio.gather(*[_parse_stmt(b, fn) for b, fn in stmt_data])
    gl_results = await asyncio.gather(*[_parse_gl(b, fn) for b, fn in gl_data])

    # Build per-file parse diagnostics (always included in every response)
    parse_info = {
        "stmt_files": [
            {"file": fn, "rows": len(r.get("rows") or []),
             "ok": r.get("ok", False), "error": r.get("error"),
             "bank_code": r.get("bank_code", "")}
            for r, (_, fn) in zip(stmt_results, stmt_data)
        ],
        "gl_files": [
            {"file": fn, "rows": len(r.get("rows") or []),
             "ok": r.get("ok", False), "error": r.get("error"),
             "accounts": r.get("accounts", [])}
            for r, (_, fn) in zip(gl_results, gl_data)
        ],
    }

    stmt_file_names = "; ".join(fn for _, fn in stmt_data)
    gl_file_names   = "; ".join(fn for _, fn in gl_data)

    def _save_failed_task(bc="", stmt_rc=0, gl_rc=0):
        try:
            return db.create_bank_recon_v2_task(
                user_id=str(user["id"]), tenant_id=user.get("tenant_id"),
                bank_code=bc, gl_account=gl_account,
                stmt_files=stmt_file_names, gl_files=gl_file_names,
                stmt_row_count=stmt_rc, gl_row_count=gl_rc,
                matched_count=0, unmatched_gl=0, unmatched_stmt=0,
                stmt_opening=0, stmt_closing=0, gl_opening=0, gl_closing=0,
                formula_diff=0, detail_json=[], summary_json={},
            )
        except Exception:
            return None

    # Hard parse errors (file couldn't be read at all) → save diagnostic task, return 200 ok:false
    stmt_errors = [r.get("error") for r in stmt_results if not r.get("ok")]
    gl_errors   = [r.get("error") for r in gl_results if not r.get("ok")]
    if stmt_errors or gl_errors:
        err_key = "stmt_parse_fail" if stmt_errors else "gl_parse_fail"
        err_msg = _brv2_err(err_key, lang,
                            e="; ".join(filter(None, (stmt_errors + gl_errors)[:2])))
        failed_id = _save_failed_task()
        return {"ok": False, "error": err_msg, "task_id": failed_id,
                "parse_info": parse_info, "stats": {}, "detail": [], "summary": {},
                "gl_accounts": []}

    # 3. Merge multi-file data
    stmt_rows, stmt_opening, stmt_closing, bank_code = merge_statements(list(stmt_results))
    gl_rows, gl_accounts, gl_opening, gl_closing = merge_gl_files(list(gl_results), gl_account)

    # No rows found → save diagnostic task, return 200 ok:false (not 422)
    if not stmt_rows or not gl_rows:
        err_key = "stmt_no_rows" if not stmt_rows else "gl_no_rows"
        err_msg = _brv2_err(err_key, lang)
        failed_id = _save_failed_task(
            bc=bank_code,
            stmt_rc=len(stmt_rows), gl_rc=len(gl_rows),
        )
        return {"ok": False, "error": err_msg, "task_id": failed_id,
                "parse_info": parse_info, "stats": {}, "detail": [], "summary": {},
                "gl_accounts": list(gl_accounts)}

    # 4. Reconcile
    recon_rows, summary = bank_reconcile(
        stmt_rows, gl_rows,
        stmt_opening=stmt_opening, gl_opening=gl_opening,
        stmt_closing=stmt_closing, gl_closing=gl_closing,
        bank_code=bank_code, gl_account_code=gl_account,
    )

    # 5. Serialize
    detail_j = rows_to_json(recon_rows)
    summary_j = bank_summary_to_json(summary)
    # v118.33.13.3 · embed real per-file parse_info into summary_json so the
    # Excel "File Info" sheet shows accurate per-file rows/bank when exporting
    # from history (previously it reconstructed bogus data using totals).
    # summary_from_json filters out unknown keys, so this is non-invasive.
    if isinstance(summary_j, dict):
        summary_j["_parse_info"] = parse_info

    # 6. Persist
    unmatched_gl   = summary.gl_debit_only_count + summary.gl_credit_only_count
    unmatched_stmt = summary.stmt_withdrawal_only_count + summary.stmt_deposit_only_count

    task_id = db.create_bank_recon_v2_task(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
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


@router.get("/bank-v2/tasks")
async def bank_v2_list_tasks(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    tasks = db.list_bank_recon_v2_tasks(
        user_id=str(user["id"]),
        tenant_id=user.get("tenant_id"),
        limit=50,
    )
    return {"ok": True, "tasks": tasks}


@router.get("/bank-v2/{task_id}")
async def bank_v2_get_task(task_id: int, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    task = db.get_bank_recon_v2_task(task_id)
    if not task:
        raise HTTPException(404, _brv2_err("task_not_found", "th"))
    import json as _j

    def _safe_json(v):
        if isinstance(v, str):
            try: return _j.loads(v)
            except: return v
        return v

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
            "matched": task.get("matched_count") or 0,
            "unmatched_gl": task.get("unmatched_gl") or 0,
            "unmatched_stmt": task.get("unmatched_stmt") or 0,
        },
        "stmt_opening": float(task.get("stmt_opening") or 0),
        "stmt_closing": float(task.get("stmt_closing") or 0),
        "gl_opening": float(task.get("gl_opening") or 0),
        "gl_closing": float(task.get("gl_closing") or 0),
        "formula_diff": float(task.get("formula_diff") or 0),
        "detail": _safe_json(task.get("detail_json")),
        "summary": _safe_json(task.get("summary_json")),
        "created_at": str(task.get("created_at") or ""),
    }


@router.get("/bank-v2/{task_id}/export")
async def bank_v2_export(task_id: int, request: Request, lang: str = "th"):
    """Export reconciliation result as Excel."""
    import json as _j, urllib.parse
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if lang not in ("th", "zh", "en", "ja"):
        lang = "th"

    task = db.get_bank_recon_v2_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    def _sj(v):
        if isinstance(v, str):
            try: return _j.loads(v)
            except: return []
        return v or []

    detail_raw = _sj(task.get("detail_json"))
    summary_raw = _sj(task.get("summary_json")) if isinstance(_sj(task.get("summary_json")), dict) else {}

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
                {"file": f.strip(), "rows": task.get("stmt_row_count", 0), "ok": True,
                 "bank_code": task.get("bank_code", "")}
                for f in (task.get("stmt_files") or "").split(";") if f.strip()
            ],
            "gl_files": [
                {"file": f.strip(), "rows": task.get("gl_row_count", 0), "ok": True,
                 "accounts": [task.get("gl_account") or ""]}
                for f in (task.get("gl_files") or "").split(";") if f.strip()
            ],
        }
    excel_bytes = export_bank_recon_excel(recon_rows, summary, lang=lang,
                                          task_info=task, parse_info=task_parse_info)

    bank_code = task.get("bank_code") or "bank"
    ascii_name = f"BankRecon_v2_{task_id}_{bank_code.upper()}.xlsx"
    utf8_name = urllib.parse.quote(ascii_name)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":
                 f"attachment; filename={ascii_name}; filename*=UTF-8''{utf8_name}"},
    )


@router.delete("/bank-v2/{task_id}")
async def bank_v2_delete(task_id: int, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    ok = db.delete_bank_recon_v2_task(task_id, str(user["id"]))
    if not ok:
        raise HTTPException(404, "任务不存在或无权删除")
    return {"ok": True}


class _BankV2BatchDeleteBody(BaseModel):
    ids: List[int]


@router.post("/bank-v2/tasks/batch_delete")
async def bank_v2_batch_delete(body: _BankV2BatchDeleteBody, request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    if not body.ids:
        return {"deleted": 0}
    deleted = db.delete_bank_recon_v2_tasks_batch(body.ids, str(user["id"]))
    return {"deleted": int(deleted)}
