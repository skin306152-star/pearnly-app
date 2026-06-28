# -*- coding: utf-8 -*-
"""Pearnly · 订阅套餐路由 · GET 当前订阅+目录 / POST 订阅 / POST 取消。

billing_routes 顶部 include_router 聚合 · app.py 单一 include 不变。
计费/订阅逻辑在 services/billing/subscription.py · 本模块仅 HTTP handler。
订阅/取消涉钱(从余额扣月费)→ 仅老板(owner)可操作;GET 任意登录用户可看。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core import db
from core.auth import get_current_user_from_request
from services.authz.deps import is_owner_role

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class SubscribeBody(BaseModel):
    plan_code: str


def _tenant_balance(tenant_id) -> float:
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            cur.execute(
                "SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s::uuid",
                (str(tenant_id),),
            )
            row = cur.fetchone()
            return float(row["balance_thb"]) if row else 0.0
    except Exception as e:
        logger.warning(f"_tenant_balance error tenant={tenant_id}: {e}")
        return 0.0


@router.get("/api/me/subscription")
async def get_my_subscription(request: Request, response: Response):
    """当前订阅 + 套餐目录 + 余额(余额实时 · 禁缓存)。"""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    user = get_current_user_from_request(request)
    tenant_id = user.get("tenant_id")
    is_owner = is_owner_role(request, user)
    out = {
        "has_tenant": bool(tenant_id),
        "is_owner": is_owner,
        "is_billing_exempt": bool(user.get("is_billing_exempt", False)),
        "plans": db.subscription_catalog(),
        "subscription": None,
        "balance_thb": 0.0,
    }
    if tenant_id:
        out["subscription"] = db.get_active_subscription(tenant_id)
        out["balance_thb"] = _tenant_balance(tenant_id)
    return out


@router.post("/api/subscription/subscribe")
async def subscribe(body: SubscribeBody, request: Request, response: Response):
    """订阅/换套餐 · 从余额扣月费(仅老板)。余额不足返 402。"""
    response.headers["Cache-Control"] = "no-store"
    user = get_current_user_from_request(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="no_tenant")
    if not is_owner_role(request, user):
        raise HTTPException(status_code=403, detail="owner_only")
    if not db.subscription_plan_spec(body.plan_code):
        raise HTTPException(status_code=400, detail="unknown_plan")

    result = db.subscription_subscribe(user.get("id"), tenant_id, body.plan_code)
    if not result.get("ok"):
        if result.get("error") == "insufficient_balance":
            raise HTTPException(status_code=402, detail=result)
        raise HTTPException(status_code=400, detail=result.get("error", "subscribe_failed"))
    return result


@router.post("/api/subscription/cancel")
async def cancel(request: Request, response: Response):
    """取消订阅(当前周期额度用到到期 · 不再续 · 仅老板)。"""
    response.headers["Cache-Control"] = "no-store"
    user = get_current_user_from_request(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="no_tenant")
    if not is_owner_role(request, user):
        raise HTTPException(status_code=403, detail="owner_only")
    result = db.subscription_cancel(tenant_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "cancel_failed"))
    return result
