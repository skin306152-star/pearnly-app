# -*- coding: utf-8 -*-
"""进项外流导出路由 · Excel 同步下载 / Drive·Sheet 异步归档(契约 05 §2.1)。

excel = 零授权同步返 xlsx blob;drive/sheet = 检查 Google 已连 → 入 recon_jobs 异步队列
(job_type=export)返 job_id,GET 轮询进度。套账隔离 + expense 门控走 purchase_common。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, gate, resolve_ws, uid as _uid
from services.export import archive as archive_svc
from services.export import google_store

router = APIRouter(prefix="/api/purchase", tags=["purchase-export"])

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ExportIn(BaseModel):
    workspace_client_id: Optional[int] = None
    format: str = "excel"  # excel | drive | sheet
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    lang: str = "th"  # 导出文件列头/枚举值跟随用户语言(zh/en/th/ja)


@router.post("/export")
async def api_export(req: ExportIn, request: Request):
    user, tid = auth_member(request, "purchase.doc.view")
    fmt = (req.format or "excel").lower()

    if fmt == "excel":
        with db.get_cursor_rls(tid, commit=False) as cur:
            gate(cur, tid)
            ws = resolve_ws(cur, request, tid, req.workspace_client_id)
            xlsx = archive_svc.excel_bytes(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                date_from=req.date_from,
                date_to=req.date_to,
                lang=req.lang,
            )
        return Response(
            content=xlsx,
            media_type=_XLSX_MIME,
            headers={"Content-Disposition": "attachment; filename=purchase_export.xlsx"},
        )

    if fmt not in ("drive", "sheet"):
        raise PosError("purchase.line_invalid", 422, detail="bad_format")

    from services.recon_jobs import store as jobs

    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        cred = google_store.get_credential(cur, tenant_id=tid, workspace_client_id=ws)
    if not cred:
        # 未授权 → 前端引导去集成中心连 Google 再回来。
        raise PosError("purchase.unexpected", 412, detail="google_not_connected")

    job_id = jobs.enqueue(
        "export",
        user_id=_uid(user),
        tenant_id=tid,
        params={
            "format": fmt,
            "date_from": req.date_from,
            "date_to": req.date_to,
            "lang": req.lang,
        },
        workspace_client_id=ws,
    )
    if not job_id:
        raise PosError("purchase.unexpected", 500, detail="enqueue_failed")
    return ok({"job_id": job_id, "status": "queued"})


@router.get("/export/{job_id}")
async def api_export_status(job_id: str, request: Request):
    user, tid = auth_member(request, "purchase.doc.view")
    from services.recon_jobs import store as jobs

    job = jobs.get(job_id, user_id=_uid(user), tenant_id=tid)
    if not job:
        raise PosError("purchase.unexpected", 404, detail="job_not_found")
    progress = job.get("progress") or {}
    return ok(
        {
            "status": job.get("status"),
            "done_n": progress.get("done_n", 0),
            "skip_n": progress.get("skip_n", 0),
            "total": progress.get("total", 0),
            "sheet_url": progress.get("sheet_url", ""),
            "drive_url": progress.get("drive_url", ""),
            "error": job.get("error_code"),
        }
    )
