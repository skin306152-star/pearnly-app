# -*- coding: utf-8 -*-
"""POS 交易明细日志(POS 项目 · 老板后台)。

跟 services/pos/report.py 是两个不同粒度:report=聚合数字,这里=逐笔流水(谁/几点/卖了什么/
哪个班次)。行内 items/qty_total/method 用相关子查询取(标量·每行一个值),不 join lines/
payments 进主查询——那样会因一对多复制主行,见 report.py 同一条踩过的坑。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from services.pos import sheets_labels

_ROW_SQL = """
SELECT s.id, s.receipt_no, s.sold_at, s.cashier_id, c.display_name AS cashier_name,
       s.shift_id, sh.opened_at AS shift_opened_at, sh.closed_at AS shift_closed_at,
       s.subtotal, s.discount_total, s.vat_amount, s.grand_total,
       s.paid_total, s.change_amount,
       (SELECT string_agg(p2.name_th || ' x' || l.qty, ', ' ORDER BY l.id)
        FROM pos_sale_lines l JOIN products p2 ON p2.id = l.product_id
        WHERE l.tenant_id = s.tenant_id AND l.sale_id = s.id) AS items,
       (SELECT COALESCE(SUM(l.qty), 0) FROM pos_sale_lines l
        WHERE l.tenant_id = s.tenant_id AND l.sale_id = s.id) AS qty_total,
       (SELECT p.method FROM pos_payments p
        WHERE p.tenant_id = s.tenant_id AND p.sale_id = s.id ORDER BY p.id LIMIT 1) AS method
FROM pos_sales s
LEFT JOIN pos_cashiers c ON c.id = s.cashier_id
LEFT JOIN pos_shifts sh ON sh.id = s.shift_id
WHERE s.tenant_id = %s AND s.workspace_client_id = %s
  AND s.status = 'completed' AND s.sale_type = 'sale'
"""

_EXPORT_CAP = 5000


def _range(date_from: Optional[date], date_to: Optional[date]) -> tuple[str, list]:
    """s.sold_at 时间窗口(半开 [from, to+1天)·含 to 当天)。同 report.py 口径。"""
    clause, params = "", []
    if date_from:
        clause += " AND s.sold_at >= %s"
        params.append(date_from)
    if date_to:
        clause += " AND s.sold_at < %s"
        params.append(date_to + timedelta(days=1))
    return clause, params


def _iso(v) -> str:
    return v.isoformat() if v else ""


def _money(v) -> str:
    return str(Decimal(str(v)) if v is not None else Decimal("0"))


def _row_to_item(r: dict, lang: str) -> dict:
    return {
        "id": str(r["id"]),
        "receipt_no": r["receipt_no"],
        "sold_at": _iso(r["sold_at"]),
        "cashier_id": str(r["cashier_id"]) if r["cashier_id"] else None,
        "cashier_name": r["cashier_name"] or "",
        "items": r["items"] or "",
        "qty_total": _money(r["qty_total"]),
        "subtotal": _money(r["subtotal"]),
        "discount_total": _money(r["discount_total"]),
        "vat_amount": _money(r["vat_amount"]),
        "grand_total": _money(r["grand_total"]),
        "paid_total": _money(r["paid_total"]),
        "change_amount": _money(r["change_amount"]),
        "method": sheets_labels.method_label(r["method"] or "", lang),
        "shift_id": str(r["shift_id"]) if r["shift_id"] else None,
        "shift_opened_at": _iso(r["shift_opened_at"]),
        "shift_closed_at": _iso(r["shift_closed_at"]),
    }


def list_sales(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    cashier_id: Optional[str] = None,
    lang: str = "th",
    limit: int = 200,
    offset: int = 0,
) -> dict:
    """分页明细(默认按售出时间倒序)+ 同筛选条件下的总数(供翻页/"共 N 笔"提示)。"""
    rng, rp = _range(date_from, date_to)
    cashier_clause, cashier_params = ("", [])
    if cashier_id:
        cashier_clause, cashier_params = " AND s.cashier_id = %s", [cashier_id]

    base = (tenant_id, workspace_client_id)
    cur.execute(
        "SELECT COUNT(*) AS n FROM pos_sales s WHERE s.tenant_id=%s AND s.workspace_client_id=%s "
        "AND s.status='completed' AND s.sale_type='sale'" + rng + cashier_clause,
        list(base) + rp + cashier_params,
    )
    total = int((cur.fetchone() or {}).get("n") or 0)

    cur.execute(
        _ROW_SQL + rng + cashier_clause + " ORDER BY s.sold_at DESC LIMIT %s OFFSET %s",
        list(base) + rp + cashier_params + [int(limit), int(offset)],
    )
    lg = sheets_labels.norm_lang(lang)
    return {"items": [_row_to_item(r, lg) for r in cur.fetchall()], "total": total}


def export_rows(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    cashier_id: Optional[str] = None,
    lang: str = "th",
) -> list:
    """导出用:同一份筛选,不分页,封顶 5000 行(同 admin_logs 导出先例·防失控大文件)。"""
    result = list_sales(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_from=date_from,
        date_to=date_to,
        cashier_id=cashier_id,
        lang=lang,
        limit=_EXPORT_CAP,
        offset=0,
    )
    return result["items"]
