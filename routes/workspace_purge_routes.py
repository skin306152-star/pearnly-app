# -*- coding: utf-8 -*-
"""按账套主体清空数据 · HTTP 端点(NDJSON 流式回进度)。

为什么流式:清一个账套要扫 70+ 张表,一个 JSON 等到最后才回,前端只能转圈假装有进度。
逐表吐一行 NDJSON,前端读一行画一格 —— 显示的是真到了第几张表,不是定时器编的。

事务:整个清除在一个事务里跑完才 commit。客户端中途断开 → 事务回滚 → 数据原样,
不会留个删一半的账套。文件在 commit 之后才删(先删文件再回滚就找不回来了)。
"""

from __future__ import annotations

import json
import logging
from typing import Iterator, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from core import db
from core.route_helpers import _tid, _log_op
from services.authz.deps import require_perm
from services.workspace import purge as purge_svc
from services.workspace import purge_files as files_svc

logger = logging.getLogger(__name__)
router = APIRouter()


def _assert_owns(cur, ws_id: int, tenant_id: str) -> str:
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (ws_id, tenant_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="workspace.not_found")
    return str(row["name"])


def _stream(tenant_id: str, ws_id: int, period: Optional[str]) -> Iterator[bytes]:
    targets: dict = {}
    leftover: list[str] = []
    leftover_detail: list = []
    deleted_total = 0
    with db.get_cursor_rls(tenant_id=tenant_id, workspace_client_id=ws_id, commit=True) as cur:
        _assert_owns(cur, ws_id, tenant_id)
        # 文件位置必须在删表之前收 —— 按期清时更是:票据与账期的联系只存在于 work_order_items,
        # 子行一删就再也认不出哪些文件属于这一期。
        scope = purge_svc.period_scope(cur, ws_id, period) if period else None
        targets = files_svc.collect(cur, tenant_id=tenant_id, ws_id=ws_id, scope=scope)
        for evt in purge_svc.purge(cur, tenant_id=tenant_id, ws_id=ws_id, period=period):
            if evt.get("step") == "finished":
                leftover = list(evt.get("leftover") or [])
                leftover_detail = list(evt.get("leftover_detail") or [])
                deleted_total = int(evt.get("deleted_total") or 0)
                continue
            yield (json.dumps(evt, ensure_ascii=False) + "\n").encode()
    # 事务已提交,再动盘上文件
    files_removed = files_svc.purge(targets)
    # 有残留 = 这次清除【没成功】,按 error 记 —— 上一版记 info,线上漏删 1648 行子数据
    # 时日志里毫无异样,是用户点开界面才发现的。
    msg = (
        f"[purge] ws={ws_id} tenant={tenant_id} rows={deleted_total} "
        f"files={files_removed} leftover={leftover_detail}"
    )
    logger.error(msg) if leftover else logger.info(msg)
    yield (
        json.dumps(
            {
                "step": "finished",
                "deleted_total": deleted_total,
                "files_removed": files_removed,
                "leftover": leftover,
                "leftover_detail": leftover_detail,
                "ok": not leftover,
            },
            ensure_ascii=False,
        )
        + "\n"
    ).encode()


@router.get("/api/workspace/clients/{workspace_client_id}/purge-periods")
async def list_purge_periods(workspace_client_id: int, request: Request):
    """该账套下真有数据的账期(供清除弹窗的账期下拉)。只列真有的,不摆空选项。"""
    user = require_perm(request, "settings.workspace.manage")
    tenant_id = _tid(user)
    if not tenant_id:
        raise HTTPException(403, detail="authz.forbidden")
    with db.get_cursor_rls(tenant_id=tenant_id, workspace_client_id=workspace_client_id) as cur:
        _assert_owns(cur, workspace_client_id, tenant_id)
        return {"periods": purge_svc.periods_with_data(cur, workspace_client_id)}


@router.post("/api/workspace/clients/{workspace_client_id}/purge")
async def purge_workspace_client_data(
    workspace_client_id: int,
    request: Request,
    period: Optional[str] = Query(None, description="留空=整个账套;给值=只清这一期"),
):
    """清空账套数据。仅老板/超管。不可撤销。

    留空 period = 整个账套(主体行只留名称与税号)。
    给了 period = 只清这一期:该期工单及其名下一切 + 挂上去的票据 + 带期表按期过滤;
    主数据与别的账期不动。越权或不存在一律 404(不泄漏存在性,同本域既有端点口径)。
    """
    user = require_perm(request, "settings.workspace.manage")
    tenant_id = _tid(user)
    if not tenant_id:
        raise HTTPException(403, detail="authz.forbidden")

    with db.get_cursor_rls(tenant_id=tenant_id) as cur:
        name = _assert_owns(cur, workspace_client_id, tenant_id)
    _log_op(
        request,
        user,
        "workspace.client.purge",
        target_type="workspace_client",
        target_id=str(workspace_client_id),
        target_name=name,
        details={"irreversible": True, "period": period or "ALL"},
    )
    return StreamingResponse(
        _stream(tenant_id, workspace_client_id, period),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
