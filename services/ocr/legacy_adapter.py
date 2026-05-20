# -*- coding: utf-8 -*-
"""
services/ocr/legacy_adapter.py

Adapter: convert PipelineResult into the legacy dict shape expected by
existing app.py / email_ingest.py / recon_routes.py post-OCR code.

The legacy format originated from gemini_engine.recognize_pdf:
    {
        "pages": [
            {
                "page_number": int,
                "text": str,
                "lines": list,
                "fields": dict,           # ThaiInvoice fields
                "is_copy": bool,
                "elapsed_ms": int,
                "input_tokens": int,
                "output_tokens": int,
                "error": Optional[str],
            }
        ],
        "page_count": int,
        "elapsed_ms": int,
        "engine": str,
    }

Downstream code (insert_ocr_history, invoice_grouper, archive, ...) reads
this shape. Our PipelineResult / PipelinePageResult / ThaiInvoice all
have richer info but a different structure. This adapter is a thin pure
function — no business logic, no side effects.

The "_layer_chain", "_trigger_reasons", "_needs_manual_review" keys are
ADDED for debug / future use; legacy consumers ignore unknown keys.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .schemas import (
    PipelinePageResult,
    PipelineResult,
    ThaiInvoice,
)


def _invoice_to_legacy_fields(inv: ThaiInvoice) -> Dict[str, Any]:
    """Serialize ThaiInvoice into the legacy `fields` dict gemini_engine
    used to return.

    Adds the legacy `tax_ids` list (concat of seller_tax + buyer_tax,
    deduplicated) that some downstream consumers may read.
    """
    fields = inv.model_dump(mode="json")
    tax_ids: List[str] = []
    if inv.seller_tax:
        tax_ids.append(inv.seller_tax)
    if inv.buyer_tax and inv.buyer_tax not in tax_ids:
        tax_ids.append(inv.buyer_tax)
    fields["tax_ids"] = tax_ids
    return fields


def _page_to_legacy(p: PipelinePageResult) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "page_number": p.page_number,
        "page": p.page_number,  # alternate key used by some downstream consumers
        "text": "",  # not surfaced by pipeline; downstream rarely uses raw text
        "lines": [],
        "fields": _invoice_to_legacy_fields(p.invoice),
        "is_copy": bool(p.invoice.is_copy_or_duplicate),
        "is_duplicate": False,  # set later by invoice_grouper based on invoice_no dedup
        "elapsed_ms": int(p.total_ms),
        "input_tokens": int(p.layer2_input_tokens + p.layer3_input_tokens),
        "output_tokens": int(p.layer2_output_tokens + p.layer3_output_tokens),
        "error": p.error,
        # Debug / new pipeline metadata (downstream consumers ignore unknown keys)
        "_layer_chain": list(p.layer_chain),
        "_trigger_reasons": list(p.trigger_reasons),
        "_needs_manual_review": bool(p.needs_manual_review),
        "_layer1_avg_confidence": float(p.layer1_avg_confidence),
        # 2026-05-21 multi-schema refactor
        "_document_type": str(p.document_type),
        "_confidence_band": str(p.confidence_band),
        "_final_confidence": float(p.final_confidence),
        "_validation_warnings": list(p.validation_warnings),
    }
    # When a non-invoice document is present (GL / Bank / VAT / Table), expose
    # its normalized JSON so bank reconciliation can consume it directly.
    if p.document is not None:
        out["document"] = p.document.model_dump(mode="json")
    return out


def pipeline_result_to_legacy_dict(pr: PipelineResult) -> Dict[str, Any]:
    """Convert a PipelineResult into the legacy dict shape.

    Args:
        pr: a PipelineResult from services.ocr.pipeline.run_*

    Returns:
        legacy-shaped dict — drop-in for old `gemini_engine.recognize_pdf`
        callers + their downstream code (no changes needed)
    """
    # 2026-05-21 aggregate routing: worst-case bucket across all pages.
    # Order: needs_review > yellow_confirm > auto
    band_priority = {"needs_review": 2, "yellow_confirm": 1, "auto": 0}
    worst_band = "auto"
    for p in pr.pages:
        if band_priority.get(p.confidence_band, 0) > band_priority[worst_band]:
            worst_band = p.confidence_band

    return {
        "pages": [_page_to_legacy(p) for p in pr.pages],
        "page_count": int(pr.page_count),
        "elapsed_ms": int(pr.elapsed_ms),
        "engine": str(pr.engine),  # "pipeline_v1"
        # Pass-through aggregate cost so callers can prefer this over their
        # own token-based formula (which misses Vision per-page cost).
        "_pipeline_cost_thb": float(pr.estimated_cost_thb),
        # 2026-05-21 multi-schema refactor: top-level routing signal
        "_document_type": str(pr.pages[0].document_type) if pr.pages else "auto",
        "_confidence_band": worst_band,
        "_needs_review": worst_band == "needs_review",
    }
