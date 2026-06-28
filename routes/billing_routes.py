# -*- coding: utf-8 -*-
"""
Pearnly · Billing 路由聚合(阶段5 Task5.1 抽出 · R21 再拆 · 2026-05-29)

14 路由按域拆为 billing_credits_routes(余额/公司/用量·只读)+ billing_topup_routes
(充值申请/凭证/审核·台账)· 此处 include_router 聚合 → 对外仍是单一 `router`,
app.py 的 `app.include_router(billing_router)` 不变。计费逻辑在 services/billing/*。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

# 契约保留:billing_routes._require_super_admin is route_helpers._require_super_admin
from core.route_helpers import _require_super_admin  # noqa: F401
from routes.billing_credits_routes import router as _credits_router
from routes.billing_records_routes import router as _records_router
from routes.billing_subscription_routes import router as _subscription_router
from routes.billing_topup_routes import router as _topup_router

logger = logging.getLogger("mr-pilot")

router = APIRouter()
router.include_router(_credits_router)
router.include_router(_topup_router)
router.include_router(_subscription_router)
router.include_router(_records_router)
