# -*- coding: utf-8 -*-
"""
services/ocr/schemas.py

Pydantic schemas shared across the new OCR pipeline layers.

Layer 1 (Vision API) produces the page/block/paragraph/word hierarchy.
Layer 2 (Flash-Lite) produces ThaiInvoice fields (the `seller_tax` /
`buyer_tax` naming per migration-plan.md decision 2 keeps compatibility
with existing downstream consumers: mrerp_xlsx_generator, archive.py,
xero_pusher.py, etc.).
Layer 3 (Flash visual fallback) will refine ThaiInvoice when layer 2 + 1
confidence is low (added later).

Public symbols:
    Layer 1: BoundingBox, Word, Paragraph, Block, Page, Layer1Result
    Layer 2: LineItem, ThaiInvoice, Layer2PageResult, Layer2Result
"""

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    """4-vertex bounding polygon for a word / paragraph / block.

    Vision API returns vertices in TL / TR / BR / BL order. Coordinates are
    absolute pixel positions in the rendered image (for PDF, this is the
    per-page rendered image; DPI is recorded on the parent Layer1Result).
    """

    vertices: List[Tuple[int, int]] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="4 (x, y) vertices in TL/TR/BR/BL order, absolute pixels",
    )


class Word(BaseModel):
    """A single OCR-detected word with its confidence and bbox."""

    text: str = Field(..., description="word text (concatenated symbols)")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Vision API confidence, 0-1"
    )
    bbox: BoundingBox


class Paragraph(BaseModel):
    """A paragraph — group of words on roughly the same line / block.

    `text` is a simple space-joined concatenation of word.text; this is
    different from `Page.full_text` which preserves Vision's original
    whitespace layout (line breaks etc).
    """

    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    words: List[Word]


class Block(BaseModel):
    """A block — group of paragraphs forming a logical section."""

    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    paragraphs: List[Paragraph]


class Page(BaseModel):
    """A single page result from Vision API.

    For a PDF input, one Page per processed PDF page (1-based numbering).
    For an image input, exactly one Page with page_number=1.
    """

    page_number: int = Field(..., ge=1, description="1-based page index")
    width: int = Field(..., ge=0, description="image width in pixels")
    height: int = Field(..., ge=0, description="image height in pixels")
    full_text: str = Field(
        ...,
        description="full extracted text preserving Vision's original layout "
        "(line breaks, paragraph separators)",
    )
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="unweighted mean of all word confidences on this page; "
        "0.0 when page contains no words",
    )
    blocks: List[Block]


class Layer1Result(BaseModel):
    """Top-level result from layer 1 (Vision API).

    Returned by every public function in `services.ocr.layer1_vision`.
    Downstream layers (layer2_structure, layer3_fallback) consume this.
    """

    pages: List[Page]
    page_count: int = Field(..., ge=0)
    elapsed_ms: int = Field(..., ge=0, description="wall-clock for all Vision calls + PDF rendering")
    engine: str = Field(default="layer1_vision", description="for cost log / audit")
    language_hints: List[str] = Field(
        default_factory=lambda: ["th", "en"],
        description="Vision API language hints used for this run",
    )
    dpi: int = Field(
        default=0,
        ge=0,
        description="DPI used to render PDF pages; 0 when input was already an image",
    )


# ============================================================
# Layer 2 schemas (Flash-Lite field extraction)
# ============================================================
def _coerce_to_str(v):
    """Permissive coercion for required string fields: None -> "", numbers -> str."""
    if v is None:
        return ""
    if isinstance(v, bool):
        # JSON booleans are not expected for string fields; stringify defensively
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return v


def _coerce_to_optional_str(v):
    """Coercion for Optional[str] fields: None stays None, numbers -> str,
    empty strings -> None (treats "" same as missing for consumers that
    do truthiness checks)."""
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    if isinstance(v, str) and not v:
        return None
    return v


class LineItem(BaseModel):
    """A single line item in a Thai tax invoice.

    All numeric-looking fields stay as strings (no Decimal) for compatibility
    with the existing gemini_engine output schema and downstream consumers
    (mrerp_xlsx_generator reads these as strings; converting now would
    cascade-break consumers).
    """

    name: str = Field(default="", description="item description as printed")
    qty: str = Field(default="", description="quantity, number-as-string")
    price: str = Field(default="", description="unit price, number-as-string, no commas")
    subtotal: str = Field(default="", description="line subtotal, number-as-string, no commas")

    # Gemini may return null / number for any of these; coerce defensively.
    _str_coerce = field_validator("name", "qty", "price", "subtotal", mode="before")(
        _coerce_to_str
    )


class ThaiInvoice(BaseModel):
    """Structured Thai tax invoice fields, produced by layer 2.

    Field naming uses `_tax` suffix (NOT `_tax_id`) per migration-plan
    decision 2; this matches the existing gemini_engine output schema and
    keeps all downstream consumers working unchanged.

    Default values are chosen so that an empty / missing field passes
    validation while remaining distinguishable from "explicitly null":
        - strings  -> ""  (empty string)
        - optional -> None (Gemini was unable to extract)
        - lists    -> []
        - bools    -> False

    All numeric fields are strings (no commas, no currency) to match the
    existing schema; pipeline.py / validators.py converts to Decimal when
    arithmetic validation is needed.
    """

    document_type: Literal["tax_invoice", "receipt", "credit_note", "other"] = Field(
        default="tax_invoice",
        description="document type classification",
    )
    is_not_invoice: bool = Field(
        default=False,
        description="true when the text is clearly NOT an invoice (letter, "
        "contract, blank page, etc.)",
    )
    is_copy_or_duplicate: bool = Field(
        default=False,
        description="true when text contains สำเนา / COPY / DUPLICATE markers",
    )

    invoice_number: Optional[str] = Field(default=None)
    date: Optional[str] = Field(
        default=None,
        description="YYYY-MM-DD Gregorian (Buddhist year converted -543 by Gemini)",
    )
    date_raw: str = Field(default="", description="date text exactly as printed")

    seller_name: str = Field(default="")
    seller_tax: str = Field(default="", description="13-digit Thai tax ID or empty")
    seller_addr: str = Field(default="")

    buyer_name: str = Field(default="")
    buyer_tax: str = Field(default="", description="13-digit Thai tax ID or empty")
    buyer_addr: str = Field(default="")

    subtotal: str = Field(default="", description="number-as-string, no commas")
    vat: str = Field(default="", description="number-as-string, no commas")
    wht_rate: str = Field(default="", description='number only, e.g. "3" not "3%"')
    wht_amount: str = Field(default="", description="number-as-string, no commas")
    total_amount: Optional[str] = Field(default=None)

    items: List[LineItem] = Field(default_factory=list)

    notes: str = Field(default="", description="remark text")
    category: str = Field(default="", description="3-5 char summary in items' language")

    # ---- Defensive coercion: Gemini sometimes returns null for empty fields
    # or number for a number-as-string. Without these, valid Gemini output
    # fails strict pydantic validation and triggers the layer 2 retry budget
    # for no reason.
    _str_coerce = field_validator(
        "date_raw",
        "seller_name",
        "seller_tax",
        "seller_addr",
        "buyer_name",
        "buyer_tax",
        "buyer_addr",
        "subtotal",
        "vat",
        "wht_rate",
        "wht_amount",
        "notes",
        "category",
        mode="before",
    )(_coerce_to_str)

    _opt_str_coerce = field_validator(
        "invoice_number",
        "date",
        "total_amount",
        mode="before",
    )(_coerce_to_optional_str)

    @field_validator("is_not_invoice", "is_copy_or_duplicate", mode="before")
    @classmethod
    def _coerce_bool(cls, v):
        """Gemini sometimes returns null for booleans; treat null as False."""
        return False if v is None else v

    @field_validator("items", mode="before")
    @classmethod
    def _coerce_items(cls, v):
        """Gemini may return null for empty items list."""
        return [] if v is None else v

    @field_validator("document_type", mode="before")
    @classmethod
    def _coerce_document_type(cls, v):
        """Gemini may return null or an unexpected value; fall back to tax_invoice."""
        if v is None:
            return "tax_invoice"
        allowed = {"tax_invoice", "receipt", "credit_note", "other"}
        return v if v in allowed else "other"


class Layer2PageResult(BaseModel):
    """Layer 2 result for one Page from a Layer1Result.

    Wraps the extracted ThaiInvoice with per-call metadata so the caller
    (typically pipeline.py) can aggregate costs, retry counts, and
    diagnose slow / failing pages.
    """

    page_number: int = Field(..., ge=1, description="1-based, matches Layer1.Page.page_number")
    invoice: ThaiInvoice
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
    """

    page_number: int = Field(..., ge=1)
    invoice: ThaiInvoice = Field(..., description="final invoice, from L2 or L3")

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
