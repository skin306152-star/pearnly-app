# -*- coding: utf-8 -*-
"""
Shared OCR entrypoint helpers.

All user-facing OCR entrances must accept the same file families and use the
same credits pricing:
  - PDF/images: page pricing via kind="pdf"
  - Excel/CSV/Word/TXT: character pricing via kind="excel"
  - file-hash cache hits: no charge
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

import db
from services.ocr.pipeline import (
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TABLE_EXTENSIONS,
    run_on_image_bytes,
    run_on_pdf_bytes,
    run_on_table_bytes,
)

SUPPORTED_OCR_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS


def file_ext(filename: str) -> str:
    name = (filename or "").lower()
    return "." + name.rsplit(".", 1)[-1] if "." in name else ""


def is_supported_ocr_file(filename: str) -> bool:
    return file_ext(filename) in SUPPORTED_OCR_EXTENSIONS


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content or b"").hexdigest()


def get_cached_history(user: Dict[str, Any], file_hash: str) -> Optional[Dict[str, Any]]:
    return db.find_ocr_by_hash(
        str(user["id"]),
        file_hash,
        tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
    )


def billing_quote(
    user: Dict[str, Any],
    file_bytes: bytes,
    filename: str,
    max_pages: int = 50,
) -> Dict[str, Any]:
    """Return pricing metadata and current-balance allowance for one OCR file."""
    ext = file_ext(filename)
    if ext not in SUPPORTED_OCR_EXTENSIONS:
        return {"allowed": False, "error_code": "ocr.unsupported_format", "ext": ext}

    if ext in PDF_EXTENSIONS:
        from services.ocr.pdf_utils import count_pdf_pages

        page_count = int(count_pdf_pages(file_bytes) or 0)
        if page_count <= 0:
            return {"allowed": False, "error_code": "ocr.invalid_pdf", "ext": ext}
        if page_count > max_pages:
            return {
                "allowed": False,
                "error_code": "ocr.too_many_pages",
                "ext": ext,
                "max": max_pages,
                "actual": page_count,
            }
        kind = "pdf"
        units = page_count
    elif ext in IMAGE_EXTENSIONS:
        page_count = 1
        kind = "pdf"
        units = 1
    else:
        page_count = 1
        kind = "excel"
        units = db._excel_char_count_estimate(file_bytes, filename)

    tenant_id = str(user.get("tenant_id")) if user.get("tenant_id") else None
    billing = db.get_billing_status_combined(str(user["id"]), tenant_id)
    is_exempt = bool(billing.get("is_exempt"))
    if not billing.get("allowed") and not is_exempt:
        if kind == "pdf":
            estimated = float(
                db.estimate_pdf_cost_thb(billing.get("pages_used_this_month", 0), units)
            )
        else:
            estimated = float(db.estimate_excel_cost_thb(units))
        return {
            "allowed": False,
            "error_code": "insufficient_balance",
            "balance": billing.get("balance_thb", 0.0),
            "estimated_cost": estimated,
            "pages_used_this_month": billing.get("pages_used_this_month", 0),
            "kind": kind,
            "units": units,
            "page_count": page_count,
            "ext": ext,
            "is_exempt": is_exempt,
        }

    return {
        "allowed": True,
        "error_code": None,
        "kind": kind,
        "units": units,
        "page_count": page_count,
        "ext": ext,
        "is_exempt": is_exempt,
        "billing": billing,
    }


def run_pipeline_for_file(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str],
    max_pages: int = 50,
):
    ext = file_ext(filename)
    if ext in PDF_EXTENSIONS:
        return run_on_pdf_bytes(file_bytes, max_pages=max_pages, api_key=api_key)
    if ext in IMAGE_EXTENSIONS:
        return run_on_image_bytes(file_bytes, api_key=api_key)
    if ext in TABLE_EXTENSIONS:
        return run_on_table_bytes(file_bytes, filename=filename, api_key=api_key)
    raise ValueError(f"unsupported OCR file extension: {ext}")


def all_pages_not_invoice(pages: list) -> bool:
    if not pages:
        return False
    for p in pages:
        f = (p or {}).get("fields") or {}
        is_not = f.get("is_not_invoice")
        if isinstance(is_not, str):
            is_not = is_not.strip().lower() == "true"
        if not is_not:
            return False
    return True


def charge_successful_ocr(
    user: Dict[str, Any],
    quote: Dict[str, Any],
    history_id: Optional[str],
    description: str,
) -> None:
    if quote.get("is_exempt"):
        return
    kind = quote.get("kind")
    units = int(quote.get("units") or 0)
    tenant_id = str(user.get("tenant_id")) if user.get("tenant_id") else None
    if not kind or units <= 0 or not tenant_id:
        return
    db.charge_ocr_async(
        str(user["id"]),
        tenant_id,
        kind,
        units,
        history_id,
        description,
    )
