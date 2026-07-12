# -*- coding: utf-8 -*-
"""模块视图 + 注册 onboarding 路由(平台业态套餐 · docs/platform-onboarding/03)。

薄层:鉴权 + 信封;读写 SQL/逻辑在 services/modules/{store,presets}.py。主程序导航据此显隐。
租户隔离走 db.get_cursor_rls。读(GET)任意已登录主体可调(导航需要);onboarding 走
settings.modules.manage(owner/admin)。

按域名分功能收口(Zihao 2026-07-12 拍板):客户侧业态自选/模块自选全部下架——
onboarding 锁死只收 firm(新注册向导静默套用的唯一合法值);逐模块 toggle 路由已删。
非 firm 预设(pos_only 等)只走运营侧(Earn 超管开通,直调 presets.apply_preset)。
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
    """新注册向导静默套用 firm 预设(owner/admin)。业态自选已下架,非 firm 一律拒——
    防老前端/脚本把租户改回旧业态标签,与「域名分功能」的壳判据打架。"""
    tid, _uid = require_perm_pos_tid(request, "settings.modules.manage")
    if req.business_type != "firm":
        raise PosError("platform.business_type_locked", 403, detail=req.business_type)
    with db.get_cursor_rls(tid, commit=True) as cur:
        presets.apply_preset(cur, tenant_id=tid, business_type=req.business_type)
        return ok(_modules_view(cur, tid))
