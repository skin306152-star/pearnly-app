# -*- coding: utf-8 -*-
"""ERP 路由共享准入闸(REFACTOR-WA-B1 · 2026-05-29 R18 从 erp_routes 抽出 · 0 逻辑改)

_check_push_access:endpoints / connection / push-log 三个 ERP 路由组共用的 plan 准入校验 ·
复用 route_helpers._plan_permissions(单一来源)。独立模块 · 避免三路由模块互相循环依赖。
"""

from fastapi import HTTPException

from core.route_helpers import _plan_permissions


def _check_push_access(user: dict):
    """所有 plan 都可用 ERP 推送(v0.8)· Free 有数量限制,无自动推"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_push_erp"):
        raise HTTPException(403, detail="erp.upgrade_required")
