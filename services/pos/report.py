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
    refund = Decimal(str(row.get("refund") or 0))
    avg = (gross / count) if count else Decimal("0")
    cost, complete = _cost_agg(cur, base, date_from, date_to)
    # 毛利净口径:营收净额(gross − 退货) − COGS 净额(售出成本 − 退货回冲成本)。gross/单数仍按
    # sale 口径呈现不变(禁区),退货只从毛利底线扣回——否则卖฿100(成本60)全退仍显毛利฿40 虚高。
    # COGS 净额由 _cost_agg 直接给(退货行带负成本,SUM 自动回冲),避免在多处 SQL 各自减退货。
    return {
        "gross": _money(gross),
        "sales_count": count,
        "avg_ticket": _money(avg),
        "refund": _money(refund),
        "cost": _money(cost),
        "gross_profit": _money(gross - refund - cost) if complete else None,
        "cost_complete": complete,
    }


def _cost_agg(cur, base, date_from, date_to) -> tuple[Decimal, bool]:
    """期内 COGS 净额 + 成本快照是否齐全(有老单据/无成本记录 → False)。

    净额=售出行成本 − 退货回冲:退货行的 cost_total 是负值(refund.py 按比例取负快照),故把
    sale+refund 两类行一起 SUM 即得净 COGS,退货成本单一事实源在退货行本身,不在此处二次计算。
    """
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT COALESCE(SUM(l.cost_total),0) AS cost, "
        "COALESCE(BOOL_AND(l.cost_total IS NOT NULL), TRUE) AS complete "
        "FROM pos_sale_lines l JOIN pos_sales s ON s.id = l.sale_id "
        "WHERE l.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type IN ('sale','refund')" + rng,
        list(base) + rp,
    )
    row = cur.fetchone() or {}
    return Decimal(str(row.get("cost") or 0)), bool(row.get("complete", True))


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
    rows = cur.fetchall()
    cost_by_day = _cost_by_day(cur, base, date_from, date_to)
    out = []
    for r in rows:
        d = r["d"].isoformat()
        gross = Decimal(str(r["gross"]))
        entry = {"date": d, "gross": _money(gross)}
        entry.update(_profit_fields(gross, cost_by_day.get(d)))
        out.append(entry)
    return out


def _cost_by_day(cur, base, date_from, date_to) -> dict:
    """按天聚合的 COGS + 完整性(供 _by_day 拼装毛利)。"""
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT (s.sold_at AT TIME ZONE 'UTC')::date AS d, "
        "COALESCE(SUM(l.cost_total),0) AS cost, "
        "COALESCE(BOOL_AND(l.cost_total IS NOT NULL), TRUE) AS complete "
        "FROM pos_sale_lines l JOIN pos_sales s ON s.id = l.sale_id "
        "WHERE l.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'" + rng + " GROUP BY 1",
        list(base) + rp,
    )
    return {
        r["d"].isoformat(): (Decimal(str(r["cost"])), bool(r["complete"])) for r in cur.fetchall()
    }


def _profit_fields(gross: Decimal, cost_entry) -> dict:
    """毛利诚实置空:该桶(天/品)内任一行成本未知 → gross_profit=None,不拿部分数据瞎猜。"""
    if not cost_entry:
        return {"cost": None, "gross_profit": None, "cost_complete": False}
    cost, complete = cost_entry
    return {
        "cost": _money(cost),
        "gross_profit": _money(gross - cost) if complete else None,
        "cost_complete": complete,
    }


def _by_method(cur, base, date_from, date_to) -> dict:
    # 现金桶取净收入:pos_payments.amount 存的是顾客给的钱(tendered),找零单独存在
    # pos_sales.change_amount。直接 SUM(amount) 会把找零当现金收入虚增(Bug#4)。混合单里
    # 只有现金笔可能溢付(非现金笔前端按剩余额封顶,无找零),故整单 change_amount 全归现金笔,
    # 且只从每单最早一笔现金(MIN(id))减一次——防同单多现金笔重复扣。非现金桶口径不变。
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT p.method AS method, COALESCE(SUM(p.amount - CASE "
        "WHEN p.method='cash' AND p.id = ("
        "SELECT MIN(p2.id) FROM pos_payments p2 "
        "WHERE p2.sale_id=p.sale_id AND p2.method='cash') "
        "THEN s.change_amount ELSE 0 END),0) AS amount "
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
        "COALESCE(SUM(l.qty),0) AS qty, COALESCE(SUM(l.line_total),0) AS gross, "
        "COALESCE(SUM(l.cost_total),0) AS cost, "
        "COALESCE(BOOL_AND(l.cost_total IS NOT NULL), TRUE) AS complete "
        "FROM pos_sale_lines l JOIN pos_sales s ON s.id = l.sale_id "
        "JOIN products pr ON pr.id = l.product_id "
        "WHERE l.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'"
        + rng
        + " GROUP BY l.product_id, pr.name_th, pr.name_en, pr.name_zh "
        "ORDER BY gross DESC LIMIT %s",
        list(base) + rp + [int(top_n)],
    )
    out = []
    for r in cur.fetchall():
        gross = Decimal(str(r["gross"]))
        entry = {
            "product_id": str(r["product_id"]),
            "name": {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]},
            "qty": _qty(r["qty"]),
            "gross": _money(gross),
        }
        entry.update(_profit_fields(gross, (Decimal(str(r["cost"])), bool(r["complete"]))))
        out.append(entry)
    return out


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
