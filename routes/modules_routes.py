# -*- coding: utf-8 -*-
"""模块开关 + 业态 onboarding 路由(POS PO-A1 / 平台业态套餐 · docs/platform-onboarding/03)。

薄层:鉴权 + 信封;读写 SQL/逻辑在 services/modules/{store,presets}.py。主程序导航据此显隐。
租户隔离走 db.get_cursor_rls。读(GET)任意已登录主体可调(导航需要);写(onboarding/toggle)
走 settings.modules.manage(owner/admin · 收银员/会计/录入不可改模块配置)。
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, ok, require_tenant
from services.authz.deps import require_perm_pos_tid
from services.modules import presets, store

router = APIRouter(prefix="/api/me", tags=["modules"])


class OnboardingRequest(BaseModel):
    business_type: str = Field(..., min_length=1, max_length=40)


class ModuleToggleRequest(BaseModel):
    enabled: bool


def _modules_view(cur, tenant_id: str) -> dict:
    """GET 与写接口共用的全模块态视图(含业态 + 可开关全集)。"""
    return {
        "modules": store.get_modules(cur, tenant_id=tenant_id),
        "business_type": store.get_business_type(cur, tenant_id=tenant_id),
        "gateable": list(store.KNOWN_MODULES),
        "needs_onboarding": store.needs_onboarding(cur, tenant_id=tenant_id),
    }


@router.get("/modules")
async def api_get_modules(request: Request):
    """当前租户开了哪些模块(含默认回落)+ 业态。前端导航/路由按此显隐。"""
    tid, _uid = require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        return ok(_modules_view(cur, tid))


@router.put("/onboarding")
async def api_onboarding(req: OnboardingRequest, request: Request):
    """注册选业态 / 设置切换业态:应用预设翻 7 模块开关 + 记录业态(owner/admin)。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    if not presets.is_known(req.business_type):
        raise PosError("platform.unknown_business_type", 400, detail=req.business_type)
    with db.get_cursor_rls(tid, commit=True) as cur:
        presets.apply_preset(cur, tenant_id=tid, business_type=req.business_type)
        return ok(_modules_view(cur, tid))


@router.put("/modules/{module_key}")
async def api_toggle_module(module_key: str, req: ModuleToggleRequest, request: Request):
    """设置页逐个开关模块(owner/admin)。关=隐藏不删数据(只翻 enabled)。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        try:
            row = store.set_module(cur, tenant_id=tid, module_key=module_key, enabled=req.enabled)
        except ValueError as exc:
            raise PosError("platform.unknown_module", 404, detail=module_key) from exc
        return ok(row)
