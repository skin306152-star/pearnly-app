# -*- coding: utf-8 -*-
"""OCR schemas · 各层结果包装(Layer2/Layer3/Pipeline 页结果与汇总)(REFACTOR-WA · R20 拆 · 0 逻辑改)。"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from services.ocr.schemas_layer1 import BusinessDocumentType
from services.ocr.schemas_documents import NonInvoiceDocument
from services.ocr.schemas_invoice import ThaiInvoice


class Layer2PageResult(BaseModel):
    """Layer 2 result for one Page from a Layer1Result.

    Wraps the extracted ThaiInvoice with per-call metadata so the caller
    (typically pipeline.py) can aggregate costs, retry counts, and
    diagnose slow / failing pages.

    2026-05-21 multi-schema refactor:
    - `invoice` always set (empty/is_not_invoice=True for non-invoice docs) for
      backwards compat with existing downstream consumers.
    - `document_type` carries the business-entry document type
      (auto/invoice/bank_statement/general_ledger/vat_report/generic_table).
    - `document` set for non-invoice doc types (GL/Bank/VAT/Table). None for
      invoice/auto. Carries the multi-row payload.
    """

    page_number: int = Field(..., ge=1, description="1-based, matches Layer1.Page.page_number")
    invoice: ThaiInvoice
    document_type: BusinessDocumentType = Field(
        default="invoice",
        description="business-entry document type (passed through from entry)",
    )
    document: Optional[NonInvoiceDocument] = Field(
        default=None,
        description="set for non-invoice document types (GL/Bank/VAT/Table). "
        "None for invoice / auto. Discriminated by document_type field.",
    )
    elapsed_ms: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    retries: int = Field(
        default=0,
        ge=0,
        description="number of JSON-parse retries actually consumed (0 = first call OK)",
    )
    skipped: bool = Field(
        default=False,
        description="true when page text was empty / too short and no API call was made",
    )
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="warnings from validators (e.g. 'amount 6091 sourced from "
        "description column — rejected')",
    )


class Layer2Result(BaseModel):
    """Aggregate layer 2 result for one document (= one Layer1Result)."""

    pages: List[Layer2PageResult]
    elapsed_ms: int = Field(default=0, ge=0, description="wall-clock for all pages")
    model: str = Field(default="", description="Gemini model identifier used")
    engine: str = Field(default="layer2_structure", description="for cost log / audit")


# ============================================================
# Layer 3 schemas (Flash visual fallback)
# ============================================================
class Layer3PageResult(BaseModel):
    """Layer 3 result for one Page that was flagged for visual review.

    Layer 3 is only invoked by pipeline.py for pages where the layer 1
    confidence / layer 2 output / amount math signal a problem. Successful
    refinement returns a corrected ThaiInvoice with the SAME schema as
    layer 2 (downstream is unaware of whether layer 3 ran).
    """

    page_number: int = Field(..., ge=1, description="1-based, matches Layer1.Page.page_number")
    invoice: ThaiInvoice = Field(..., description="corrected ThaiInvoice after visual refinement")
    elapsed_ms: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0, description="includes both text + image tokens")
    output_tokens: int = Field(default=0, ge=0)
    retries: int = Field(
        default=0,
        ge=0,
        description="JSON-parse retries actually consumed (0 = first call OK)",
    )
    trigger_reasons: List[str] = Field(
        default_factory=list,
        description="why pipeline.py called layer 3 (passed back in result for audit)",
    )
    model: str = Field(default="", description="Gemini model identifier used")


# ============================================================
# Pipeline schemas (layer 1 + 2 + 3 orchestration)
# ============================================================
class PipelinePageResult(BaseModel):
    """One page's end-to-end result through the full pipeline (L1 + L2 + maybe L3).

    Downstream consumers care about `invoice` (the final ThaiInvoice after
    all applicable layers) and `needs_manual_review`. The other fields are
    audit / cost / debugging info.

    2026-05-21 multi-schema refactor: when document_type != "invoice"/"auto",
    the meaningful payload is in `document` (GL / Bank / VAT / Table); the
    `invoice` field is left at its is_not_invoice=True default for back-compat.
    """

    page_number: int = Field(..., ge=1)
    invoice: ThaiInvoice = Field(..., description="final invoice, from L2 or L3")
    document_type: BusinessDocumentType = Field(default="invoice")
    document: Optional[NonInvoiceDocument] = Field(
        default=None,
        description="non-invoice payload (GL / Bank / VAT / Table) — set when "
        "document_type != invoice/auto",
    )

    layer_chain: List[str] = Field(
        default_factory=list,
        description='which layers ran, e.g. ["L1","L2"] or ["L1","L2","L3"] or '
        '["L1","L2","L3_failed"] (L3 was tried but failed; L2 result kept)',
    )
    trigger_reasons: List[str] = Field(
        default_factory=list,
        description="why L3 was called (empty list = L3 not invoked)",
    )

    layer1_avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    layer2_input_tokens: int = Field(default=0, ge=0)
    layer2_output_tokens: int = Field(default=0, ge=0)
    layer3_input_tokens: int = Field(default=0, ge=0)
    layer3_output_tokens: int = Field(default=0, ge=0)
    layer1_ms: int = Field(default=0, ge=0)
    layer2_ms: int = Field(default=0, ge=0)
    layer3_ms: int = Field(default=0, ge=0, description="0 if L3 didn't run")
    total_ms: int = Field(default=0, ge=0)

    needs_manual_review: bool = Field(
        default=False,
        description="true when L3 was triggered but failed (and we kept L2 result), "
        "OR (future) when final confidence is too low for auto-acceptance",
    )
    confidence_band: Literal["auto", "yellow_confirm", "needs_review"] = Field(
        default="auto",
        description="confidence routing bucket: "
        "auto (>=0.98 — can flow into ERP) / "
        "yellow_confirm (0.90-0.98 — user must click confirm) / "
        "needs_review (<0.90 — into manual review queue)",
    )
    final_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="aggregate page confidence (min of critical-field confidences)",
    )
    field_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="per-critical-field min L1 word confidence (invoice_number / "
        "total_amount / seller_tax / date) — feeds the review screen 'needs-check' "
        "field highlight; field absent from OCR text (hallucinated/missing) → 0.0",
    )
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="warnings from validators (mis-sourced amount, etc.)",
    )
    error: Optional[str] = Field(
        default=None,
        description="set if any layer hit a recoverable error (caller can still use invoice)",
    )


class PipelineResult(BaseModel):
    """End-to-end pipeline result for one document (= one PDF or one image)."""

    pages: List[PipelinePageResult]
    page_count: int = Field(..., ge=0)
    elapsed_ms: int = Field(..., ge=0)
    engine: str = Field(default="pipeline_v1")
    estimated_cost_thb: float = Field(
        default=0.0,
        ge=0.0,
        description="rough cost estimate in THB based on Vision pages + Gemini tokens",
    )
