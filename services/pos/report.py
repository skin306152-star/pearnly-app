# -*- coding: utf-8 -*-
"""POS 销售报表聚合(POS 项目 · PO-B6 · docs/pos/04 §7)。

从 pos_sales 流水聚合:KPI(营业额/单数/客单价/退款)、按天、按支付方式、畅销品、按收银员。
每个分区一条独立聚合查询——绝不把 lines 与 payments join 进同一句(那会笛卡尔积翻倍金额,
见 [[pos-po-a1-shipped]] 库存翻倍血泪)。应用层每句 WHERE tenant_id + workspace_client_id,
全参数化;日期窗口 [from, to+1d) 半开区间,按曼谷日切(sold_at 是 timestamptz,边界把
「曼谷日零点」换算成绝对时刻,按天分组同用 Asia/Bangkok——店主的「一天」不从 UTC 0 点
即曼谷早上 7 点起算);钱 Decimal 字符串化、量 3 位小数。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from services.pos.report_window import bangkok_day_range as _range
from services.sales.dates import bangkok_today

_HEAT_DAYS = 14


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def _qty(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.3f}"


def sales_report(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    top_n: int = 10,
    prev_from: Optional[date] = None,
    prev_to: Optional[date] = None,
) -> dict:
    base = (tenant_id, workspace_client_id)
    out = {
        "kpi": _kpi(cur, base, date_from, date_to),
        "by_day": _by_day(cur, base, date_from, date_to),
        "by_method": _by_method(cur, base, date_from, date_to),
        "top_products": _top_products(cur, base, date_from, date_to, top_n),
        "by_cashier": _by_cashier(cur, base, date_from, date_to),
    }
    # 环比对照窗口:前端可显式指定语义窗口(按日=上周同日,零售有星期节律;按月=上一自然月),
    # 没给回落相邻等长上一窗口。窗口无界(全程)没有对照物,诚实给 None,前端不显示环比
    # 而不是显示 Odoo 式的「↑∞%」。
    if not (prev_from and prev_to) and date_from and date_to:
        span = (date_to - date_from).days + 1
        prev_to = date_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=span - 1)
    if prev_from and prev_to:
        out["prev_kpi"] = _kpi(cur, base, prev_from, prev_to)
        out["prev_range"] = {"from": prev_from.isoformat(), "to": prev_to.isoformat()}
    else:
        out["prev_kpi"] = None
        out["prev_range"] = None
    # 单日窗口给分时序列(店内钟点 Asia/Bangkok:分时图是给店主看的,UTC 钟点没人看得懂)。
    # 窗口本身仍沿用全表的既有口径,分时桶只是窗口内流水的另一种切法,总额与 KPI 恒等。
    out["by_hour"] = (
        _by_hour(cur, base, date_from, date_to)
        if (date_from and date_to and date_from == date_to)
        else None
    )
    out["heat"] = _heat(cur, base, date_to)
    out["live"] = _live(cur, base)
    return out


def _heat(cur, base, date_to: Optional[date]) -> list:
    """近 14 天 × 钟点的营业额格子(天与小时都按曼谷钟切,凌晨单跨 UTC 日也落对格)。

    锚 = 窗口终点 date_to(热力跟着看的时期走),无锚用曼谷今天。窗口与格子同轴:_range
    已按曼谷日切,[锚−13天 0:00, 锚+1天 0:00) 恰好罩住 14 个完整曼谷日。
    """
    anchor = date_to or bangkok_today()
    rng, rp = _range("sold_at", anchor - timedelta(days=_HEAT_DAYS - 1), anchor)
    cur.execute(
        "SELECT (sold_at AT TIME ZONE 'Asia/Bangkok')::date AS d, "
        "EXTRACT(HOUR FROM (sold_at AT TIME ZONE 'Asia/Bangkok'))::int AS h, "
        "COALESCE(SUM(grand_total),0) AS gross "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' AND sale_type='sale'"
        + rng
        + " GROUP BY 1, 2 ORDER BY 1, 2",
        list(base) + rp,
    )
    return [
        {"date": r["d"].isoformat(), "hour": int(r["h"]), "gross": _money(r["gross"])}
        for r in cur.fetchall()
    ]


def _live(cur, base) -> dict:
    """实时侧写(横幅右徽章):最新一单时刻 + 当前未交班班次。有意不吃窗口——徽章说的是「现在」。"""
    cur.execute(
        "SELECT MAX(sold_at) AS last_sale_at FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' AND sale_type='sale'",
        list(base),
    )
    row = cur.fetchone() or {}
    last = row.get("last_sale_at")
    cur.execute(
        "SELECT sh.shift_seq, c.display_name AS cashier_name "
        "FROM pos_shifts sh LEFT JOIN pos_cashiers c ON c.id = sh.cashier_id "
        "WHERE sh.tenant_id=%s AND sh.workspace_client_id=%s AND sh.status='open' "
        "ORDER BY sh.opened_at DESC LIMIT 1",
        list(base),
    )
    sh = cur.fetchone()
    return {
        "last_sale_at": last.isoformat() if last else None,
        "open_shift": (
            {"cashier_name": sh["cashier_name"], "shift_seq": sh["shift_seq"]} if sh else None
        ),
    }


def _by_hour(cur, base, date_from, date_to) -> list:
    rng, rp = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT EXTRACT(HOUR FROM (sold_at AT TIME ZONE 'Asia/Bangkok'))::int AS h, "
        "COALESCE(SUM(grand_total),0) AS gross, COUNT(*) AS sales_count "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' AND sale_type='sale'"
        + rng
        + " GROUP BY 1 ORDER BY 1",
        list(base) + rp,
    )
    return [
        {"hour": int(r["h"]), "gross": _money(r["gross"]), "sales_count": int(r["sales_count"])}
        for r in cur.fetchall()
    ]


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
        "SELECT (sold_at AT TIME ZONE 'Asia/Bangkok')::date AS d, "
        "COALESCE(SUM(grand_total),0) AS gross, "
        "COUNT(*) AS sales_count "
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
        entry = {"date": d, "gross": _money(gross), "sales_count": int(r["sales_count"])}
        entry.update(_profit_fields(gross, cost_by_day.get(d)))
        out.append(entry)
    return out


def _cost_by_day(cur, base, date_from, date_to) -> dict:
    """按天聚合的 COGS + 完整性(供 _by_day 拼装毛利)。"""
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT (s.sold_at AT TIME ZONE 'Asia/Bangkok')::date AS d, "
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
    # pos_payments.amount 现金笔存的是顾客给的钱(tendered),找零单独存 pos_sales.change_amount。
    # 直接 SUM(amount) 会把找零当现金收入虚增(Bug#4)。混合单里只有现金笔可能溢付(非现金笔前端
    # 按剩余额封顶,无找零),故整单 change_amount 全归现金桶。分两句:按方式汇总 tendered,再单独
    # 汇总找零(pos_sales 每单一行·SUM 天然每单只算一次·避开 min(uuid) 聚合不存在),Python 侧从
    # 现金桶减去。非现金桶口径不变。
    rng_j, rp_j = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT p.method AS method, COALESCE(SUM(p.amount),0) AS amount "
        "FROM pos_payments p JOIN pos_sales s ON s.id = p.sale_id "
        "WHERE p.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'" + rng_j + " GROUP BY p.method",
        list(base) + rp_j,
    )
    out = {r["method"]: Decimal(str(r["amount"])) for r in cur.fetchall()}  # SQL 已 COALESCE(…,0)
    rng_s, rp_s = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT COALESCE(SUM(change_amount),0) AS chg FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s "
        "AND status='completed' AND sale_type='sale'" + rng_s,
        list(base) + rp_s,
    )
    total_change = Decimal(str((cur.fetchone() or {}).get("chg") or 0))
    if total_change:
        out["cash"] = out.get("cash", Decimal("0")) - total_change
    return {m: _money(v) for m, v in out.items()}


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
