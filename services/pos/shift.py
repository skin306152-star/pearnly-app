# -*- coding: utf-8 -*-
"""班次开/交班 + 日结(POS 项目 · PO-B2 · docs/pos/04 §5)。

开班:校无未结班次(DB partial unique 兜底 · 这里先查给友好码 pos.shift_already_open)。交班:
算应有现金(备用金 + 现金销售 - 现金退款)、汇总当班销售(笔数/毛额/各支付方式),写差异收口。
每条语句 WHERE tenant_id;在已开事务的 cursor 上调用。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.pos import cashier as cashier_dal


def _f(v) -> float:
    return float(v) if v is not None else 0.0


def open_shift(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    terminal_id: Optional[int] = None,
    cashier_id: str,
    opening_float,
) -> dict:
    # 单终端门店常态:前台不显式带 terminal_id → 回落账套默认终端(无则建)。
    if terminal_id is None:
        term = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        terminal_id = term["id"]
    cur.execute(
        "SELECT 1 FROM pos_shifts WHERE tenant_id = %s AND terminal_id = %s AND status = 'open'",
        (tenant_id, terminal_id),
    )
    if cur.fetchone():
        raise PosError("pos.shift_already_open", 409)
    cur.execute(
        "INSERT INTO pos_shifts "
        "(tenant_id, workspace_client_id, terminal_id, cashier_id, opening_float) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id, opened_at, opening_float",
        (tenant_id, workspace_client_id, terminal_id, cashier_id, Decimal(str(opening_float))),
    )
    row = cur.fetchone()
    return {
        "id": str(row["id"]),
        "terminal_id": terminal_id,
        "opened_at": row["opened_at"].isoformat() if row["opened_at"] else None,
        "opening_float": _f(row["opening_float"]),
    }


def _get_open_shift(cur, *, tenant_id: str, shift_id: str):
    cur.execute(
        "SELECT id, opening_float, status FROM pos_shifts WHERE tenant_id = %s AND id = %s",
        (tenant_id, shift_id),
    )
    return cur.fetchone()


def _summary(cur, *, tenant_id: str, shift_id: str) -> dict:
    """当班销售汇总:笔数/毛额(完成的正常销售)+ 各支付方式净额(销售为正、退款为负)。"""
    cur.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(grand_total), 0) AS gross FROM pos_sales "
        "WHERE tenant_id = %s AND shift_id = %s AND sale_type = 'sale' AND status = 'completed'",
        (tenant_id, shift_id),
    )
    head = cur.fetchone()
    cur.execute(
        "SELECT p.method, COALESCE(SUM(p.amount), 0) AS amt FROM pos_payments p "
        "JOIN pos_sales s ON s.id = p.sale_id "
        "WHERE p.tenant_id = %s AND s.shift_id = %s AND s.status = 'completed' "
        "GROUP BY p.method",
        (tenant_id, shift_id),
    )
    by_method = {r["method"]: _f(r["amt"]) for r in cur.fetchall()}
    cur.execute(
        "SELECT COALESCE(SUM(change_amount), 0) AS chg FROM pos_sales "
        "WHERE tenant_id = %s AND shift_id = %s AND status = 'completed'",
        (tenant_id, shift_id),
    )
    change_total = Decimal(str(cur.fetchone()["chg"]))
    return {
        "sales_count": int(head["n"]),
        "gross": _f(head["gross"]),
        "by_method": by_method,
        "change_total": _f(change_total),
    }


def close_shift(
    cur, *, tenant_id: str, workspace_client_id: int, shift_id: str, counted_cash
) -> dict:
    shift = _get_open_shift(cur, tenant_id=tenant_id, shift_id=shift_id)
    if not shift or shift["status"] != "open":
        raise PosError("pos.shift_closed", 409)
    summary = _summary(cur, tenant_id=tenant_id, shift_id=shift_id)
    # 现金支付额是【收取额(含找零前)】;抽屉净现金 = 现金收取 - 找零(找零只发现金)。
    cash_in = Decimal(str(summary["by_method"].get("cash", 0)))
    change_out = Decimal(str(summary.get("change_total", 0)))
    expected = Decimal(str(shift["opening_float"])) + cash_in - change_out
    counted = Decimal(str(counted_cash))
    diff = counted - expected
    cur.execute(
        "UPDATE pos_shifts SET status = 'closed', closed_at = now(), "
        "expected_cash = %s, counted_cash = %s, cash_diff = %s "
        "WHERE tenant_id = %s AND id = %s "
        "RETURNING id, closed_at, expected_cash, counted_cash, cash_diff",
        (expected, counted, diff, tenant_id, shift_id),
    )
    row = cur.fetchone()
    return {
        "shift": {
            "id": str(row["id"]),
            "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
            "expected_cash": _f(row["expected_cash"]),
            "counted_cash": _f(row["counted_cash"]),
            "cash_diff": _f(row["cash_diff"]),
        },
        "summary": summary,
    }
