# -*- coding: utf-8 -*-
"""POS 销售报表路由(POS 项目 · PO-B6 · docs/pos/04 §7)。

薄层:require_perm_pos_tid(收银员 token 不可调报表)→ 模块守门(pos)→ account 归属 → 调
services/pos/report 聚合。统一 POS 信封。只读(get_cursor_rls 不 commit)。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Request

from core import db
from core.pos_api import assert_module_enabled, ok, require_workspace
from services.authz.deps import require_perm_pos_tid
from services.pos import audit_report as audit_svc
from services.pos import report as report_svc

router = APIRouter(prefix="/api/pos", tags=["pos-report"])


def _parse_date(raw: Optional[str]) -> Optional[date]:
    """YYYY-MM-DD → date;空/坏格式 → None(该边界不设限,报表覆盖全程)。"""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw.strip())
    except (ValueError, AttributeError):
        return None


@router.get("/admin/report")
async def api_report(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
):
    """销售报表:KPI / 按天 / 按支付 / 畅销 / 按收银员。数据从 pos_sales 流水聚合。"""
    tid, _uid = require_perm_pos_tid(request, "pos.report.view")
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, workspace_client_id)
        data = report_svc.sales_report(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
        )
    return ok(data)


@router.get("/admin/audit/summary")
async def api_audit_summary(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    cashier_id: Optional[str] = Query(None),
):
    """异常汇总:每收银员的作废/退货/折扣(次数+金额)+ 长短款,附合计。老板端防内盗速览。"""
    tid, _uid = require_perm_pos_tid(request, "pos.report.view")
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, workspace_client_id)
        data = audit_svc.summary(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            cashier_id=cashier_id,
        )
    return ok(data)


@router.get("/admin/audit/events")
async def api_audit_events(
    request: Request,
    workspace_client_id: int = Query(...),
    kind: str = Query(...),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    cashier_id: Optional[str] = Query(None),
):
    """异常下钻明细:某类(void/refund/discount)逐笔——时间/收银员/金额/单号/授权人。"""
    tid, _uid = require_perm_pos_tid(request, "pos.report.view")
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, workspace_client_id)
        data = audit_svc.events(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            kind=kind,
            cashier_id=cashier_id,
        )
    return ok(data)
