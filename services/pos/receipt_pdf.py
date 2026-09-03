# -*- coding: utf-8 -*-
"""POS 小票 PDF 数据组装(G1 · 版式在 receipt_render · docs/pos/04)。

单一职责:读单据/明细/收款/卖方/收银员 → 组 doc 给渲染叶子。合计按存额组装不重算
(票面自洽,防历史单据被事后价改动影响)。版式身份跟 sale.doc_kind 走(单据是历史
文件,账套后来改 VAT 状态不改变已开出票的身份);账套 VAT 状态只在开单时刻定号段
与 doc_kind(见 tax_policy.receipt_doc_kind)。
"""

from __future__ import annotations

from decimal import Decimal

from core.pos_api import PosError
from services.pos import receipt_render, receipt_settings, sales_store
from services.products.names import display_product_name

VAT_RATE = Decimal("7")  # 泰国标准 VAT(与 sale.VAT_RATE 同值 · 票面拆示用)

# 卖方块 = 账套主体:法定要素(名/址/税号)+ 品牌字段(logo/页脚)+ 合规字段(G1/G4)。
_SELLER_SQL = (
    "SELECT name, address, tax_id, phone, vat_registered, logo_url, footer_text, "
    "pos_register_no, pos_receipt_qr_enabled "
    "FROM workspace_clients WHERE tenant_id = %s AND id = %s"
)


def build_receipt_pdf(
    cur, *, tenant_id: str, workspace_client_id: int, sale_id: str, width_mm: int = 80
) -> bytes:
    sale = sales_store.get_sale(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
    )
    if not sale:
        raise PosError("pos.product_not_found", 404)
    cur.execute(
        "SELECT l.qty, l.unit_price, l.line_discount, l.line_total, "
        "l.product_name_snapshot, p.name_th, p.name_en, p.name_zh "
        "FROM pos_sale_lines l JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.sale_id = %s ORDER BY l.id",
        (tenant_id, sale_id),
    )
    doc_lines = [
        {
            "description": r.get("product_name_snapshot") or display_product_name(r),
            "qty": r["qty"],
            "unit_price": r["unit_price"],
            "discount": r["line_discount"],
            "line_total": r["line_total"],
        }
        for r in cur.fetchall()
    ]
    payments = sales_store.list_payments(cur, tenant_id=tenant_id, sale_id=sale_id)
    cur.execute(_SELLER_SQL, (tenant_id, sale["workspace_client_id"]))
    seller = dict(cur.fetchone() or {})
    doc_kind = "abbrev_tax_invoice" if sale["doc_kind"] == "abbrev_tax_invoice" else "receipt"
    doc = {
        "doc_kind": doc_kind,
        "doc_number": sale["receipt_no"],
        "issue_at": sale["sold_at"],
        "cashier_name": _cashier_name(cur, tenant_id=tenant_id, cashier_id=sale["cashier_id"]),
        "lines": doc_lines,
        "subtotal": sale["subtotal"],
        "discount_total": sale["discount_total"],
        "vat_rate": VAT_RATE,
        "vat_amount": sale["vat_amount"],
        "grand_total": sale["grand_total"],
        "price_includes_vat": bool(sale["price_includes_vat"]),
        "payments": [dict(p) for p in payments],
        "change_amount": sale["change_amount"],
        "qr_payload": _qr_payload(seller, doc_kind, workspace_client_id, sale["receipt_no"]),
    }
    seller_view = {
        "name": seller.get("name"),
        "address": seller.get("address"),
        "phone": seller.get("phone"),
        "tax_id": seller.get("tax_id"),
        "register_no": seller.get("pos_register_no"),
        "logo_url": seller.get("logo_url"),
        "footer_text": seller.get("footer_text"),
    }
    return receipt_render.render_receipt_pdf(doc, seller_view, width_mm=width_mm)


def _qr_payload(seller: dict, doc_kind: str, workspace_client_id: int, receipt_no) -> str | None:
    """G4 架子:账套开关开 + ABB 票才给码(未注册户开不了全式税票,码是死路;开关默认关,
    G2 通路落地随批开 · 见 receipt_settings)。"""
    if not seller.get("pos_receipt_qr_enabled") or doc_kind != "abbrev_tax_invoice":
        return None
    return receipt_settings.qr_payload(
        workspace_client_id=workspace_client_id, receipt_no=receipt_no or ""
    )


def _cashier_name(cur, *, tenant_id: str, cashier_id) -> str | None:
    """收银员名上票(SM 真票 Served By 对应项);单上没绑收银员则整行不印。"""
    if not cashier_id:
        return None
    cur.execute(
        "SELECT display_name FROM pos_cashiers WHERE tenant_id = %s AND id = %s",
        (tenant_id, cashier_id),
    )
    row = cur.fetchone()
    return row["display_name"] if row else None
