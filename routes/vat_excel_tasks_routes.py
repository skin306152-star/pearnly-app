# -*- coding: utf-8 -*-
"""vat_excel 路由 · 任务列表/详情/清理/删除(只读+删·非扣费)(REFACTOR-WA-B1 · R22 拆 · 0 逻辑改)
GET /tasks · GET /tasks/{id} · DELETE /tasks/clear_old(必先于 {id})· DELETE /tasks/{id}。
vat_excel_routes 顶部 include_router 聚合(承父 prefix /api/vat_excel)· app 单一 include 不变。"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from core import db
from core import workspace_context as wc
from services.vat.vat_excel_helpers import _require_user, _tenant_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ════ 任务列表 ════
@router.get("/tasks")
async def list_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
):
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)
    _ws = wc.active_workspace_for_request(request, tenant_id)
    result = db.list_vat_recon_tasks(
        tenant_id=tenant_id,
        user_id=str(user_id),
        page=page,
        page_size=page_size,
        status=status,
        period=period,
        workspace_client_id=_ws,
    )
    kpi = db.get_vat_recon_tasks_kpi(
        tenant_id=tenant_id, user_id=str(user_id), workspace_client_id=_ws
    )
    # UUID/datetime 序列化
    for row in result["rows"]:
        for k in ("id", "tenant_id", "user_id"):
            if row.get(k):
                row[k] = str(row[k])
        for k in ("created_at", "updated_at"):
            if row.get(k):
                row[k] = row[k].isoformat()
        if row.get("mismatch_amount") is not None:
            row["mismatch_amount"] = float(row["mismatch_amount"])
        if row.get("elapsed_seconds") is not None:
            row["elapsed_seconds"] = float(row["elapsed_seconds"])
    return {**result, "kpi": kpi}


# ════ 任务详情(含 raw_data_json) ════
@router.get("/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)
    task = db.get_vat_recon_task(
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=str(user_id),
        workspace_client_id=wc.active_workspace_for_request(request, tenant_id),
    )
    if not task:
        raise HTTPException(404, "任务不存在")
    # 序列化
    for k in ("id", "tenant_id", "user_id"):
        if task.get(k):
            task[k] = str(task[k])
    for k in ("created_at", "updated_at"):
        if task.get(k):
            task[k] = task[k].isoformat()
    if task.get("mismatch_amount") is not None:
        task["mismatch_amount"] = float(task["mismatch_amount"])
    if task.get("elapsed_seconds") is not None:
        task["elapsed_seconds"] = float(task["elapsed_seconds"])
    return task


# ════ 批量清理旧任务 ════
@router.delete("/tasks/clear_old")
async def clear_old_tasks(
    request: Request,
    days: int = Query(7, ge=1, le=365),
):
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)
    deleted_count, excel_paths = db.delete_vat_recon_tasks_older_than(
        days=days, tenant_id=tenant_id, user_id=str(user_id)
    )
    for p in excel_paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception as e:
            logger.warning(f"[vex] clear_old: delete file failed: {e}")
    return {"ok": True, "deleted": deleted_count}


# ════ 任务删除 ════
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, request: Request):
    user = _require_user(request)
    tenant_id, user_id = _tenant_user(user)
    excel_path = db.delete_vat_recon_task(
        task_id=task_id, tenant_id=tenant_id, user_id=str(user_id)
    )
    if excel_path is None:
        raise HTTPException(404, "任务不存在")
    # 删文件(忽略失败)
    try:
        if excel_path and os.path.exists(excel_path):
            os.remove(excel_path)
    except Exception as e:
        logger.warning(f"[vex] delete excel file failed: {e}")
    return {"ok": True}
