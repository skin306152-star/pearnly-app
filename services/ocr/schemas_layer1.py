# -*- coding: utf-8 -*-
"""OCR schemas · 基础原语层(REFACTOR-WA · R20 从 schemas.py 拆 · 0 逻辑改)
文档类型判别 BusinessDocumentType + 字段溯源 FieldRef + Vision 几何层级(Page/Block/Paragraph/Word/BoundingBox/Layer1Result)。
其余 schema 子模块(documents/invoice/results)从此 import 基础类型。schemas.py 门面 re-export。"""

from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator

# ============================================================
# Document-type discriminator (2026-05-21 multi-schema refactor)
# ============================================================
# Business entry points MUST pass one of these explicitly.
# - "auto"            : pipeline guesses (defaults to invoice for backwards compat)
# - "invoice"         : Thai tax invoice / receipt / credit note → ThaiInvoice
# - "bank_statement"  : bank deposit / withdrawal ledger        → BankStatementDocument
# - "general_ledger"  : accounting GL with debit/credit columns → GeneralLedgerDocument
# - "vat_report"      : 销项/进项 VAT report (国税局格式)         → VatReportDocument
# - "generic_table"   : any other tabular file                  → GenericTableDocument
#
# CRITICAL: see layer2_structure.py — when document_type != "invoice"/"auto"
# the prompt + output schema + validation rules are all different. e.g. GL files
# MUST NOT treat description column numbers (like 6091) as amounts.
BusinessDocumentType = Literal[
    "auto",
    "invoice",
    "bank_statement",
    "general_ledger",
    "vat_report",
    "generic_table",
]


class FieldRef(BaseModel):
    """Source-tracked field for audit + frontend highlight + anti-hallucination.

    Used on amount / date / tax_id / invoice_no / voucher_no / account_code
    fields so we can answer "where on the page did this number come from?".
    `source_column` is the table column header (Debit / Credit / Description / ...)
    — this is the critical field that lets validators reject numbers from
    Description columns being assigned to amount fields.
    """

    value: Optional[Union[str, float, int]] = Field(
        default=None,
        description="parsed value (string for text fields, float for numeric)",
    )
    source_text: str = Field(
        default="",
        description="exact text as printed on the page (preserves commas, ฿, etc.)",
    )
    source_page: int = Field(default=0, ge=0, description="1-based page number, 0 = unknown")
    source_bbox: Optional[List[float]] = Field(
        default=None,
        description="[x1, y1, x2, y2] absolute pixel coords, or None if unknown",
    )
    source_column: str = Field(
        default="",
        description="table column header where value was found "
        "(e.g. 'Debit' / 'Credit' / 'Description' / 'Voucher No.') — "
        "validators use this to reject mis-assigned amounts",
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("source_text", "source_column", "source_page", "confidence", mode="before")
    @classmethod
    def _null_to_default(cls, v, info):
        # Gemini returns explicit null for these on simple receipts (no table columns).
        # An explicit null bypasses Field(default=...), so coerce it back to the default —
        # null = "unknown", and downstream validators expect the typed default, not None.
        if v is None:
            return {"source_text": "", "source_column": "", "source_page": 0, "confidence": 0.0}[
                info.field_name
            ]
        return v


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
    confidence: float = Field(..., ge=0.0, le=1.0, description="Vision API confidence, 0-1")
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

    # 2026-05-21 multi-schema refactor: when the input is Excel/CSV/Word
    # (table_path layer 0), we preserve the structured rows here so Layer 2
    # can pick out columns by header rather than re-parsing free text.
    # None for image / scanned-PDF / vision-OCR pages.
    table_rows: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="structured table rows from Excel/CSV/Word direct read; "
        "each dict is {column_header: cell_value}. None when input was OCR'd.",
    )
    table_headers: Optional[List[str]] = Field(
        default=None,
        description="ordered list of column headers as printed",
    )


class Layer1Result(BaseModel):
    """Top-level result from layer 1 (Vision API).

    Returned by every public function in `services.ocr.layer1_vision`.
    Downstream layers (layer2_structure, layer3_fallback) consume this.
    """

    pages: List[Page]
    page_count: int = Field(..., ge=0)
    elapsed_ms: int = Field(
        ..., ge=0, description="wall-clock for all Vision calls + PDF rendering"
    )
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
