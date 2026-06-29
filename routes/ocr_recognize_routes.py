"""
ocr_recognize_routes.py · POST /api/ocr/recognize 主路由(OCR 识别热路径)

薄壳:解析 HTTP request → 读 content → 调 services/ocr/recognize/core.run_recognition_core
(校验/缓存/闸/pipeline/persist/扣费/推送的单一事实源,与缺口④异步 worker 共用)→
调度 PDF 留底后台化 → 返回响应。
v1 别名 meta_aliases_routes.v1_recognize 通过 `from ocr_recognize_routes import ocr_recognize` 调到。
⚠️ 高敏:登录鉴权 + credits 计费扣费 + OCR pipeline 热路径 + ERP 自动推送(铁律 #26)。
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from services.ocr.recognize.core import run_recognition_core

logger = logging.getLogger("mr-pilot")
router = APIRouter()


@router.post("/api/ocr/recognize")
async def ocr_recognize(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),  # v27.8.1.13a · 右上角客户切换器选中时自动归属
    # B1 相 1 · workspace 账套归属 · 可选 · Form 或 header X-Workspace-Client-Id · 带不上 NULL。
    workspace_client_id: Optional[str] = Form(None),
):
    user = get_current_user_from_request(request)

    _ws_raw = workspace_client_id or request.headers.get("X-Workspace-Client-Id")
    _ws_client_id = int(_ws_raw) if (_ws_raw and str(_ws_raw).strip().isdigit()) else None

    content = await file.read()

    outcome = run_recognition_core(
        user, content, file, client_id=client_id, ws_client_id=_ws_client_id
    )

    # PDF 留底后台化:响应返回后才生成 searchable PDF + 回填 pdf_storage_path(前端 has_pdf 届时显示)。
    # 字段/响应一字不变;留底失败只是没下载。sync CPU/disk 走 to_thread 不堵 event loop。
    _schedule_pdf_backfill(user, content, outcome["raw_pages"], outcome["history_ids"])

    return outcome["response"]


def _schedule_pdf_backfill(user: dict, content: bytes, raw_pages: list, history_ids: list) -> None:
    """同步路由专用:有运行中的事件循环 → create_task 后台留底(worker 路径走内联,见 jobs/handler)。"""
    if not history_ids:
        return
    try:
        import asyncio

        _pdf_pages = raw_pages or []
        _pdf_uid = str(user["id"])
        _pdf_tid = _tid(user)
        _pdf_hids = list(history_ids)
        _pdf_content = content

        async def _bg_pdf_backfill():
            try:
                from services.ocr.pdf_backfill import generate_and_save_pdf

                rel, size = await asyncio.to_thread(
                    generate_and_save_pdf, _pdf_content, _pdf_pages, _pdf_uid
                )
                if rel:
                    await asyncio.to_thread(
                        db.update_ocr_history_pdf_storage, _pdf_hids, rel, size, _pdf_uid, _pdf_tid
                    )
            except Exception as _bge:
                logger.warning(f"[ocrperf] PDF 后台留底/回填失败(已忽略): {_bge}")

        asyncio.create_task(_bg_pdf_backfill())
    except Exception as _sched_err:
        logger.warning(f"[ocrperf] PDF 后台任务调度失败(已忽略): {_sched_err}")
