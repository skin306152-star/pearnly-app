# -*- coding: utf-8 -*-
"""POS 热敏小票 PDF 渲染(复用销项 pdf_thermal · 58/80mm · docs/pos/04)。

从 sale.py 抽出(单一职责):建单编排不该背着 PDF 版式。doc_type=receipt;合计按存额反推
以票面自洽(不重算,防历史单据被事后价改动影响)。
"""

from __future__ import annotations

from decimal import Decimal

from core.pos_api import PosError
from services.pos import sales_store

VAT_RATE = Decimal("7")  # 泰国标准 VAT(与 sale.VAT_RATE 同值 · 票面反推用)


def build_receipt_pdf(
    cur, *, tenant_id: str, workspace_client_id: int, sale_id: str, width_mm: int = 80
) -> bytes:
    from services.sales.pdf_thermal import render_thermal_pdf

    sale = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
    )
    if not sale:
        raise PosError("pos.product_not_found", 404)
    cur.execute(
        "SELECT l.qty, l.unit_price, l.line_total, p.name_th, p.name_en "
        "FROM pos_sale_lines l JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.sale_id = %s ORDER BY l.id",
        (tenant_id, sale_id),
    )
    doc_lines = [
        {
            "description": r["name_th"] or r["name_en"],
            "qty": r["qty"],
            "unit_price": r["unit_price"],
            "line_total": r["line_total"],
        }
        for r in cur.fetchall()
    ]
    payments = sales_store.list_payments(cur, tenant_id=tenant_id, sale_id=sale_id)
    grand = Decimal(str(sale["grand_total"]))
    vat = Decimal(str(sale["vat_amount"]))
    subtotal = grand if sale["price_includes_vat"] else (grand - vat)
    cur.execute(
        "SELECT name, address, tax_id, phone FROM workspace_clients WHERE tenant_id = %s AND id = %s",
        (tenant_id, sale["workspace_client_id"]),
    )
    seller = dict(cur.fetchone() or {})
    doc = {
        "doc_type": "receipt",
        "doc_number": sale["receipt_no"],
        "issue_date": sale["sold_at"],
        "lines": doc_lines,
        "subtotal": subtotal,
        "header_discount_amount": 0,
        "vat_rate": VAT_RATE,
        "vat_amount": vat,
        "wht_amount": 0,
        "grand_total": grand,
        "price_includes_vat": bool(sale["price_includes_vat"]),
        "currency": "THB",
        "payment_status": "paid",
        "payment_method": payments[0]["method"] if payments else None,
        "paid_amount": sale["paid_total"],
    }
    return render_thermal_pdf(doc, seller, {}, width_mm=width_mm)
