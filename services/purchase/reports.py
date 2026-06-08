# -*- coding: utf-8 -*-
"""采购汇总(联动报税 · docs/purchasing/02 §7)。

按期聚合进货/费用/可抵进项税/WHT 代扣(喂报税:销项税−进项税;WHT→PND 53/3)。单表
FILTER 聚合,无 join 无笛卡尔。只算 posted。隔离=WHERE tenant_id + workspace_client_id。
"""

from __future__ import annotations

from typing import Optional


def summary(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """期间汇总。from/to 缺省=不限(全部 posted)。日期闭区间(含端点)。"""
    sql = (
        "SELECT "
        "COALESCE(SUM(grand_total) FILTER (WHERE doc_kind IN "
        "('purchase_invoice','purchase_order')), 0) AS goods_total, "
        "COALESCE(SUM(grand_total) FILTER (WHERE doc_kind = 'expense'), 0) AS expense_total, "
        "COALESCE(SUM(vat_amount) FILTER (WHERE doc_kind = 'purchase_invoice' AND has_vat), 0) "
        "AS vat_claimable, "
        "COALESCE(SUM(wht_amount), 0) AS wht_total, "
        "COALESCE(SUM(net_payable - paid_amount) FILTER (WHERE payment_status <> 'paid'), 0) "
        "AS unpaid_total, "
        "COUNT(*) AS doc_count "
        "FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'posted'"
    )
    params: list = [tenant_id, workspace_client_id]
    if date_from:
        sql += " AND doc_date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND doc_date <= %s"
        params.append(date_to)
    cur.execute(sql, tuple(params))
    r = cur.fetchone()
    return {
        "goods_total": r["goods_total"],
        "expense_total": r["expense_total"],
        "vat_claimable": r["vat_claimable"],
        "wht_total": r["wht_total"],
        "unpaid_total": r["unpaid_total"],
        "doc_count": int(r["doc_count"]),
        "from": date_from,
        "to": date_to,
    }
