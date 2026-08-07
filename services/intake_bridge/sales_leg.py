# -*- coding: utf-8 -*-
"""销项腿:OCR history → sales_documents(直接 issued,不占号)。

票已经在外部世界开出——会计手上早有这张票,系统的角色是【登记】不是【发号】。
services/sales/numbering.allocate 是给"从系统里开票"用的连号器,套在这里会把票面真实号码
作废重编,跟原始票据对不上。故本函数直接建 status='issued'、doc_number=票面号,唯一性靠
uq_sales_documents_ocr_history 之外的 uq_sales_doc_number(tenant_id, doc_type, doc_number)
天然兜底(撞号 → SkipConversion('duplicate'))。

头金额算法与 services/sales/document.create_draft 同一套(services.sales.totals.compute_
totals),不额外发明一套算法——票面 vat/subtotal 只用来决定 vat_rate,行金额仍由明细行
qty×unit_price 反算,与销项模块其余单据的算钱口径保持单一事实源。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import psycopg2

from services.erp.express_push.common import parse_invoice_date
from services.intake_bridge.errors import SkipConversion
from services.purchase.field_clean import (
    clean_address,
    clean_branch_no,
    clean_invoice_no,
    clean_seller,
    clean_tax_id,
)
from services.sales import buyer as buyer_mod
from services.sales.document_writes import replace_lines
from services.sales.totals import compute_totals

_DOC_TYPE = "tax_invoice"


def _to_decimal(v) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip()) if v not in (None, "") else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _build_lines(fields: dict) -> list:
    """票面明细 → compute_totals 输入行(description/qty/unit_price)。品名或金额任一缺 →
    该行不采信(不臆造 0 元行凑数),整单收敛不出行 → 调用方判 no_items。"""
    lines = []
    for it in fields.get("items") or []:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        qty = _to_decimal(it.get("qty")) or Decimal("1")
        price = _to_decimal(it.get("price"))
        sub = _to_decimal(it.get("subtotal"))
        if price <= 0 and sub > 0:
            price = (sub / qty) if qty else sub
        if price <= 0:
            continue
        lines.append({"description": name, "qty": qty, "unit_price": price, "vat_applicable": True})
    return lines


def _buyer_type(tax_id: str, name: str) -> str:
    if tax_id:
        return "company"
    if name:
        return "individual"
    return "anonymous"


def issue_from_history(cur, *, tenant_id, workspace_client_id, created_by, fields: dict) -> tuple:
    """登记销项单据(status='issued')。返回 (doc_id, doc_no)。"""
    doc_no = clean_invoice_no(fields.get("invoice_number"))
    if not doc_no:
        raise SkipConversion("no_doc_no")

    lines = _build_lines(fields)
    if not lines:
        raise SkipConversion("no_items")

    issue_date = parse_invoice_date(fields.get("date"))
    if issue_date is None:
        raise SkipConversion("no_date")

    vat = _to_decimal(fields.get("vat"))
    vat_rate = Decimal("7") if vat > 0 else Decimal("0")

    buyer_tax = clean_tax_id(fields.get("buyer_tax"))
    buyer_name = (
        clean_seller(fields.get("buyer_name")) or str(fields.get("buyer_name") or "").strip()
    )
    buyer_addr = clean_address(fields.get("buyer_addr"))
    buyer_branch_no = clean_branch_no(fields.get("buyer_branch"))
    buyer = buyer_mod.normalize_buyer(
        {
            "type": _buyer_type(buyer_tax, buyer_name),
            "name": buyer_name,
            "address": buyer_addr,
            "tax_id": buyer_tax,
            "branch_type": "branch" if buyer_branch_no else "hq",
            "branch_no": buyer_branch_no,
        }
    )
    cols = buyer_mod.to_columns(buyer)
    t = compute_totals(lines, vat_rate=vat_rate, wht_rate=0, price_includes_vat=False)

    try:
        cur.execute(
            "INSERT INTO sales_documents ("
            "tenant_id, doc_type, doc_number, status, seller_workspace_client_id, issue_date, "
            "issued_at, currency, subtotal, discount_total, header_discount_amount, "
            "header_discount_pct, price_includes_vat, vat_rate, vat_amount, wht_rate, "
            "wht_amount, grand_total, buyer_type, buyer_name, buyer_address, buyer_tax_id, "
            "buyer_branch_type, buyer_branch_no, created_by"
            ") VALUES (%s,%s,%s,'issued',%s,%s,now(),'THB',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
            "%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                tenant_id,
                _DOC_TYPE,
                doc_no,
                workspace_client_id,
                issue_date,
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
                cols["buyer_type"],
                cols["buyer_name"],
                cols["buyer_address"],
                cols["buyer_tax_id"],
                cols["buyer_branch_type"],
                cols["buyer_branch_no"],
                created_by,
            ),
        )
    except psycopg2.errors.UniqueViolation as e:
        raise SkipConversion("duplicate") from e
    doc_id = cur.fetchone()["id"]
    # 头金额已在上面的 INSERT 里一次写齐(与 write_header_totals 同口径的 t 字典),此处只补
    # 明细行;write_header_totals 是 update 场景用的整替写法,建单场景不必再调一次。
    replace_lines(cur, tenant_id, doc_id, t["lines"])
    return doc_id, doc_no
