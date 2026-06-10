# -*- coding: utf-8 -*-
"""设置页「业务/模块」管理路由(POS 项目 · C3 · docs/pos/02 §2.2 / 04 §2)。

薄层:require_perm_pos_tid(模块管理是老板动作,收银员不可调)→ get_cursor_rls → store/onboarding →
POS 信封。模块关 = 隐藏入口,不删任何数据(tenant_modules.enabled=false;库存/小票行保留)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, ok, require_workspace
from services.authz.deps import require_perm_pos_tid
from services.modules import store as modules_store
from services.pos import onboarding as onboarding_svc

router = APIRouter(prefix="/api/pos/admin", tags=["pos-modules"])


@router.get("/modules")
async def api_get_modules(request: Request):
    """全模块开关视图(老板设置页用 · 含默认回落 + config)。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    with db.get_cursor_rls(tid) as cur:
        modules = modules_store.get_modules(cur, tenant_id=tid)
    return ok({"modules": modules})


class SetModuleRequest(BaseModel):
    module_key: str = Field(..., min_length=1, max_length=40)
    enabled: bool
    config: Optional[dict] = None


@router.put("/modules")
async def api_set_module(req: SetModuleRequest, request: Request):
    """开/关单模块(关=隐藏不删数据)。未知 module_key → pos.line_invalid(422)。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        try:
            updated = modules_store.set_module(
                cur,
                tenant_id=tid,
                module_key=req.module_key,
                enabled=req.enabled,
                config=req.config,
            )
        except ValueError as e:
            raise PosError("pos.line_invalid", 422, detail=str(e)) from e
    return ok({"module": updated})


@router.get("/onboarding-state")
async def api_onboarding_state(request: Request, workspace_client_id: int = Query(...)):
    """该账套是否已开通收银 + 当前业态(屏8 据此判断,避免重复开通)。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    with db.get_cursor_rls(tid) as cur:
        require_workspace(cur, tid, workspace_client_id)
        state = onboarding_svc.get_state(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id
        )
    return ok(state)


@router.get("/business-presets")
async def api_business_presets(request: Request):
    """业态预设(业态 → 能力块清单)· 给开通向导渲染选项。"""
    require_perm_pos_tid(request, "settings.modules.manage")
    return ok({"presets": onboarding_svc.BUSINESS_PRESETS})
