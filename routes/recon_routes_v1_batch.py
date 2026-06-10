# -*- coding: utf-8 -*-
"""收入对账 · 批量智能识别(屏 B)+ 任务删除路由组 · recon_routes 拆分。

verbatim 抽出·0 逻辑改(仅装饰器对象名)。delete_one_task 复用 batch_delete_tasks。"""

import json
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from pydantic import BaseModel

from core import db
from services.authz.deps import require_perm
from services.vat.vat_report_parser import parse_vat_report
from routes.recon_routes_shared import _user_key
from routes.recon_routes_progress import _progress_init, _progress_update

logger = logging.getLogger(__name__)

v1batch_router = APIRouter()


# ======================================================================
# 屏 B · 批量智能识别
# ======================================================================


@v1batch_router.post("/batch_process")
async def batch_process(
    request: Request,
    confirmed_groups_json: str = Form(...),
    files: List[UploadFile] = File(...),
    progress_id: Optional[str] = Form(None),
):
    """v118.32.2 · 屏 B · 用户确认分组后 · OCR 发票 + 解析报告 + 建任务
    v118.32.4 · 拆两阶段 + 进度上报 + parse_vat_report 走 run_in_executor 防阻塞"""
    user = require_perm(request, "recon.create")
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


# ======================================================================
# v118.32.3 · 任务删除(单条 + 批量) · 顺便清掉对应的 OCR 缓存
# ======================================================================
class _DeleteIdsBody(BaseModel):
    ids: List[int]


@v1batch_router.post("/tasks/batch_delete")
async def batch_delete_tasks(body: _DeleteIdsBody, request: Request):
    """删除多个对账任务 · 同时清:
    - reconciliation_row(该任务的所有 diff 行)
    - reconciliation_task(任务本身)
    - ocr_history(本任务上传的发票 · 按 source_ref=task_id 关联)
    - vat_report(该任务的 VAT 报告解析结果 · 仅当无其他任务引用)
    """
    user = require_perm(request, "recon.create")
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


@v1batch_router.delete("/task/{task_id}")
async def delete_one_task(task_id: int, request: Request):
    """单条删除 · 复用批量逻辑"""
    return await batch_delete_tasks(_DeleteIdsBody(ids=[task_id]), request)
