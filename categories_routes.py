# -*- coding: utf-8 -*-
"""
Pearnly · 分类(Categories)API 路由模块(REFACTOR-B1 · 2026-05-25 抽出)

单路由 · 列出当前 tenant/user 用过的 category(前端 datalist 自动补全 + 统计)。
从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 1 个 API:
  GET /api/categories       · 列出用过的 category + 供应商映射数

依赖:
  - db.list_used_categories / count_supplier_mappings
  - auth.get_current_user_from_request
  - route_helpers._tid(取 user tenant_id)
"""

from __future__ import annotations

from fastapi import APIRouter, Request

import db
from auth import get_current_user_from_request
from route_helpers import _tid

router = APIRouter()


@router.get("/api/categories")
async def api_list_used_categories(request: Request):
    """列出当前 tenant/user 用过的所有 category(给前端 datalist 自动补全 + 统计)"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    cats = db.list_used_categories(user_id=str(user["id"]), tenant_id=tid, limit=30)
    n_mappings = db.count_supplier_mappings(user_id=str(user["id"]), tenant_id=tid)
    return {"categories": cats, "supplier_count": n_mappings}
