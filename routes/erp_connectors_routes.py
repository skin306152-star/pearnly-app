# -*- coding: utf-8 -*-
"""
Pearnly · ERP 连接器聚合路由

GET /api/erp/connectors/status — 统一返回当前用户/租户所有「已配置的 ERP 连接器」
(erp_endpoints 表里的 webhook / mrerp / flowaccount 等 adapter)· 抽屉「1 个推送按钮」用。

依赖:db.list_erp_endpoints · auth.get_current_user_from_request。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Request

from core import db
from core.auth import get_current_user_from_request

logger = logging.getLogger("mr-pilot")

router = APIRouter()


@router.get("/api/erp/connectors/status")
async def erp_connectors_status(request: Request):
    """统一返回当前用户/租户所有「已配置的 ERP 连接器」(erp_endpoints 表)·
    抽屉「1 个推送按钮」用。所有连接器均走 POST /api/erp/push(endpoint_id 必填)。"""
    user = get_current_user_from_request(request)
    connectors: List[Dict[str, Any]] = []

    try:
        endpoints = db.list_erp_endpoints(str(user["id"])) or []
        for ep in endpoints:
            if not ep.get("enabled", True):
                continue
            adapter = ep.get("adapter") or "webhook"
            # DMS guard (DMS-UI-005 · 2026-06-01) · mrerp_dms is the car-sales
            # ID-card→booking adapter, NEVER an invoice push target. Keep it out
            # of the unified push connector list so the history-drawer split
            # button can't offer "push invoice to DMS" (mirrors ocr-push.js's
            # filter + push_to_endpoint's ERR_DMS_NOT_INVOICE_ENDPOINT reject).
            if adapter == "mrerp_dms":
                continue
            connectors.append(
                {
                    "id": f"endpoint_{ep['id']}",
                    "type": adapter,
                    "endpoint_id": str(ep["id"]),
                    "name": ep.get("name") or "Webhook",
                    "method": "webhook",
                    "status": "connected",
                    "is_default": bool(ep.get("is_default")),
                    "meta": {
                        "auto_push": bool(ep.get("auto_push")),
                    },
                }
            )
    except Exception as e:
        logger.warning(f"connectors_status endpoints failed: {e}")

    return {"connectors": connectors}
