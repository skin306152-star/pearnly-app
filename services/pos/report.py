# -*- coding: utf-8 -*-
"""POS 销售报表聚合(POS 项目 · PO-B6 · docs/pos/04 §7)。

从 pos_sales 流水聚合:KPI(营业额/单数/客单价/退款)、按天、按支付方式、畅销品、按收银员。
每个分区一条独立聚合查询——绝不把 lines 与 payments join 进同一句(那会笛卡尔积翻倍金额,
见 [[pos-po-a1-shipped]] 库存翻倍血泪)。应用层每句 WHERE tenant_id + workspace_client_id,
全参数化;日期窗口 [from, to+1d) 半开区间;钱 Decimal 字符串化、量 3 位小数。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def _qty(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.3f}"


def _range(col: str, date_from: Optional[date], date_to: Optional[date]) -> tuple[str, list]:
    """sold_at 时间窗口片段(半开 [from, to+1天)· 含 to 当天)。无界则不加条件。"""
    clause, params = "", []
    if date_from:
        clause += f" AND {col} >= %s"
        params.append(date_from)
    if date_to:
        clause += f" AND {col} < %s"
        params.append(date_to + timedelta(days=1))
    return clause, params


def sales_report(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    top_n: int = 10,
) -> dict:
    base = (tenant_id, workspace_client_id)
    return {
        "kpi": _kpi(cur, base, date_from, date_to),
        "by_day": _by_day(cur, base, date_from, date_to),
        "by_method": _by_method(cur, base, date_from, date_to),
        "top_products": _top_products(cur, base, date_from, date_to, top_n),
        "by_cashier": _by_cashier(cur, base, date_from, date_to),
    }


def _kpi(cur, base, date_from, date_to) -> dict:
    rng, rp = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT "
        "COALESCE(SUM(grand_total) FILTER (WHERE sale_type='sale'),0) AS gross, "
        "COUNT(*) FILTER (WHERE sale_type='sale') AS sales_count, "
        "COALESCE(-SUM(grand_total) FILTER (WHERE sale_type='refund'),0) AS refund "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed'" + rng,
        list(base) + rp,
    )
    row = cur.fetchone() or {}
    gross = Decimal(str(row.get("gross") or 0))
    count = int(row.get("sales_count") or 0)
    avg = (gross / count) if count else Decimal("0")
    return {
        "gross": _money(gross),
        "sales_count": count,
        "avg_ticket": _money(avg),
        "refund": _money(row.get("refund")),
    }


def _by_day(cur, base, date_from, date_to) -> list:
    rng, rp = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT (sold_at AT TIME ZONE 'UTC')::date AS d, COALESCE(SUM(grand_total),0) AS gross "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' AND sale_type='sale'"
        + rng
        + " GROUP BY 1 ORDER BY 1",
        list(base) + rp,
    )
    return [{"date": r["d"].isoformat(), "gross": _money(r["gross"])} for r in cur.fetchall()]


def _by_method(cur, base, date_from, date_to) -> dict:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT p.method AS method, COALESCE(SUM(p.amount),0) AS amount "
        "FROM pos_payments p JOIN pos_sales s ON s.id = p.sale_id "
        "WHERE p.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'" + rng + " GROUP BY p.method",
        list(base) + rp,
    )
    return {r["method"]: _money(r["amount"]) for r in cur.fetchall()}


def _top_products(cur, base, date_from, date_to, top_n) -> list:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT l.product_id, pr.name_th, pr.name_en, pr.name_zh, "
        "COALESCE(SUM(l.qty),0) AS qty, COALESCE(SUM(l.line_total),0) AS gross "
        "FROM pos_sale_lines l JOIN pos_sales s ON s.id = l.sale_id "
        "JOIN products pr ON pr.id = l.product_id "
        "WHERE l.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'"
        + rng
        + " GROUP BY l.product_id, pr.name_th, pr.name_en, pr.name_zh "
        "ORDER BY gross DESC LIMIT %s",
        list(base) + rp + [int(top_n)],
    )
    return [
        {
            "product_id": str(r["product_id"]),
            "name": {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]},
            "qty": _qty(r["qty"]),
            "gross": _money(r["gross"]),
        }
        for r in cur.fetchall()
    ]


def _by_cashier(cur, base, date_from, date_to) -> list:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT s.cashier_id, c.display_name AS name, "
        "COUNT(*) AS sales_count, COALESCE(SUM(s.grand_total),0) AS gross "
        "FROM pos_sales s LEFT JOIN pos_cashiers c ON c.id = s.cashier_id "
        "WHERE s.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'"
        + rng
        + " GROUP BY s.cashier_id, c.display_name ORDER BY gross DESC",
        list(base) + rp,
    )
    return [
        {
            "cashier_id": str(r["cashier_id"]) if r["cashier_id"] else None,
            "name": r["name"],
            "sales_count": int(r["sales_count"]),
            "gross": _money(r["gross"]),
        }
        for r in cur.fetchall()
    ]
