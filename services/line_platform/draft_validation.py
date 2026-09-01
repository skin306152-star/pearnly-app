"""Shared anomaly gate for Cowork and ERP LINE batch confirmation."""

from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _fields(record: dict) -> dict:
    pages = record.get("pages") or []
    if not pages or not isinstance(pages[0], dict):
        return {}
    fields = pages[0].get("fields") or {}
    return fields if isinstance(fields, dict) else {}


def document_issues(record: dict, direction: str, *, require_posting_kind: bool) -> list[str]:
    """Validate the canonical merged page used by downstream document conversion."""
    fields = _fields(record)
    issues: list[str] = []
    if fields.get("is_not_invoice") is True:
        issues.append("not_invoice")
    if fields.get("is_copy_or_duplicate") is True:
        issues.append("duplicate")
    if not _text(fields.get("date") or fields.get("invoice_date")):
        issues.append("date_required")
    if direction == "sales":
        if not _text(fields.get("invoice_number") or fields.get("invoice_no")):
            issues.append("invoice_number_required")
    else:
        if not _text(fields.get("seller_name") or fields.get("vendor")):
            issues.append("seller_name_required")
        if not _text(fields.get("total_amount") or fields.get("grand_total")):
            issues.append("total_amount_required")
    items = fields.get("items")
    if not isinstance(items, list) or not items:
        issues.append("items_required")
        return issues
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"item_invalid:{index}")
            continue
        if not _text(item.get("name") or item.get("description")):
            issues.append(f"item_name_required:{index}")
        if not _text(item.get("qty") or item.get("quantity")):
            issues.append(f"item_qty_required:{index}")
        if require_posting_kind and _text(item.get("posting_kind")).lower() not in {
            "stock",
            "service",
        }:
            issues.append(f"posting_kind_required:{index}")
    return issues


def batch_issues(
    records: list[dict], direction: str, *, require_posting_kind: bool
) -> dict[str, list[str]]:
    invalid = {}
    for record in records:
        issues = document_issues(record, direction, require_posting_kind=require_posting_kind)
        if issues:
            record_id = str(record.get("id") or record.get("history_id") or "")
            invalid[record_id] = issues
    return invalid


__all__ = ["batch_issues", "document_issues"]
