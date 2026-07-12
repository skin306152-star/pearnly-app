# -*- coding: utf-8 -*-
"""库存报表路由(POS 项目 · C1 · docs/pos/04 §4)。

薄层:require_perm_pos_tid(库存报表是老板/会计后台分析,收银员 token 不可调)→ 模块守门(inventory)
→ account 归属 → 调 services/inventory/reports。统一 POS 信封。只读。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Request

from core import db
from core.pos_api import assert_module_enabled, ok, require_workspace_access
from services.authz import field_mask
from services.authz.deps import require_perm_pos_tid
from services.inventory import reports as report_svc

router = APIRouter(prefix="/api/inventory", tags=["inventory-report"])


def _parse_date(raw: Optional[str], default: date) -> date:
    if not raw:
        return default
    try:
        return date.fromisoformat(raw.strip())
    except (ValueError, AttributeError):
        return default


@router.get("/report")
async def api_inventory_report(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    near_expiry_days: int = Query(30, ge=1, le=365),
):
    """进销存 + 周转 + 近效期看板。默认期间=本月 1 号至今天(请求可覆盖 from/to)。"""
    today = date.today()
    d_to = _parse_date(date_to, today)
    d_from = _parse_date(date_from, today.replace(day=1))
    tid, _uid = require_perm_pos_tid(request, "inv.report.view")
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "inventory")
        require_workspace_access(cur, request, tid, workspace_client_id)
        data = report_svc.inventory_report(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            date_from=d_from,
            date_to=d_to,
            near_expiry_days=near_expiry_days,
            mask_cost=not field_mask.cost_visible(request),
        )
    return ok(data)
