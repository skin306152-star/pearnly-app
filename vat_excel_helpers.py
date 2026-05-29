# -*- coding: utf-8 -*-
"""vat_excel 路由共享小工具(REFACTOR-WA-B1 · R22 从 vat_excel_routes 抽 · 0 逻辑改)
_require_user / _user_key / _tenant_user · 供 vat_excel_routes 与 vat_excel_tasks_routes 共用 · 避循环依赖。
"""

from typing import Optional

from fastapi import HTTPException, Request

from auth import get_current_user_from_request


def _require_user(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(401, "未登录")
    return user


def _user_key(user) -> Optional[str]:
    return (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip() or None


def _tenant_user(user):
    return (user.get("tenant_id"), user["id"])
