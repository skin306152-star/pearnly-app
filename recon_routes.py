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
# P1.2-M2 · 发票侧字段级用户校正(铁律 #21 独立 service)
from services.recon.field_override import record_field_override, ALLOWED_FIELDS as _OVERRIDE_FIELDS
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
        "zh": "在文件里没找到收入科目数据。请确认右侧上传的是『总账 GL』(Excel/CSV · 至少含日期/科目/借方/贷方列)· 如果你的收入科目不是 4 开头,请调右侧『收入科目前缀』",
        "en": "No revenue account rows found. Please upload a General Ledger file (Excel/CSV with Date/Account/Debit/Credit columns) · If your revenue accounts don't start with '4', adjust the 'Revenue Account Prefix' on the right",
        "th": "ไม่พบรายการบัญชีรายได้ในไฟล์ · กรุณาอัปโหลดบัญชีแยกประเภท GL (Excel/CSV ที่มีคอลัมน์ วันที่/รหัสบัญชี/เดบิต/เครดิต) · หากบัญชีรายได้ไม่ขึ้นต้นด้วย 4 ให้ปรับ 'รหัสนำหน้าบัญชีรายได้' ด้านขวา",
        "ja": "ファイルに収益科目データが見つかりません · 右側に『総勘定元帳 GL』(日付/科目/借方/貸方列のある Excel/CSV) をアップロードしてください · 収益科目が 4 以外で始まる場合は右側の『収益科目接頭辞』を変更してください",
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


class FieldOverrideBody(BaseModel):
    field: str
    user_value: Optional[str] = None  # 空/None = 撤销该字段校正(还原 OCR)


@router.patch("/row/{row_id}/field")
async def row_field_override(row_id: int, body: FieldOverrideBody, request: Request):
    """P1.2-M2 · 用户校正发票侧 OCR 字段 · 记 OCR 原值 vs 用户值到 field_overrides"""
    user = get_current_user_from_request(request)
    if not user: raise HTTPException(401, "未登录")
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
    gl_list:  List[UploadFile] = list(gl_files or [])
    vat_list: List[UploadFile] = list(vat_files or [])
    if gl_file is not None:
        gl_list.append(gl_file)
    if vat_file is not None:
        vat_list.append(vat_file)
    if not gl_list or not vat_list:
        raise HTTPException(422, _glv_err("gl_parse_failed", lang, e="missing files"))

    # 读所有字节
    gl_data:  List[tuple] = []
    vat_data: List[tuple] = []
    for f in gl_list:
        gl_data.append((await f.read(), f.filename or "gl.pdf"))
    for f in vat_list:
        vat_data.append((await f.read(), f.filename or "vat.pdf"))

    gl_name  = "; ".join(fn for _, fn in gl_data)
    vat_name = "; ".join(fn for _, fn in vat_data)
    api_key = _user_key(user)

    # 1. 并行解析所有 GL 文件 + 合并 rows
    import asyncio
    loop = asyncio.get_event_loop()
    gl_results = await asyncio.gather(*[
        loop.run_in_executor(None, lambda b=b, n=n: parse_gl(b, n, revenue_prefix or "4"))
        for b, n in gl_data
    ])
    gl_errors = [r.get("error") for r in gl_results if not r.get("ok") and r.get("error")]
    if gl_errors and not any(r.get("rows") for r in gl_results):
        # 所有 GL 都解析失败
        raise HTTPException(422, _glv_err("gl_parse_failed", lang,
                                          e="; ".join(filter(None, gl_errors))[:200]))
    merged_gl_rows = []
    for r in gl_results:
        merged_gl_rows.extend(r.get("rows") or [])
    if not merged_gl_rows:
        logger.warning(f"[gl-vat] GL parsed but 0 revenue rows · files={gl_name} · "
                       f"prefix={revenue_prefix}")
        raise HTTPException(422, _glv_err("gl_no_revenue_rows", lang))
    gl_result = {"ok": True, "rows": merged_gl_rows,
                 "row_count": sum(r.get("row_count") or 0 for r in gl_results)}

    # 2. 并行解析所有 VAT 报表 + 合并 rows
    vat_results = await asyncio.gather(*[
        loop.run_in_executor(None, lambda b=b, n=n: parse_vat_report(b, n, api_key=api_key))
        for b, n in vat_data
    ])
    vat_errors = [r.get("error") for r in vat_results if not r.get("ok") and r.get("error")]
    if vat_errors and not any(r.get("rows") for r in vat_results):
        raise HTTPException(422, _glv_err("vat_parse_failed", lang,
                                          e="; ".join(filter(None, vat_errors))[:200]))
    merged_vat_rows = []
    for r in vat_results:
        merged_vat_rows.extend(r.get("rows") or [])
    if not merged_vat_rows:
        raise HTTPException(422, _glv_err("vat_no_rows", lang))
    vat_result = {"ok": True, "rows": merged_vat_rows,
                  "row_count": sum(r.get("row_count") or 0 for r in vat_results)}

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


# v118.35.0.54 · 输入不匹配警告(GL 与对账单期间/科目对不上)· 防止系统闷头算出
# 让用户看不懂的差额、误以为系统坏了。返回 warnings 数组 · 前端显示提示条。
_BRV2_WARN = {
    "period_mismatch": {
        "zh": "⚠️ GL 与对账单的期间不重叠(GL:{g};对账单:{s})。很可能上传了不同期间的文件,请核对后重新上传同一期间的 GL 与对账单。",
        "en": "⚠️ The GL and bank statement periods do not overlap (GL: {g}; statement: {s}). You may have uploaded files from different periods — please re-upload the GL and statement for the same period.",
        "th": "⚠️ ช่วงเวลาของ GL กับใบแจ้งยอดไม่ตรงกัน (GL: {g}; ใบแจ้งยอด: {s}) อาจอัปโหลดไฟล์คนละช่วงเวลา กรุณาตรวจสอบและอัปโหลด GL กับใบแจ้งยอดของช่วงเวลาเดียวกัน",
        "ja": "⚠️ GL と明細の期間が重なっていません(GL:{g};明細:{s})。異なる期間のファイルをアップロードした可能性があります。同じ期間の GL と明細を再アップロードしてください。",
    },
    "gl_too_few": {
        "zh": "⚠️ GL 只有 {n} 行,而对账单有 {m} 行,差距过大。可能上传了不完整或不对应的 GL,对账结果可能无意义。",
        "en": "⚠️ The GL has only {n} row(s) but the statement has {m}. This large gap suggests an incomplete or mismatched GL — the reconciliation result may be meaningless.",
        "th": "⚠️ GL มีเพียง {n} รายการ แต่ใบแจ้งยอดมี {m} รายการ ความต่างมากเกินไป อาจเป็น GL ที่ไม่สมบูรณ์หรือไม่ตรงกัน ผลกระทบยอดอาจไม่มีความหมาย",
        "ja": "⚠️ GL は {n} 行のみですが明細は {m} 行あります。差が大きすぎるため、不完全または不一致の GL の可能性があり、照合結果が無意味になる場合があります。",
    },
    "no_match": {
        "zh": "⚠️ 没有任何记录匹配成功。请确认 GL 与对账单是否为同一账户、同一期间。",
        "en": "⚠️ No records matched at all. Please confirm the GL and statement are for the same account and period.",
        "th": "⚠️ ไม่มีรายการใดจับคู่สำเร็จ กรุณายืนยันว่า GL กับใบแจ้งยอดเป็นบัญชีและช่วงเวลาเดียวกัน",
        "ja": "⚠️ 一致したレコードがありません。GL と明細が同じ口座・同じ期間か確認してください。",
    },
    # v118.35.0.63 · 提取行与账单印刷合计/笔数/期末对不上 → 多半漏行或读错 · 主动提示核对
    "completeness": {
        "zh": "⚠️ 对账单完整性检查未通过:{detail}。这通常意味着有交易未被识别(漏行)或金额读错,请对照原始账单核对,必要时手动补充。",
        "en": "⚠️ Statement completeness check failed: {detail}. This usually means a transaction was missed or an amount misread — please check against the original statement and add any missing rows.",
        "th": "⚠️ การตรวจความครบถ้วนของใบแจ้งยอดไม่ผ่าน: {detail} มักหมายถึงมีรายการตกหล่นหรืออ่านยอดผิด กรุณาตรวจกับใบแจ้งยอดต้นฉบับและเพิ่มรายการที่ขาด",
        "ja": "⚠️ 明細の完全性チェックに失敗: {detail}。取引の取りこぼしや金額の誤読の可能性があります。元の明細と照合し、不足行を補ってください。",
    },
    # v118.35.0.61 · 一个文件含多个账户(每 sheet 一个)· 已分账户独立校验余额 · 提示用户
    "multi_account": {
        "zh": "⚠️ 此对账单文件含 {n} 个账户({codes})。系统已『分账户』独立核对各自余额,但银行对账需 GL 与单一账户对应。若 GL 只含其中某一个账户,请只看对应账户的结果。",
        "en": "⚠️ This statement file contains {n} accounts ({codes}). Each account's balance was verified separately, but reconciliation requires the GL to match a single account. If your GL covers only one of them, refer to that account's result only.",
        "th": "⚠️ ไฟล์ใบแจ้งยอดนี้มี {n} บัญชี ({codes}) ระบบตรวจยอดแต่ละบัญชีแยกกันแล้ว แต่การกระทบยอดต้องให้ GL ตรงกับบัญชีเดียว หาก GL มีเพียงบัญชีเดียว ให้ดูเฉพาะผลของบัญชีนั้น",
        "ja": "⚠️ この明細ファイルには {n} 口座（{codes}）が含まれます。各口座の残高は個別に検証済みですが、照合には GL が単一口座に対応している必要があります。GL が 1 口座のみの場合、その口座の結果のみを参照してください。",
    },
}


_ROWS_PER_PAGE_BILLING = 40  # v0.58 · 居中计费:一页约 40 笔 · 防密集账单按页低估


def _pdf_billing_units(page_count: int, row_count: int) -> int:
    """v118.35.0.58 · 银行对账 PDF/图片计费『页数』· 居中口径 max(实际页数, ⌈行数/N⌉)。
    对齐 ฿1.5/页规则 · 修复此前误按交易行数计费(超收 10-34 倍)的 bug。
    既不让多页大账单超收 · 也不让一页塞很多笔的密集账单被低估 · 图片=1 页。"""
    import math as _m
    pages = max(1, int(page_count or 0))
    rows = max(0, int(row_count or 0))
    return max(pages, _m.ceil(rows / _ROWS_PER_PAGE_BILLING))


def _brv2_warn(key: str, lang: str = "th", **fmt) -> str:
    lang = lang if lang in ("zh", "en", "th", "ja") else "th"
    msg = (_BRV2_WARN.get(key) or {}).get(lang) or (_BRV2_WARN.get(key) or {}).get("en") or key
    return msg.format(**fmt) if fmt else msg


_COMP_LBL = {
    "credit": {"zh": "存款", "en": "credits", "th": "ฝาก", "ja": "入金"},
    "debit":  {"zh": "取款", "en": "debits", "th": "ถอน", "ja": "出金"},
    "cnt":    {"zh": "笔数", "en": "count", "th": "จำนวน", "ja": "件数"},
    "sum":    {"zh": "合计", "en": "sum", "th": "ยอดรวม", "ja": "合計"},
    "printed": {"zh": "账单印", "en": "stmt prints", "th": "ใบแจ้งยอด", "ja": "明細表記"},
    "got":    {"zh": "识别", "en": "extracted", "th": "อ่านได้", "ja": "抽出"},
    "close":  {"zh": "期末", "en": "closing", "th": "ยอดปิด", "ja": "期末"},
    "calc":   {"zh": "算得", "en": "calculated", "th": "คำนวณ", "ja": "計算"},
}


def _completeness_details(issues, lang) -> list:
    """v118.35.0.63 · 把完整性 issue 列表转成简短可读的提示片段(跟 lang 走)。"""
    def L(k):
        return (_COMP_LBL.get(k) or {}).get(lang) or (_COMP_LBL.get(k) or {}).get("en") or k
    out = []
    for it in (issues or []):
        t = it.get("type", "")
        if t == "credit_count_mismatch":
            out.append(f"{L('credit')}{L('cnt')}({L('printed')}{it['printed']}/{L('got')}{it['count']})")
        elif t == "debit_count_mismatch":
            out.append(f"{L('debit')}{L('cnt')}({L('printed')}{it['printed']}/{L('got')}{it['count']})")
        elif t == "credit_sum_mismatch":
            out.append(f"{L('credit')}{L('sum')}({L('printed')}{it['printed']:,.0f}/{L('got')}{it['sum']:,.0f})")
        elif t == "debit_sum_mismatch":
            out.append(f"{L('debit')}{L('sum')}({L('printed')}{it['printed']:,.0f}/{L('got')}{it['sum']:,.0f})")
        elif t == "closing_mismatch":
            out.append(f"{L('close')}({L('printed')}{it['printed']:,.0f}/{L('calc')}{it['calc']:,.0f})")
    return out


def _detect_recon_mismatch(stmt_rows, gl_rows, matched_count, lang) -> list:
    """v118.35.0.54 · 检测 GL 与对账单是否明显不匹配 · 返回 4 语警告字符串列表(可空)。"""
    warnings = []
    try:
        s_dates = [r.date for r in stmt_rows if getattr(r, "date", None)]
        g_dates = [r.date for r in gl_rows if getattr(r, "date", None)]
        if s_dates and g_dates:
            smin, smax, gmin, gmax = min(s_dates), max(s_dates), min(g_dates), max(g_dates)
            if smax < gmin or gmax < smin:  # 完全不重叠
                warnings.append(_brv2_warn("period_mismatch", lang,
                                           g=f"{gmin}~{gmax}", s=f"{smin}~{smax}"))
        # v118.35.0.61 · 改比例阈值:GL 行数 < 对账单 20% 且账单≥20 行 → 规模悬殊预警
        # (旧阈值 GL≤2 太严 · 12 行 GL 对 237 行账单这种明显不对应的情况漏报)
        if len(stmt_rows) >= 20 and len(gl_rows) * 5 < len(stmt_rows):
            warnings.append(_brv2_warn("gl_too_few", lang, n=len(gl_rows), m=len(stmt_rows)))
        if matched_count == 0 and (len(stmt_rows) + len(gl_rows)) >= 10:
            warnings.append(_brv2_warn("no_match", lang))
    except Exception:
        pass
    return warnings


def _apply_anchor_overrides(
    stmt_opening: float, gl_opening: float, gl_closing: float, stmt_closing: float,
    stmt_opening_override: Optional[float],
    gl_opening_override: Optional[float],
    gl_closing_override: Optional[float],
    stmt_closing_override: Optional[float] = None,
):
    """
    P0.1 BUG-B-T1 v118.35.0.37 · 把『OCR snapshot + override 替换』封装成纯函数 · 守门测试容易
    BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing(Statement 期末)· 客户反馈 OCR 95% 准
                                · 5% 抽不准时需要兜底框
    Always returns the OCR snapshot (even when no override) so the frontend can prefill
    the 4 anchor inputs next time (localStorage) and Excel/history can show OCR vs user.
    Returns: (final_stmt_open, final_gl_open, final_gl_close, final_stmt_close,
              anchor_ocr_dict, anchor_overrides_dict)
    """
    anchor_ocr = {
        "stmt_opening": stmt_opening,
        "gl_opening": gl_opening,
        "gl_closing": gl_closing,
        "stmt_closing": stmt_closing,
    }
    anchor_overrides = {}
    if stmt_opening_override is not None:
        anchor_overrides["stmt_opening"] = {"ocr": stmt_opening, "user": float(stmt_opening_override)}
        stmt_opening = float(stmt_opening_override)
    if gl_opening_override is not None:
        anchor_overrides["gl_opening"] = {"ocr": gl_opening, "user": float(gl_opening_override)}
        gl_opening = float(gl_opening_override)
    if gl_closing_override is not None:
        anchor_overrides["gl_closing"] = {"ocr": gl_closing, "user": float(gl_closing_override)}
        gl_closing = float(gl_closing_override)
    if stmt_closing_override is not None:
        anchor_overrides["stmt_closing"] = {"ocr": stmt_closing, "user": float(stmt_closing_override)}
        stmt_closing = float(stmt_closing_override)
    return stmt_opening, gl_opening, gl_closing, stmt_closing, anchor_ocr, anchor_overrides


@router.post("/bank-v2/run")
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
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, _brv2_err("auth_required", lang))

    if not stmt_files:
        raise HTTPException(422, _brv2_err("no_stmt_files", lang))
    if not gl_files:
        raise HTTPException(422, _brv2_err("no_gl_files", lang))

    # v118.35.0.21 · Credits 前置检查(1 次 SELECT · 异步扣费)
    _billing_bv2 = {"is_exempt": True, "pages_used_this_month": 0}
    try:
        import db as _db_credit
        _tid_bv2 = user.get("tenant_id")
        _billing_bv2 = _db_credit.get_billing_status_combined(str(user.get("id")), _tid_bv2)
        if not _billing_bv2.get("allowed") and not _billing_bv2.get("is_exempt"):
            _est_cost = float(_db_credit.estimate_pdf_cost_thb(
                _billing_bv2.get("pages_used_this_month", 0),
                len(stmt_files) + len(gl_files)))
            raise HTTPException(402, detail={
                "code": "insufficient_balance",
                "balance": _billing_bv2.get("balance_thb", 0.0),
                "estimated_cost": _est_cost,
                "pages_used_this_month": _billing_bv2.get("pages_used_this_month", 0),
            })
    except HTTPException:
        raise
    except Exception as _be:
        import logging as _lg_pre
        _lg_pre.getLogger('recon').warning(f"[bank_v2.credits] pre-check skip: {_be}")

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

    # v118.35.0.21 · 异步扣费 · 按文件扩展名分 pdf/excel 两种 kind
    if not _billing_bv2.get("is_exempt"):
        try:
            import db as _db_chg
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
                asyncio.create_task(asyncio.to_thread(
                    _db_chg.charge_ocr_async,
                    str(user.get("id")), _tid_chg, "pdf", _pdf_units,
                    None, f"银行对账 PDF · {_pdf_units} 页"))
            if _excel_units > 0:
                asyncio.create_task(asyncio.to_thread(
                    _db_chg.charge_ocr_async,
                    str(user.get("id")), _tid_chg, "excel", _excel_units,
                    None, f"银行对账 Excel · {_excel_units} 字符"))
        except Exception as _ce:
            import logging as _lg_ce
            _lg_ce.getLogger('recon').warning(f"💳 bank_v2 async charge skip: {_ce}")

    # v118.35.0.19 · per-file parse diagnostics 带 error_code 字段 · 前端用它做 i18n 翻译
    parse_info = {
        "stmt_files": [
            {"file": fn, "rows": len(r.get("rows") or []),
             "ok": r.get("ok", False), "error": r.get("error"),
             "error_code": r.get("error_code"),
             "bank_code": r.get("bank_code", "")}
            for r, (_, fn) in zip(stmt_results, stmt_data)
        ],
        "gl_files": [
            {"file": fn, "rows": len(r.get("rows") or []),
             "ok": r.get("ok", False), "error": r.get("error"),
             "error_code": r.get("error_code"),
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

    # v118.35.0.53 · 部分文件失败容错:一个坏文件不再拖垮整批。
    # merge_statements/merge_gl_files 本就跳过 not-ok 的结果 · 这里只在『某一侧全部失败』时硬报错。
    # 部分失败 → 跳过坏文件、用成功的继续 · 失败文件在 parse_info 里逐个标出(前端可显示)。
    stmt_ok_n = sum(1 for r in stmt_results if r.get("ok"))
    gl_ok_n   = sum(1 for r in gl_results if r.get("ok"))
    stmt_errors = [r.get("error") for r in stmt_results if not r.get("ok")]
    gl_errors   = [r.get("error") for r in gl_results if not r.get("ok")]
    skipped_files = [fn for r, (_, fn) in zip(stmt_results, stmt_data) if not r.get("ok")] + \
                    [fn for r, (_, fn) in zip(gl_results, gl_data) if not r.get("ok")]
    if stmt_ok_n == 0 or gl_ok_n == 0:
        # 整侧全失败才真失败(对账单全坏 或 GL 全坏)
        err_key = "stmt_parse_fail" if stmt_ok_n == 0 else "gl_parse_fail"
        err_msg = _brv2_err(err_key, lang,
                            e="; ".join(filter(None, (stmt_errors + gl_errors)[:2])))
        failed_id = _save_failed_task()
        return {"ok": False, "error": err_msg, "task_id": failed_id,
                "parse_info": parse_info, "stats": {}, "detail": [], "summary": {},
                "gl_accounts": []}

    # 3. Merge multi-file data
    stmt_rows, stmt_opening, stmt_closing, bank_code = merge_statements(list(stmt_results))
    gl_rows, gl_accounts, gl_opening, gl_closing = merge_gl_files(list(gl_results), gl_account)

    # BUG-B v118.35.0.36 · 用户在前端 anchor TEXT BOX 填了值就用用户的 · OCR 的降级成参考
    # P0.1 BUG-B-T1 v118.35.0.37 · 抽成 _apply_anchor_overrides 纯函数 · 总是 snapshot OCR 给前端预填用
    # BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing
    (stmt_opening, gl_opening, gl_closing, stmt_closing,
     _anchor_ocr_snapshot, _anchor_used) = _apply_anchor_overrides(
        stmt_opening, gl_opening, gl_closing, stmt_closing,
        stmt_opening_override, gl_opening_override, gl_closing_override,
        stmt_closing_override,
    )
    if _anchor_used:
        logger.info(f"[bank_v2_run] anchor overrides applied: {_anchor_used} · "
                    f"user_id={user.get('id')}")

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
        brv2_warnings.append(_brv2_warn(
            "multi_account", lang, n=len(_seen), codes="、".join(_seen)))

    # v118.35.0.63 · 完整性交叉校验:提取行 vs 账单印刷合计/笔数/期末对不上 → 主动提示漏行
    _comp_details = []
    for _r in stmt_results:
        comp = _r.get("completeness") if _r.get("ok") else None
        if comp and not comp.get("ok"):
            _comp_details.extend(_completeness_details(comp["issues"], lang))
    if _comp_details:
        brv2_warnings.append(_brv2_warn(
            "completeness", lang, detail="；".join(_comp_details[:4])))

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
        "skipped_files": skipped_files,  # v118.35.0.53 · 部分失败被跳过的文件 · 前端可提示
        "warnings": brv2_warnings,       # v118.35.0.54 · 输入不匹配警告(期间/规模)· 前端显示提示条
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
    """v118.35.0.29 P0 隔离 (体检 2026-05-21 风险 2) · 镜像 gl_vat 修复"""
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    task = db.get_bank_recon_v2_task(task_id, str(user["id"]), user.get("tenant_id"))
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

    # v118.35.0.29 P0 隔离修复(体检风险 2) · 强制 user_id + tenant_id scope
    task = db.get_bank_recon_v2_task(task_id, str(user["id"]), user.get("tenant_id"))
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
    # P0.2 BUG-B-T2 v118.35.0.38 · summary_raw 还含 _anchor_overrides + _anchor_ocr · 单独传给 export
    # bank_summary_from_json 过滤掉 `_` 开头字段 · 所以这里要从原 summary_raw 拿
    _ao = summary_raw.get("_anchor_overrides") if isinstance(summary_raw, dict) else None
    _aocr = summary_raw.get("_anchor_ocr") if isinstance(summary_raw, dict) else None
    _warns = summary_raw.get("_brv2_warnings") if isinstance(summary_raw, dict) else None
    excel_bytes = export_bank_recon_excel(recon_rows, summary, lang=lang,
                                          task_info=task, parse_info=task_parse_info,
                                          anchor_overrides=_ao, anchor_ocr=_aocr,
                                          warnings=_warns)

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
