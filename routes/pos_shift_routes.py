# -*- coding: utf-8 -*-
"""POS 班次开/交班路由(PC-3 · 从 pos_sales_routes 拆出 · docs/pos/04 §5)。

薄层:POS 信封(鉴权/模块闸/账套归属/单事务)。连号(shift.shift_seq)与对账公式在
services/pos/shift;审计(pos.shift.opened/closed)挂 pos_write 的 after_commit 钩子——commit 后
独立写、失败不回滚交班(shift_audit best-effort · 收银员令牌避 FK 血泪见该模块)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db, pos_api
from core.pos_api import PosError, assert_module_enabled, ok, require_workspace_access
from services.pos import shift as shift_svc
from services.pos import shift_audit

router = APIRouter(prefix="/api/pos", tags=["pos-shift"])


class OpenShiftRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    terminal_id: Optional[int] = None  # 缺省 → 服务端回落账套默认终端(单终端门店)
    opening_float: float = Field(0, ge=0)


class CloseShiftRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    counted_cash: float = Field(..., ge=0)


@router.post("/shifts/open")
async def api_open_shift(req: OpenShiftRequest, request: Request):
    def _fn(cur, tid, ws, user):
        cashier_id = user.get("cashier_id")
        if not cashier_id:
            raise PosError("pos.forbidden", 403)  # 仅收银员(PIN 登录)可开班
        return {
            "shift": shift_svc.open_shift(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                terminal_id=req.terminal_id,
                cashier_id=cashier_id,
                opening_float=req.opening_float,
            )
        }

    return pos_api.pos_write(
        request,
        ws_override=req.workspace_client_id,
        write_fn=_fn,
        permission="pos.shift.operate",
        after_commit=shift_audit.after_open,
    )


@router.get("/shifts/current")
async def api_current_shift(request: Request, workspace_client_id: Optional[int] = Query(None)):
    """本收银台当前未结班次 + 汇总(交班屏直查,不依赖前端内存 → 刷新/换人后仍能交班)。
    无班次 → data:null(屏显诚实空态)。"""
    user, tid = pos_api.subject(request, "pos.shift.operate")
    ws = pos_api.resolve_ws(user, workspace_client_id)
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace_access(cur, request, tid, ws)
        return ok(shift_svc.current_shift(cur, tenant_id=tid, workspace_client_id=ws))


@router.post("/shifts/{shift_id}/close")
async def api_close_shift(shift_id: str, req: CloseShiftRequest, request: Request):
    def _fn(cur, tid, ws, user):
        return shift_svc.close_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            shift_id=shift_id,
            counted_cash=req.counted_cash,
        )

    return pos_api.pos_write(
        request,
        ws_override=req.workspace_client_id,
        write_fn=_fn,
        permission="pos.shift.operate",
        after_commit=shift_audit.after_close,
    )
