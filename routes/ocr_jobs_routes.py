# -*- coding: utf-8 -*-
"""网页 OCR 上传 · 异步 submit + 状态查询路由(缺口④)。

加性改造(铁律 #17:新路由进 *_routes.py · 不进 app.py):
  - 老 POST /api/ocr/recognize(同步)**保持不动**(flag off 时前端仍走它)。
  - 新增 submit(秒回 job_id)+ 状态查询。重活由后台 worker 跑 services/ocr/jobs/handler。

submit:鉴权 + 暂存落盘 + 建 job + 秒回。**不在此做缓存/余额闸**——交给 job 内的
run_recognition_core 统一处理"缓存先于余额闸"(0 余额复用旧结果)且闸在 pipeline 之前
(0 余额不产生 OCR 成本),既保契约又不重复钱逻辑。
状态:GET /api/ocr/jobs/{id} → {status, progress, result(done 时同形 recognize 响应), error_code}。
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from services.ocr.jobs import store, worker

logger = logging.getLogger("ocr_jobs.routes")
router = APIRouter(tags=["ocr-jobs"])


@router.post("/api/ocr/submit")
async def ocr_submit(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),
    workspace_client_id: Optional[str] = Form(None),
):
    """异步上传:暂存文件 + 入队 + 秒回 job_id。前端随后轮询 /api/ocr/jobs/{id}。"""
    user = get_current_user_from_request(request)

    _ws_raw = workspace_client_id or request.headers.get("X-Workspace-Client-Id")
    ws_client_id = int(_ws_raw) if (_ws_raw and str(_ws_raw).strip().isdigit()) else None

    job_id = str(uuid.uuid4())
    stage_dir = worker.stage_dir_for(job_id)
    try:
        os.makedirs(stage_dir, exist_ok=True)
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(400, detail="ocr.empty_file")
        disk_name = os.path.basename(file.filename or "upload") or "upload"
        path = os.path.join(stage_dir, disk_name)
        with open(path, "wb") as out:
            out.write(content)
    except HTTPException:
        worker._cleanup_stage(job_id)
        raise
    except Exception as e:  # noqa: BLE001
        worker._cleanup_stage(job_id)
        logger.error(f"[ocr-submit] stage failed: {e}")
        raise HTTPException(500, detail="ocr.submit_failed")

    params = {
        "filename": disk_name,
        "client_id": client_id,
        "workspace_client_id": ws_client_id,
    }
    rid = store.enqueue(
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        params=params,
        input_ref=[{"path": path, "filename": file.filename or disk_name}],
        job_id=job_id,
        workspace_client_id=ws_client_id,
        max_attempts=1,  # 不重试 → 任务至多执行一次 → 扣费/落库至多一次
    )
    if not rid:
        worker._cleanup_stage(job_id)
        raise HTTPException(500, detail="ocr.submit_failed")
    return {"ok": True, "job_id": rid}


@router.get("/api/ocr/jobs/{job_id}")
async def get_ocr_job(job_id: str, request: Request):
    """轮询任务状态;done 时 result 即同形 recognize 响应(前端 ingestResult 直接用)。"""
    user = get_current_user_from_request(request)
    job = store.get(job_id, user_id=str(user["id"]), tenant_id=user.get("tenant_id"))
    if not job:
        raise HTTPException(404, detail="ocr.job_not_found")
    status = job.get("status")
    return {
        "ok": True,
        "job_id": job["id"],
        "status": status,
        "progress": job.get("progress") or {},
        "result": job.get("result") if status == "done" else None,
        "error_code": job.get("error_code"),
        "created_at": job.get("created_at"),
        "finished_at": job.get("finished_at"),
    }
