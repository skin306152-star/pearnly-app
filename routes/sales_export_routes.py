# -*- coding: utf-8 -*-
"""ERP 销售记录导出与 Google Drive 归档。"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core import db
from core import workspace_context as wc
from core.pos_api import PosError, ok
from services.authz.deps import require_perm_tid
from services.export import google_store

router = APIRouter(prefix="/api/sales", tags=["sales-export"])


class SalesExportIn(BaseModel):
    workspace_client_id: Optional[int] = None
    history_ids: list[str] = Field(min_length=1, max_length=500)
    format: str = "drive"
    lang: str = "th"


@router.post("/export")
async def api_sales_export(req: SalesExportIn, request: Request):
    tid, uid = require_perm_tid(request, "sales.doc.view")
    if req.format != "drive":
        raise PosError("sales.bad_export_format", 422, detail="bad_format")

    with db.get_cursor_rls(tid, commit=False) as cur:
        active_ws = wc.resolve_active_workspace_id(cur, request, tenant_id=tid)
        ws = int(req.workspace_client_id) if req.workspace_client_id is not None else active_ws
        if ws is None or (active_ws is not None and int(active_ws) != int(ws)):
            raise PosError("workspace.required", 422, detail="workspace_mismatch")
        credential = google_store.get_credential(cur, tenant_id=tid, workspace_client_id=int(ws))
    if not credential:
        raise PosError("sales.google_not_connected", 412, detail="google_not_connected")

    from services.recon_jobs import store as jobs

    job_id = jobs.enqueue(
        "export",
        user_id=str(uid),
        tenant_id=str(tid),
        params={
            "source_type": "sales",
            "history_ids": list(dict.fromkeys(req.history_ids)),
            "format": "drive",
            "lang": req.lang,
        },
        workspace_client_id=int(ws),
    )
    if not job_id:
        raise PosError("sales.export_failed", 500, detail="enqueue_failed")
    return ok({"job_id": job_id, "status": "queued"})


@router.get("/export/{job_id}")
async def api_sales_export_status(job_id: str, request: Request):
    tid, uid = require_perm_tid(request, "sales.doc.view")
    from services.recon_jobs import store as jobs

    job = jobs.get(job_id, user_id=str(uid), tenant_id=str(tid))
    if not job:
        raise PosError("sales.export_not_found", 404, detail="job_not_found")
    progress = job.get("progress") or {}
    return ok(
        {
            "status": job.get("status"),
            "done_n": progress.get("done_n", 0),
            "skip_n": progress.get("skip_n", 0),
            "total": progress.get("total", 0),
            "drive_url": progress.get("drive_url", ""),
            "sheet_url": "",
            "error": job.get("error_code"),
        }
    )
