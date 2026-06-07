# -*- coding: utf-8 -*-
"""销项单据写入小工具(从 document.py 拆出 · 纯搬家 0 逻辑改 · 控 document.py <500)。

头部金额回写 + 明细行整替。均为叶子:收 (cur, tenant_id, doc_id, 数据),每条 WHERE tenant_id,
SQL 全参数化、列名硬编码。document.py 顶部 import 后调用点不变。
"""

from __future__ import annotations


def write_header_totals(cur, tenant_id: str, doc_id, t: dict) -> None:
    cur.execute(
        "UPDATE sales_documents SET subtotal=%s, discount_total=%s, header_discount_amount=%s, "
        "header_discount_pct=%s, price_includes_vat=%s, vat_rate=%s, vat_amount=%s, "
        "wht_rate=%s, wht_amount=%s, grand_total=%s, updated_at=now() "
        "WHERE tenant_id=%s AND id=%s",
        (
            t["subtotal"],
            t["discount_total"],
            t["header_discount_amount"],
            t["header_discount_pct"],
            t["price_includes_vat"],
            t["vat_rate"],
            t["vat_amount"],
            t["wht_rate"],
            t["wht_amount"],
            t["grand_total"],
            tenant_id,
            doc_id,
        ),
    )


def replace_lines(cur, tenant_id: str, doc_id, lines: list) -> None:
    cur.execute(
        "DELETE FROM sales_document_lines WHERE tenant_id=%s AND document_id=%s",
        (tenant_id, doc_id),
    )
    for ln in lines:
        cur.execute(
            "INSERT INTO sales_document_lines (tenant_id, document_id, line_no, product_id, "
            "description, qty, unit_price, discount, discount_pct, vat_applicable, line_total) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant_id,
                doc_id,
                ln["line_no"],
                ln["product_id"],
                ln["description"],
                ln["qty"],
                ln["unit_price"],
                ln["discount"],
                ln["discount_pct"],
                ln["vat_applicable"],
                ln["line_total"],
            ),
        )
