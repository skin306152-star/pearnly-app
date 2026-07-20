# -*- coding: utf-8 -*-
"""
Pearnly · 识别记录归属 API(2026-07-20 从 history_routes 拆出 · 纯搬家)

把一条识别记录挂到套账(workspace_client)或客户(client)。与 history 的增删改查是两件事:
那边管记录本身,这边管它归谁——所以独立成模块。URL/method/权限/返回结构/错误码 0 改。

router 由 history_routes 用 include_router 挂进同一棵树(app.py 零改动),
故本模块不得 import history_routes,否则成环。共用的 _check_history_access 已上移
core.route_helpers。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _check_history_access, _tid

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class AssignClientRequest(BaseModel):
    client_id: Optional[int] = None  # None 表示移除归属


class AssignWorkspaceRequest(BaseModel):
    workspace_client_id: int = Field(..., description="目标套账 id(必须指定,不许清空归属)")


@router.post("/api/history/{history_id}/assign_workspace")
async def api_assign_workspace(history_id: str, req: AssignWorkspaceRequest, request: Request):
    """把识别记录改归属到另一个套账(税号路由再准也有例外:代付/税号印错的票)。

    只许挪到本租户的套账;不提供清空(NULL 会让 Express 方向判定失锚,见 persist 注释)。
    """
    user = get_current_user_from_request(request)
    _check_history_access(user)
    _tenant = _tid(user)
    if not _tenant:
        raise HTTPException(400, detail="workspace.required")
    from core.workspace_context import assert_workspace_in_tenant

    with db.get_cursor() as cur:
        assert_workspace_in_tenant(
            cur, tenant_id=_tenant, workspace_client_id=int(req.workspace_client_id)
        )
    ok = db.update_history_workspace_client_id(
        history_id, int(req.workspace_client_id), str(user["id"]), tenant_id=_tenant
    )
    if not ok:
        raise HTTPException(400, detail="history.assign_workspace_failed")
    return {"ok": True, "workspace_client_id": int(req.workspace_client_id)}


@router.post("/api/history/{history_id}/assign_client")
async def api_assign_client(history_id: str, req: AssignClientRequest, request: Request):
    """把发票归属到客户 · client_id=null 表示取消归属"""
    user = get_current_user_from_request(request)
    # v118.28.1 · 员工:校验 client_id 在 visible_ids 内 · 否则 403(防员工把发票归到他不能看的客户)
    if req.client_id is not None:
        visible = db.get_visible_client_ids_for_user(user)
        if visible is not None and int(req.client_id) not in set(visible):
            raise HTTPException(403, detail="client.no_access")
    ok = db.assign_invoice_to_client(
        str(user["id"]), history_id, req.client_id, tenant_id=_tid(user)
    )
    if not ok:
        raise HTTPException(400, detail="client.assign_failed")

    # 批 1 改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) · 用户手动 assign 时 ·
    # 把 buyer_name + buyer_tax → client_id 的关系学进 buyer_to_client_memory ·
    # 下次 OCR 出同 buyer 就 auto-resolve · 不用每次手动选.
    if req.client_id is not None:
        try:
            h = db.get_ocr_history_detail(
                str(user["id"]),
                history_id,
                tenant_id=_tid(user),
            )
            if h:
                _pages = h.get("pages") or []
                _primary = next(
                    (
                        p
                        for p in _pages
                        if isinstance(p, dict)
                        and not p.get("is_duplicate")
                        and not p.get("is_copy")
                    ),
                    _pages[0] if _pages else {},
                )
                _f = (_primary or {}).get("fields") or {}
                _buyer_name = _f.get("buyer_name") or ""
                _buyer_tax = _f.get("buyer_tax") or ""
                if _buyer_name:
                    db.learn_buyer_to_client(
                        _buyer_name,
                        _buyer_tax,
                        int(req.client_id),
                        str(user["id"]),
                        tenant_id=_tid(user),
                    )
                    logger.info(
                        "[assign_client] learned buyer→client: %r → %s",
                        _buyer_name[:40],
                        req.client_id,
                    )
        except Exception as e:
            logger.warning(f"learn buyer→client failed (history={history_id[:8]}): {e}")

    return {"ok": True}
