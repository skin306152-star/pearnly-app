"""
services/ocr/recognize/autopush.py · OCR 识别·ERP 自动推送分发

从 app.py ocr_recognize 抽出(REFACTOR-WB-app · 2026-06-01)。
已归属(有 client_id)的票推所有自动推送端点;未归属(现金/散客)的票只推 Express
—— Express 销项 mapper 对现金买方有兜底(挂固定现金客户档),走的是与手动推送同一条链路,
故能落账;MR.ERP 无客户档会硬失败 ERR_NO_CLIENT,不把未归属票发给它。
ERP_SELLER_ROUTING 开启时已归属票走卖方账套分拣,否则每张推所有自动推送端点。
返回 auto_pushed(布尔·进响应)。
"""

import logging

from core import db
from core.route_helpers import _plan_permissions, _tid
from services.erp.auto_push import (
    _auto_push_history,
    _auto_push_smart_routed,
    _erp_seller_routing_enabled,
)

logger = logging.getLogger("mr-pilot")


def _is_express(endpoint):
    return (endpoint.get("adapter") or "").strip().lower() == "express"


def dispatch_auto_push(*, history_ids, plan, user):
    """OCR 识别后异步入队自动推送(不阻塞返回)。"""
    if not (history_ids and _plan_permissions(plan).get("can_auto_push_erp")):
        return False
    try:
        user_id = str(user["id"])
        tid = _tid(user)
        auto_eps = db.list_erp_endpoints(user_id, auto_push_only=True)
        if not auto_eps:
            return False
        express_eps = [ep for ep in auto_eps if _is_express(ep)]

        # 已归属票推所有端点;未归属(现金/散客)票只推 Express。
        assigned_ids, express_only_ids = [], []
        for hid in history_ids:
            h = db.get_ocr_history_detail(user_id, hid, tenant_id=tid)
            if h and h.get("client_id"):
                assigned_ids.append(hid)
            elif express_eps:
                express_only_ids.append(hid)
            else:
                logger.info("[auto-push] skip history=%s · 未归属且无 Express 端点", hid[:8])

        if not (assigned_ids or express_only_ids):
            return False

        import asyncio

        if assigned_ids:
            if _erp_seller_routing_enabled(user_id):
                asyncio.create_task(_auto_push_smart_routed(user_id, assigned_ids, tid, auto_eps))
            else:
                for hid in assigned_ids:
                    asyncio.create_task(_auto_push_history(user_id, hid, auto_eps, tenant_id=tid))
        for hid in express_only_ids:
            asyncio.create_task(_auto_push_history(user_id, hid, express_eps, tenant_id=tid))

        logger.info(
            "自动推送已入队 · 已归属 %d × %d 端点 · 现金/散客 %d × %d Express",
            len(assigned_ids),
            len(auto_eps),
            len(express_only_ids),
            len(express_eps),
        )
        return True
    except Exception as e:
        logger.warning("自动推送入队失败(不影响识别): %s", e)
        return False
