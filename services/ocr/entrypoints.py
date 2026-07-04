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

from core import db
from services.ocr.pipeline import IMAGE_EXTENSIONS, PDF_EXTENSIONS, TABLE_EXTENSIONS

SUPPORTED_OCR_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS


def file_ext(filename: str) -> str:
    name = (filename or "").lower()
    return "." + name.rsplit(".", 1)[-1] if "." in name else ""


def is_supported_ocr_file(filename: str) -> bool:
    return file_ext(filename) in SUPPORTED_OCR_EXTENSIONS


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content or b"").hexdigest()


def get_cached_history(
    user: Dict[str, Any],
    file_hash: str,
    workspace_client_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    # PO-4 · 文件指纹缓存按套账隔离:同文件在另一套账上传不复用本套账结果(跨套账不串)。
    return db.find_ocr_by_hash(
        str(user["id"]),
        file_hash,
        tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
        workspace_client_id=workspace_client_id,
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


def policy_context_from_billing(billing_or_quote: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract OCR engine policy inputs from an existing billing lookup."""
    source = billing_or_quote or {}
    billing = source.get("billing") if isinstance(source.get("billing"), dict) else source
    subscription = (billing or {}).get("subscription") or {}
    return {
        "plan_code": subscription.get("plan_code"),
        "is_exempt": bool(source.get("is_exempt") or (billing or {}).get("is_exempt")),
    }


def run_pipeline_for_file(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str],
    max_pages: int = 50,
    *,
    document_type: str = "auto",
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    user_type: Optional[str] = None,
):
    """Facade → controller(task=invoice)· 派发逻辑在 handlers/invoice.py。"""
    from services.ocr import controller
    from services.ocr.contracts import OcrRequest

    return controller.run(
        OcrRequest(
            task="invoice",
            file_bytes=file_bytes,
            filename=filename,
            api_key=api_key,
            plan_code=plan_code,
            is_exempt=is_exempt,
            user_type=user_type,
            options={"max_pages": max_pages, "document_type": document_type},
        )
    ).data


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
