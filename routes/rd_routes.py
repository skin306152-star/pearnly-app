# -*- coding: utf-8 -*-
"""
Pearnly · 泰国 RD 税务 API 路由模块(REFACTOR-B1 · 2026-05-25 抽出)

第 5.1 批 · 泰国 RD 税务 API(校验 + 同步)。从 app.py 整片搬过来 ·
纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 4 个 API:
  POST /api/rd/verify       · 校验税号是否真实存在(TIN Service)
  POST /api/rd/lookup       · 查公司全信息(VAT Service · 17 字段)
  POST /api/v1/rd/verify    · v1 别名 → rd_verify
  POST /api/v1/rd/lookup    · v1 别名 → rd_lookup

依赖:
  - db.get_rd_daily_usage / increment_rd_daily_usage
  - auth.get_current_user_from_request
  - route_helpers._plan_permissions(权限闸)
  - rd_api.verify_tin / lookup_vat(函数内懒 import)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _plan_permissions

router = APIRouter()


class RdQueryRequest(BaseModel):
    tax_id: str = Field(..., description="13 位税号")
    branch: Optional[int] = Field(0, description="分支号 · 默认 0(总部)")


def _check_rd_access(user: dict):
    """v0.8 · 所有 plan 可用 · Free 有日限"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_verify_tax"):
        raise HTTPException(403, detail="rd.upgrade_required")

    daily_limit = p.get("rd_daily_limit")
    if daily_limit is None:
        return  # 无限

    # 当日用量(从 Redis/内存都没有,直接查 DB 简表)
    used = db.get_rd_daily_usage(str(user["id"]))
    if used >= daily_limit:
        raise HTTPException(
            429,
            detail={
                "code": "rd.daily_limit_reached",
                "limit": daily_limit,
                "used": used,
            },
        )


@router.post("/api/rd/verify")
async def rd_verify(req: RdQueryRequest, request: Request):
    """校验税号是否真实存在(快 · TIN Service)"""
    user = get_current_user_from_request(request)
    _check_rd_access(user)
    from services.rd.rd_api import verify_tin

    result = verify_tin(req.tax_id)
    # v0.8.1 · 只计成功的查询,失败不算日限
    if (result or {}).get("valid"):
        db.increment_rd_daily_usage(str(user["id"]))
    return result


@router.post("/api/rd/lookup")
async def rd_lookup(req: RdQueryRequest, request: Request):
    """查公司全信息(VAT Service · 17 字段 · 用于一键同步)"""
    user = get_current_user_from_request(request)
    _check_rd_access(user)
    from services.rd.rd_api import lookup_vat

    result = lookup_vat(req.tax_id, req.branch or 0)
    # v0.8.1 · 只计查到公司信息的请求
    if (result or {}).get("found") or (result or {}).get("name"):
        db.increment_rd_daily_usage(str(user["id"]))
    return result


# v1 别名
@router.post("/api/v1/rd/verify")
async def v1_rd_verify(req: RdQueryRequest, request: Request):
    return await rd_verify(req, request)


@router.post("/api/v1/rd/lookup")
async def v1_rd_lookup(req: RdQueryRequest, request: Request):
    return await rd_lookup(req, request)
