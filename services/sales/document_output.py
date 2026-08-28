"""Serialize sales documents for the HTTP API."""

from __future__ import annotations

from typing import Optional


def _money(value) -> Optional[str]:
    return str(value) if value is not None else None


def _line(line: dict) -> dict:
    return {
        "line_no": line.get("line_no"),
        "product_id": str(line["product_id"]) if line.get("product_id") else None,
        "description": line.get("description"),
        "item_type": line.get("item_type") or "goods",
        "qty": _money(line.get("qty")),
        "unit_price": _money(line.get("unit_price")),
        "discount": _money(line.get("discount")),
        "discount_pct": _money(line.get("discount_pct")),
        "vat_applicable": bool(line.get("vat_applicable")),
        "line_total": _money(line.get("line_total")),
    }


def serialize(document: dict) -> dict:
    return {
        "id": str(document["id"]),
        "doc_type": document.get("doc_type"),
        "doc_number": document.get("doc_number"),
        "client_id": int(document["client_id"]) if document.get("client_id") is not None else None,
        "seller_workspace_client_id": (
            int(document["seller_workspace_client_id"])
            if document.get("seller_workspace_client_id") is not None
            else None
        ),
        "issue_date": document["issue_date"].isoformat() if document.get("issue_date") else None,
        "status": document.get("status"),
        "currency": document.get("currency"),
        "subtotal": _money(document.get("subtotal")),
        "discount_total": _money(document.get("discount_total")),
        "header_discount_amount": _money(document.get("header_discount_amount")),
        "header_discount_pct": _money(document.get("header_discount_pct")),
        "vat_rate": _money(document.get("vat_rate")),
        "vat_amount": _money(document.get("vat_amount")),
        "price_includes_vat": bool(document.get("price_includes_vat")),
        "copies_layout": document.get("copies_layout") or "separate",
        "paper_size": document.get("paper_size") or "A4",
        "doc_language": document.get("doc_language") or "th_en",
        "wht_rate": _money(document.get("wht_rate")),
        "wht_amount": _money(document.get("wht_amount")),
        "grand_total": _money(document.get("grand_total")),
        "issued_at": document["issued_at"].isoformat() if document.get("issued_at") else None,
        "pdf_sha256": document.get("pdf_sha256"),
        "references_document_id": (
            str(document["references_document_id"])
            if document.get("references_document_id")
            else None
        ),
        "ocr_history_id": (
            str(document["ocr_history_id"]) if document.get("ocr_history_id") else None
        ),
        "source": document.get("source") or "manual",
        "posting_kind": document.get("posting_kind"),
        "push_status": document.get("push_status") or "not_pushed",
        "push_endpoints": document.get("push_endpoints") or [],
        "reference_reason": document.get("reference_reason"),
        "due_date": document["due_date"].isoformat() if document.get("due_date") else None,
        "payment_terms": document.get("payment_terms"),
        "buyer": {
            "type": document.get("buyer_type"),
            "name": document.get("buyer_name"),
            "address": document.get("buyer_address"),
            "tax_id": document.get("buyer_tax_id"),
            "branch_type": document.get("buyer_branch_type"),
            "branch_no": document.get("buyer_branch_no"),
        },
        "payment": {
            "status": document.get("payment_status"),
            "paid_amount": _money(document.get("paid_amount")),
            "method": document.get("payment_method"),
            "date": (
                document["payment_date"].isoformat() if document.get("payment_date") else None
            ),
        },
        "approval": {
            "approved_by": document.get("approved_by"),
            "approved_at": (
                document["approved_at"].isoformat() if document.get("approved_at") else None
            ),
            "rejected_reason": document.get("rejected_reason"),
        },
        "created_at": document["created_at"].isoformat() if document.get("created_at") else None,
        "lines": [_line(line) for line in document.get("lines", [])],
    }
