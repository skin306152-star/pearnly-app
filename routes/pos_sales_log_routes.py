# -*- coding: utf-8 -*-
"""POS 交易明细日志路由(老板后台 · 逐笔流水 + CSV 导出)。

薄层:require_perm_pos_tid(view 级 · 收银员 token 不可调,同报表口径)→ 模块守门(pos)→
账套归属 → 调 services/pos/sales_log。CSV 走 SafeCsvWriter 防公式注入(同 admin_logs 先例)。
"""

from __future__ import annotations

import csv as _csv
from datetime import date
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from core import db
from core.pos_api import assert_module_enabled, ok, require_workspace
from services.authz.deps import require_perm_pos_tid
from services.export.csv_safe import SafeCsvWriter
from services.pos import sales_log as svc
from services.pos import sheets_labels

router = APIRouter(prefix="/api/pos/admin", tags=["pos-sales-log"])


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw.strip())
    except (ValueError, AttributeError):
        return None


@router.get("/sales-log")
async def api_sales_log(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    cashier_id: Optional[str] = Query(None),
    lang: str = Query("th"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """逐笔交易明细(时间/收银员/商品/金额/付款方式/所属班次)+ 按筛选的总数。"""
    tid, _uid = require_perm_pos_tid(request, "pos.report.view")
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, workspace_client_id)
        data = svc.list_sales(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            cashier_id=cashier_id,
            lang=lang,
            limit=limit,
            offset=offset,
        )
    return ok(data)


@router.get("/sales-log/export.csv")
async def api_sales_log_export(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    cashier_id: Optional[str] = Query(None),
    lang: str = Query("th"),
):
    """按当前筛选(日期段 + 收银员)导出 CSV,列口径跟 Google Sheet 留档对齐 + 多一列班次。"""
    tid, _uid = require_perm_pos_tid(request, "pos.report.view")
    lg = sheets_labels.norm_lang(lang)
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, workspace_client_id)
        rows = svc.export_rows(
            cur,
            tenant_id=tid,
            workspace_client_id=workspace_client_id,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            cashier_id=cashier_id,
            lang=lg,
        )

    buf = StringIO()
    buf.write("﻿")
    w = SafeCsvWriter(_csv.writer(buf))
    w.writerow([*sheets_labels.header_row(lg), sheets_labels.shift_label(lg)])
    for r in rows:
        shift = (
            f"{r['shift_opened_at']}–{r['shift_closed_at'] or sheets_labels.shift_open_label(lg)}"
            if r["shift_opened_at"]
            else ""
        )
        w.writerow(
            [
                r["receipt_no"],
                r["sold_at"][:10],
                r["sold_at"][11:19],
                r["cashier_name"],
                r["items"],
                r["qty_total"],
                r["subtotal"],
                r["discount_total"],
                r["vat_amount"],
                r["grand_total"],
                r["method"],
                r["paid_total"],
                r["change_amount"],
                shift,
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_pos_sales_log.csv"'},
    )
