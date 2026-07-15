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
from core.pos_api import PosError, ok, require_workspace_access
from services.authz.deps import require_perm_pos_tid
from services.pos import onboarding as onboarding_svc

router = APIRouter(prefix="/api/pos/admin", tags=["pos-modules"])


# ── 自助模块管理已封死(Phase3 · 各是各的):功能跟登录入口走,不再逐模块自选。
# PUT 是「自助逐模块 toggle」影子活体(与「入口定功能」直接冲突);GET 读侧与 business-presets
# 孤悬端点均零前端消费者(grep 为证),一并封。保留路由壳返 403,不动 app 注册。开通向导只走
# onboarding-state(读)+ 运营侧 presets.apply_preset(写),不经这三个端点。


@router.get("/modules")
async def api_get_modules(request: Request):
    """已封死:自助模块开关读侧废弃(零前端消费者)。"""
    raise PosError("pos.forbidden", 403)


class SetModuleRequest(BaseModel):
    module_key: str = Field(..., min_length=1, max_length=40)
    enabled: bool
    config: Optional[dict] = None


@router.put("/modules")
async def api_set_module(req: SetModuleRequest, request: Request):
    """已封死:自助逐模块 toggle 影子活体(与「入口定功能」冲突,禁自助开通)。"""
    raise PosError("pos.forbidden", 403)


@router.get("/onboarding-state")
async def api_onboarding_state(request: Request, workspace_client_id: int = Query(...)):
    """该账套是否已开通收银 + 当前业态(屏8 据此判断,避免重复开通)。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    with db.get_cursor_rls(tid) as cur:
        require_workspace_access(cur, request, tid, workspace_client_id)
        state = onboarding_svc.get_state(
            cur, tenant_id=tid, workspace_client_id=workspace_client_id
        )
    return ok(state)


@router.get("/business-presets")
async def api_business_presets(request: Request):
    """已封死:业态预设孤悬端点(零前端消费者)。"""
    raise PosError("pos.forbidden", 403)
