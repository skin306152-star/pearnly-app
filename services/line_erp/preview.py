"""Shape OCR fields for the compact ERP LINE review card."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def _text(fields: dict, *keys: str) -> str:
    for key in keys:
        value = fields.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _money(value) -> str:
    try:
        return f"{Decimal(str(value or 0).replace(',', '')):,.2f}"
    except (InvalidOperation, ValueError):
        return str(value or "-")


def _item(row: dict) -> dict:
    qty = _text(row, "qty", "quantity") or "1"
    price = _text(row, "price", "unit_price")
    total = _text(row, "subtotal", "line_total", "amount")
    if not total and price:
        try:
            total = str(Decimal(qty) * Decimal(price))
        except (InvalidOperation, ValueError):
            total = ""
    return {
        "name": _text(row, "name", "description") or "-",
        "qty": qty,
        "price": _money(price) if price else "-",
        "total": _money(total) if total else "-",
        "kind": _text(row, "posting_kind"),
    }


def from_result(result: dict, mode: str) -> dict:
    pages = result.get("raw_pages") or []
    page = pages[0] if pages and isinstance(pages[0], dict) else {}
    fields = page.get("fields") or {}
    if not isinstance(fields, dict):
        fields = {}
    is_purchase = mode == "purchase"
    items = [_item(row) for row in fields.get("items") or [] if isinstance(row, dict)]
    return {
        "document_no": _text(fields, "invoice_number", "invoice_no"),
        "document_date": _text(fields, "date", "invoice_date"),
        "party_label": "ผู้ขาย" if is_purchase else "ผู้ซื้อ",
        "party_name": _text(
            fields,
            *(("seller_name", "vendor") if is_purchase else ("buyer_name", "customer_name")),
        ),
        "party_tax": _text(
            fields,
            *(("seller_tax", "seller_tax_id") if is_purchase else ("buyer_tax", "buyer_tax_id")),
        ),
        "party_branch": _text(
            fields,
            *(
                ("seller_branch", "seller_branch_no")
                if is_purchase
                else ("buyer_branch", "buyer_branch_no")
            ),
        ),
        "party_address": _text(
            fields,
            *(
                ("seller_addr", "seller_address")
                if is_purchase
                else ("buyer_addr", "buyer_address")
            ),
        ),
        "subtotal": _money(_text(fields, "subtotal")),
        "vat": _money(_text(fields, "vat", "vat_amount")),
        "total": _money(_text(fields, "total_amount", "grand_total")),
        "items": items,
        "item_count": len(items),
    }
