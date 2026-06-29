# -*- coding: utf-8 -*-
"""web_ocr 任务处理器(缺口④)。

worker 在线程里调本处理器:从暂存目录读文件 → 调 run_recognition_core
(与网页同步上传**同一份**校验/缓存/闸/pipeline/persist/扣费/推送逻辑)→ 内联 PDF 留底 →
返回 {"result": <同形 recognize 响应>, "history_ids": [...]}。

校验/非票/余额(HTTPException)→ ("__failed__", {error_code}) 让前端按失败展示明确原因;
其它异常 raise(worker 捕获置 failed,error_code 存真错)。max_attempts=1:不重试 → 不重扣/不重复落库。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from core import db
from core.route_helpers import _tid
from . import worker as _worker

logger = logging.getLogger("ocr_jobs.handler")

JOB_TYPE = "web_ocr"


class _StagedFile:
    """run_recognition_core 只用 file.filename(persist/cache 同),给个轻量替身即可。"""

    def __init__(self, filename: str):
        self.filename = filename


def _staged_path(params: Dict[str, Any], input_ref: list) -> Optional[str]:
    job_id = params.get("job_id")
    filename = params.get("filename")
    if not job_id or not filename:
        # 兜底:input_ref 里带了显式路径
        for ref in input_ref or []:
            if isinstance(ref, dict) and ref.get("path"):
                return ref["path"]
        return None
    return os.path.join(_worker.stage_dir_for(str(job_id)), str(filename))


def _error_code_from_http(exc) -> str:
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        return str(detail.get("code") or detail.get("error_code") or "ocr_failed")
    if isinstance(detail, str):
        return detail
    return "ocr_failed"


def handle_web_ocr(
    params: Dict[str, Any], input_ref: list, progress_cb: Callable
) -> Union[Dict[str, Any], Tuple[str, dict]]:
    from fastapi import HTTPException

    from services.ocr.recognize.core import run_recognition_core

    user_id = params.get("user_id")
    user = db.find_user_by_id(str(user_id)) if user_id else None
    if not user:
        return ("__failed__", {"error_code": "user_not_found"})

    path = _staged_path(params, input_ref)
    if not path or not os.path.isfile(path):
        return ("__failed__", {"error_code": "staged_file_missing"})

    with open(path, "rb") as fh:
        content = fh.read()

    filename = str(params.get("filename") or os.path.basename(path) or "upload")
    file = _StagedFile(filename)
    client_id = params.get("client_id")
    ws_raw = params.get("workspace_client_id")
    ws_client_id = int(ws_raw) if (ws_raw is not None and str(ws_raw).strip().isdigit()) else None

    progress_cb({"stage": "running", "filename": filename})

    try:
        outcome = run_recognition_core(
            user, content, file, client_id=client_id, ws_client_id=ws_client_id
        )
    except HTTPException as he:
        # 校验/非票/余额不足:终态失败,前端按明确原因展示(绝不冒充完成)。
        return ("__failed__", {"error_code": _error_code_from_http(he)})

    history_ids: List[str] = outcome.get("history_ids") or []
    # PDF 留底:同步路由走 create_task,worker 无事件循环 → 内联同步生成+回填。
    if history_ids:
        try:
            from services.ocr.pdf_backfill import generate_and_save_pdf

            rel, size = generate_and_save_pdf(
                content, outcome.get("raw_pages") or [], str(user["id"])
            )
            if rel:
                db.update_ocr_history_pdf_storage(
                    history_ids, rel, size, str(user["id"]), _tid(user)
                )
        except Exception as _bge:
            logger.warning(f"[ocr-job] PDF 留底/回填失败(已忽略): {_bge}")

    return {"result": outcome.get("response"), "history_ids": history_ids}


def _register() -> None:
    _worker.register_handler(JOB_TYPE, handle_web_ocr)
