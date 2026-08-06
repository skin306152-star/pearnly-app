# -*- coding: utf-8 -*-
"""POS 销项月度汇总(POS 项目 · G3 · docs/pos/04 §7b)。

代账每月做 ภ.พ.30 申报靠这份包对账:金额只读 pos_sales 一张表(services/pos/sales_log.py 的
拆列口径),含已升级为全式税票的行——upgrade.py 回填 full_invoice_id 时金额逐字搬自原小票,
计一次即正确,不二次从 sales_documents 取数(不重复计 VAT,见 docs/pos/04 §6)。
sales_documents 只用来出「全式税票清单」附录佐证。

全式票开在 M+1 月而原单在 M 月的,附录按原单 sold_at 的曼谷月归属(join full_invoice_id),
不按 issue_date——结构上不存在跨月双计。

退货/作废的计入范围与 services/pos/report.py 的 _kpi 同一 FILTER 口径(sale_type='sale' 计
营收、'refund' 单独净额、status!='completed' 天然排除作废),两处对同一个月不会报出两套数字。
"""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date
from decimal import Decimal

from services.pos import report as report_svc
from services.pos.report_window import bangkok_day_range as _range

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class MonthInvalid(ValueError):
    """月份参数不是 YYYY-MM(路由转 pos.month_invalid · 422)。"""


def parse_month(month: str) -> tuple[date, date]:
    """ "YYYY-MM" → 该曼谷月的 (第一天, 最后一天)。"""
    if not month or not _MONTH_RE.match(month):
        raise MonthInvalid(month)
    year, mon = int(month[:4]), int(month[5:7])
    return date(year, mon, 1), date(year, mon, monthrange(year, mon)[1])


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def month_summary(cur, *, tenant_id: str, workspace_client_id: int, month: str) -> dict:
    """月度销项汇总包:日汇总 + 支付方式 + 月合计 + ABB 票号区间 + 全式税票附录。"""
    date_from, date_to = parse_month(month)
    base = (tenant_id, workspace_client_id)
    return {
        "month": month,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "days": _days(cur, base, date_from, date_to),
        "by_method": _by_method_with_counts(cur, base, date_from, date_to),
        "totals": _totals(cur, base, date_from, date_to),
        "abb_ranges": _abb_ranges(cur, base, date_from, date_to),
        "full_invoices": _full_invoices(cur, base, date_from, date_to),
    }


def _days(cur, base, date_from, date_to) -> list:
    rng, rp = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT (sold_at AT TIME ZONE 'Asia/Bangkok')::date AS d, COUNT(*) AS sales_count, "
        "COALESCE(SUM(subtotal),0) AS subtotal, COALESCE(SUM(discount_total),0) AS discount_total, "
        "COALESCE(SUM(vat_amount),0) AS vat_amount, COALESCE(SUM(grand_total),0) AS grand_total "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' AND sale_type='sale'"
        + rng
        + " GROUP BY 1 ORDER BY 1",
        list(base) + rp,
    )
    return [
        {
            "date": r["d"].isoformat(),
            "sales_count": int(r["sales_count"]),
            "subtotal": _money(r["subtotal"]),
            "discount_total": _money(r["discount_total"]),
            "vat_amount": _money(r["vat_amount"]),
            "gross": _money(r["grand_total"]),
        }
        for r in cur.fetchall()
    ]


def _by_method_with_counts(cur, base, date_from, date_to) -> dict:
    """金额净额复用 report._by_method(找零回冲同一套逻辑,不重新发明);笔数另起一句
    (笔数不受找零影响,不需要那套净额算法)。"""
    amounts = report_svc._by_method(cur, base, date_from, date_to)
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT p.method AS method, COUNT(*) AS n FROM pos_payments p "
        "JOIN pos_sales s ON s.id = p.sale_id "
        "WHERE p.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'" + rng + " GROUP BY p.method",
        list(base) + rp,
    )
    counts = {r["method"]: int(r["n"]) for r in cur.fetchall()}
    return {m: {"amount": amt, "count": counts.get(m, 0)} for m, amt in amounts.items()}


def _totals(cur, base, date_from, date_to) -> dict:
    """月合计:与 report._kpi 同一 FILTER 口径(sale='sale' 拆列营收 · refund 单独净额)。"""
    rng, rp = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT "
        "COALESCE(SUM(subtotal) FILTER (WHERE sale_type='sale'),0) AS subtotal, "
        "COALESCE(SUM(discount_total) FILTER (WHERE sale_type='sale'),0) AS discount_total, "
        "COALESCE(SUM(vat_amount) FILTER (WHERE sale_type='sale'),0) AS vat_amount, "
        "COALESCE(SUM(grand_total) FILTER (WHERE sale_type='sale'),0) AS gross, "
        "COUNT(*) FILTER (WHERE sale_type='sale') AS sales_count, "
        "COALESCE(-SUM(grand_total) FILTER (WHERE sale_type='refund'),0) AS refund "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed'" + rng,
        list(base) + rp,
    )
    row = cur.fetchone() or {}
    return {
        "subtotal": _money(row.get("subtotal")),
        "discount_total": _money(row.get("discount_total")),
        "vat_amount": _money(row.get("vat_amount")),
        "gross": _money(row.get("gross")),
        "sales_count": int(row.get("sales_count") or 0),
        "refund": _money(row.get("refund")),
    }


def _abb_ranges(cur, base, date_from, date_to) -> list:
    """按曼谷日的简式小票(ABB)票号区间——事务所核对连号完整性用。同日跨终端会合并成
    一个区间,不判定跨终端断号(号段本身按终端各自连续,见 numbering.py)。"""
    rng, rp = _range("sold_at", date_from, date_to)
    cur.execute(
        "SELECT (sold_at AT TIME ZONE 'Asia/Bangkok')::date AS d, "
        "MIN(receipt_no) AS receipt_min, MAX(receipt_no) AS receipt_max, COUNT(*) AS n "
        "FROM pos_sales "
        "WHERE tenant_id=%s AND workspace_client_id=%s AND status='completed' AND sale_type='sale'"
        + rng
        + " GROUP BY 1 ORDER BY 1",
        list(base) + rp,
    )
    return [
        {
            "date": r["d"].isoformat(),
            "receipt_min": r["receipt_min"],
            "receipt_max": r["receipt_max"],
            "count": int(r["n"]),
        }
        for r in cur.fetchall()
    ]


def _full_invoices(cur, base, date_from, date_to) -> list:
    """全式税票附录:按原小票 sold_at 的曼谷月归属(join full_invoice_id),不按 issue_date——
    升级发生在下月的票也回收进原单所属月,同一笔金额只在这一份包里出现一次(见模块头注释)。"""
    tenant_id, workspace_client_id = base
    rng, rp = _range("s.sold_at", date_from, date_to)
    cur.execute(
        "SELECT d.doc_number, d.issue_date, d.source_receipt_no, d.buyer_name, d.buyer_tax_id, "
        "d.subtotal, d.discount_total, d.vat_amount, d.grand_total "
        "FROM sales_documents d "
        "JOIN pos_sales s ON s.tenant_id = d.tenant_id AND s.full_invoice_id = d.id "
        "WHERE d.tenant_id=%s AND s.tenant_id=%s AND s.workspace_client_id=%s "
        "AND d.status='issued'" + rng + " ORDER BY d.issue_date, d.doc_number",
        [tenant_id, tenant_id, workspace_client_id] + rp,
    )
    return [
        {
            "doc_number": r["doc_number"],
            "issued_date": r["issue_date"].isoformat() if r["issue_date"] else None,
            "source_receipt_no": r["source_receipt_no"],
            "buyer_name": r["buyer_name"],
            "buyer_tax_id": r["buyer_tax_id"],
            "subtotal": _money(r["subtotal"]),
            "discount_total": _money(r["discount_total"]),
            "vat_amount": _money(r["vat_amount"]),
            "gross": _money(r["grand_total"]),
        }
        for r in cur.fetchall()
    ]
