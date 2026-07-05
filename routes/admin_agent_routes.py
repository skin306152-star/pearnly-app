# -*- coding: utf-8 -*-
"""对话 Agent 健康/漏斗超管路由(Earn 后台「Agent 助手」页 · 观测 W0)。

只读聚合,不碰任何对话/扣费逻辑:轮结局与降级率来自 agent_turn_logs
(services/agent/turn_log),获客漏斗来自 line_funnel_events + line_bindings +
agent_turn_logs(services/line_binding/line_funnel)。_require_super_admin 守门。

覆盖:
  GET /api/admin/agent/overview · 健康(kind/意图/降级分布+crash率)+ 漏斗四级
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request

from core.route_helpers import _require_super_admin
from services.agent import turn_log
from services.line_binding import line_funnel

logger = logging.getLogger("mr-pilot")

router = APIRouter()


@router.get("/api/admin/agent/overview")
async def admin_agent_overview(
    request: Request,
    hours: int = Query(24, ge=1, le=720),
    days: int = Query(7, ge=1, le=90),
):
    _require_super_admin(request)
    return {
        "health": turn_log.stats(hours=hours),
        "funnel": line_funnel.funnel_stats(days=days),
    }
