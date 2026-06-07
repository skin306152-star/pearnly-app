# -*- coding: utf-8 -*-
"""模块开关路由(POS 项目 · PO-A1 · docs/pos/04 §2)。

薄层:鉴权 + 信封;读写 SQL 在 services/modules/store.py。主程序导航据此显隐
(库存/POS/切收银台 按开关出现)。租户隔离走 db.get_cursor_rls。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from core import db
from core.pos_api import ok, require_tenant
from services.modules import store

router = APIRouter(prefix="/api/me", tags=["modules"])


@router.get("/modules")
async def api_get_modules(request: Request):
    """当前租户开了哪些模块(含默认回落)。前端导航/路由按此显隐。"""
    tid, _uid = require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        modules = store.get_modules(cur, tenant_id=tid)
    return ok({"modules": modules})
