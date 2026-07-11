# -*- coding: utf-8 -*-
"""POS 异常/审计读模型(POS 项目 · PC-2 · 防内盗信任基石)。

老板端「操作记录/异常」页的数据源:对标 Square 的 Comps&Voids / Discounts 报表——按收银员
汇总作废/退货/折扣/长短款(次数 + 金额),可下钻到具体几笔。跟 report.py(营业额聚合)、
sales_log.py(逐笔流水)是三个不同粒度,不重复。

归属口径(「这笔是谁点的」):
  - 销售/折扣:pos_sales.cashier_id(经手收银员)。
  - 退货:退货是新负单,其 cashier_id/created_by = 操作者本人(refund.py 落库时写入)。
  - 作废:原单 cashier_id 是原销售员,不是作废操作人;真正的「谁点了作废」记在
    operation_logs(action='pos.sale.voided' · details.operator_cashier_id),故按该操作人归属,
    无该记录的历史作废回落原销售员。
  - 长短款:pos_shifts.cash_diff 按班次 cashier_id 汇总(仅已交班)。

每个指标一句独立聚合(绝不 join 出笛卡尔积翻倍金额,见 report.py 同一条血泪),应用层每句
WHERE tenant_id + workspace_client_id 全参数化;钱 Decimal、序列化成 2 位小数字符串;时间窗口
半开 [from, to+1天)。作废/退货窗口按业务日(销售在 sold_at、长短款在 closed_at)。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

# 各指标下钻的过滤/金额口径 + 授权覆盖动作(events 的 authorized_by 来源)。
_KIND_WHERE = {
    "void": "s.status = 'void'",
    "refund": "s.status = 'completed' AND s.sale_type = 'refund'",
    "discount": "s.status = 'completed' AND s.sale_type = 'sale' AND s.discount_total > 0",
}
_KIND_AMOUNT = {"void": "s.grand_total", "refund": "-s.grand_total", "discount": "s.discount_total"}
_KIND_APPROVE_ACTION = {
    "void": "pos.void.approved",
    "refund": "pos.refund.approved",
    "discount": "pos.discount.approved",
}

# 作废操作人 lateral:取该单最近一条 pos.sale.voided 记录里的操作收银员(谁点了作废)。
_VOIDER_LATERAL = (
    "LEFT JOIN LATERAL ("
    "  SELECT NULLIF(ol.details->>'operator_cashier_id', '')::uuid AS op_cashier_id"
    "  FROM operation_logs ol"
    "  WHERE ol.tenant_id = s.tenant_id AND ol.action = 'pos.sale.voided'"
    "        AND ol.target_id = s.id::text"
    "  ORDER BY ol.created_at DESC LIMIT 1"
    ") vl ON TRUE"
)
_VOIDER_CASHIER = "COALESCE(vl.op_cashier_id, s.cashier_id)"

_EVENTS_CAP = 500


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def _range(col: str, date_from: Optional[date], date_to: Optional[date]) -> tuple[str, list]:
    """时间窗口片段(半开 [from, to+1天)·含 to 当天)。无界则不加条件。"""
    clause, params = "", []
    if date_from:
        clause += f" AND {col} >= %s"
        params.append(date_from)
    if date_to:
        clause += f" AND {col} < %s"
        params.append(date_to + timedelta(days=1))
    return clause, params


def _cashier_filter(expr: str, cashier_id: Optional[str]) -> tuple[str, list]:
    """按归属收银员筛(expr = 该指标的归属列/表达式)。"""
    if not cashier_id:
        return "", []
    return f" AND {expr} = %s::uuid", [cashier_id]


def _empty(cid: Optional[str]) -> dict:
    return {
        "cashier_id": cid,
        "cashier_name": None,
        "sales_count": 0,
        "sales_amount": Decimal("0"),
        "void_count": 0,
        "void_amount": Decimal("0"),
        "refund_count": 0,
        "refund_amount": Decimal("0"),
        "discount_count": 0,
        "discount_amount": Decimal("0"),
        "cash_short_over": Decimal("0"),
    }


def summary(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    cashier_id: Optional[str] = None,
) -> dict:
    """每收银员一行:销售/作废/退货/折扣的次数+金额 + 长短款,附一个合计行。

    各指标独立聚合后按归属收银员合并(作废归操作人、退货归操作者、销售/折扣归经手人)。
    """
    base = (tenant_id, workspace_client_id)
    rows: dict = {}

    def slot(cid, name) -> dict:
        key = str(cid) if cid else None
        if key not in rows:
            rows[key] = _empty(key)
        if name and not rows[key]["cashier_name"]:
            rows[key]["cashier_name"] = name
        return rows[key]

    _sales(cur, base, date_from, date_to, cashier_id, slot)
    _discounts(cur, base, date_from, date_to, cashier_id, slot)
    _voids(cur, base, date_from, date_to, cashier_id, slot)
    _refunds(cur, base, date_from, date_to, cashier_id, slot)
    _cash_diff(cur, base, date_from, date_to, cashier_id, slot)

    ordered = sorted(rows.values(), key=lambda r: r["sales_amount"], reverse=True)
    return {"rows": [_serialize(r) for r in ordered], "total": _total(ordered)}


def _serialize(r: dict) -> dict:
    return {
        **r,
        "sales_amount": _money(r["sales_amount"]),
        "void_amount": _money(r["void_amount"]),
        "refund_amount": _money(r["refund_amount"]),
        "discount_amount": _money(r["discount_amount"]),
        "cash_short_over": _money(r["cash_short_over"]),
    }


def _total(rows: list) -> dict:
    agg = _empty(None)
    del agg["cashier_id"], agg["cashier_name"]
    for r in rows:
        for k in agg:
            agg[k] += r[k]
    return {
        "sales_count": agg["sales_count"],
        "sales_amount": _money(agg["sales_amount"]),
        "void_count": agg["void_count"],
        "void_amount": _money(agg["void_amount"]),
        "refund_count": agg["refund_count"],
        "refund_amount": _money(agg["refund_amount"]),
        "discount_count": agg["discount_count"],
        "discount_amount": _money(agg["discount_amount"]),
        "cash_short_over": _money(agg["cash_short_over"]),
    }


def _sales(cur, base, date_from, date_to, cashier_id, slot) -> None:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cf, cfp = _cashier_filter("s.cashier_id", cashier_id)
    cur.execute(
        "SELECT s.cashier_id AS cid, c.display_name AS name, "
        "COUNT(*) AS cnt, COALESCE(SUM(s.grand_total), 0) AS amt "
        "FROM pos_sales s LEFT JOIN pos_cashiers c ON c.id = s.cashier_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s "
        "AND s.status = 'completed' AND s.sale_type = 'sale'"
        + rng
        + cf
        + " GROUP BY s.cashier_id, c.display_name",
        list(base) + rp + cfp,
    )
    for r in cur.fetchall():
        row = slot(r["cid"], r["name"])
        row["sales_count"] = int(r["cnt"])
        row["sales_amount"] = Decimal(str(r["amt"]))


def _discounts(cur, base, date_from, date_to, cashier_id, slot) -> None:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cf, cfp = _cashier_filter("s.cashier_id", cashier_id)
    cur.execute(
        "SELECT s.cashier_id AS cid, c.display_name AS name, "
        "COUNT(*) AS cnt, COALESCE(SUM(s.discount_total), 0) AS amt "
        "FROM pos_sales s LEFT JOIN pos_cashiers c ON c.id = s.cashier_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s "
        "AND s.status = 'completed' AND s.sale_type = 'sale' AND s.discount_total > 0"
        + rng
        + cf
        + " GROUP BY s.cashier_id, c.display_name",
        list(base) + rp + cfp,
    )
    for r in cur.fetchall():
        row = slot(r["cid"], r["name"])
        row["discount_count"] = int(r["cnt"])
        row["discount_amount"] = Decimal(str(r["amt"]))


def _voids(cur, base, date_from, date_to, cashier_id, slot) -> None:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cf, cfp = _cashier_filter(_VOIDER_CASHIER, cashier_id)
    cur.execute(
        f"SELECT {_VOIDER_CASHIER} AS cid, c.display_name AS name, "
        "COUNT(*) AS cnt, COALESCE(SUM(s.grand_total), 0) AS amt "
        "FROM pos_sales s "
        + _VOIDER_LATERAL
        + f" LEFT JOIN pos_cashiers c ON c.id = {_VOIDER_CASHIER} "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND s.status = 'void'"
        + rng
        + cf
        + f" GROUP BY {_VOIDER_CASHIER}, c.display_name",
        list(base) + rp + cfp,
    )
    for r in cur.fetchall():
        row = slot(r["cid"], r["name"])
        row["void_count"] = int(r["cnt"])
        row["void_amount"] = Decimal(str(r["amt"]))


def _refunds(cur, base, date_from, date_to, cashier_id, slot) -> None:
    rng, rp = _range("s.sold_at", date_from, date_to)
    cf, cfp = _cashier_filter("s.cashier_id", cashier_id)
    cur.execute(
        "SELECT s.cashier_id AS cid, c.display_name AS name, "
        "COUNT(*) AS cnt, COALESCE(SUM(-s.grand_total), 0) AS amt "
        "FROM pos_sales s LEFT JOIN pos_cashiers c ON c.id = s.cashier_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s "
        "AND s.status = 'completed' AND s.sale_type = 'refund'"
        + rng
        + cf
        + " GROUP BY s.cashier_id, c.display_name",
        list(base) + rp + cfp,
    )
    for r in cur.fetchall():
        row = slot(r["cid"], r["name"])
        row["refund_count"] = int(r["cnt"])
        row["refund_amount"] = Decimal(str(r["amt"]))


def _cash_diff(cur, base, date_from, date_to, cashier_id, slot) -> None:
    rng, rp = _range("sh.closed_at", date_from, date_to)
    cf, cfp = _cashier_filter("sh.cashier_id", cashier_id)
    cur.execute(
        "SELECT sh.cashier_id AS cid, c.display_name AS name, "
        "COALESCE(SUM(sh.cash_diff), 0) AS amt "
        "FROM pos_shifts sh LEFT JOIN pos_cashiers c ON c.id = sh.cashier_id "
        "WHERE sh.tenant_id = %s AND sh.workspace_client_id = %s "
        "AND sh.status = 'closed' AND sh.cash_diff IS NOT NULL"
        + rng
        + cf
        + " GROUP BY sh.cashier_id, c.display_name",
        list(base) + rp + cfp,
    )
    for r in cur.fetchall():
        row = slot(r["cid"], r["name"])
        row["cash_short_over"] = Decimal(str(r["amt"]))


def events(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[date],
    date_to: Optional[date],
    kind: str,
    cashier_id: Optional[str] = None,
) -> dict:
    """某一类异常(作废/退货/折扣)的下钻明细。每条:时间/类型/收银员/金额/单号/授权人。

    收银员 = 归属人(作废取操作人、退货/折扣取经手人);authorized_by = 若该单有店长授权覆盖
    (operation_logs 对应 *.approved 行)则带出授权人名,无则 None。
    """
    if kind not in _KIND_WHERE:
        return {"events": []}
    is_void = kind == "void"
    cashier_expr = _VOIDER_CASHIER if is_void else "s.cashier_id"

    rng, rp = _range("s.sold_at", date_from, date_to)
    cf, cfp = _cashier_filter(cashier_expr, cashier_id)
    approve_lateral = (
        "LEFT JOIN LATERAL ("
        "  SELECT ol.actor_username AS approver FROM operation_logs ol"
        f"  WHERE ol.tenant_id = s.tenant_id AND ol.action = '{_KIND_APPROVE_ACTION[kind]}'"
        "        AND ol.target_id = s.id::text"
        "  ORDER BY ol.created_at DESC LIMIT 1"
        ") al ON TRUE"
    )
    joins = _VOIDER_LATERAL + " " if is_void else ""
    cur.execute(
        f"SELECT s.sold_at, {cashier_expr} AS cid, c.display_name AS cashier_name, "
        f"{_KIND_AMOUNT[kind]} AS amount, s.receipt_no, al.approver AS authorized_by "
        "FROM pos_sales s "
        + joins
        + approve_lateral
        + f" LEFT JOIN pos_cashiers c ON c.id = {cashier_expr} "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND "
        + _KIND_WHERE[kind]
        + rng
        + cf
        + " ORDER BY s.sold_at DESC LIMIT %s",
        [tenant_id, workspace_client_id] + rp + cfp + [_EVENTS_CAP],
    )
    return {
        "events": [
            {
                "sold_at": r["sold_at"].isoformat() if r["sold_at"] else None,
                "kind": kind,
                "cashier_name": r["cashier_name"],
                "amount": _money(r["amount"]),
                "receipt_no": r["receipt_no"],
                "authorized_by": r["authorized_by"],
            }
            for r in cur.fetchall()
        ]
    }
