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
# Multi-document Layer 2 schemas (2026-05-21 refactor)
# ============================================================
# Each non-invoice document type has its own row schema + document schema.
# The Layer 2 prompt is selected per document_type — see layer2_structure.py.
# Validators (validators.py) enforce that amount fields source from the
# correct columns (Debit/Credit for GL, deposit/withdrawal/balance for bank
# statement, etc.) — this is what prevents 6091-style description numbers
# from being mis-parsed as amounts.

class GLEntry(BaseModel):
    """One row of a General Ledger.

    Field-source contract (enforced by validators.validate_gl_entry):
    - debit / credit / balance MUST come from their respective columns
    - amount = debit if debit > 0 else credit (derived, signed)
    - direction = 'deposit' (debit > 0) | 'withdrawal' (credit > 0) | ''
    - description / voucher_no / account_code numbers (e.g. 6091, JV681130.1,
      QP10280137, 1112-07) MUST NOT appear in debit/credit/amount/balance
    """

    transaction_date: str = Field(default="", description="YYYY-MM-DD or empty")
    transaction_date_raw: str = Field(default="", description="date text as printed")
    voucher_no: str = Field(default="", description="voucher/document number, e.g. JV681130.1")
    account_code: str = Field(default="", description="account code, e.g. 1112-07")
    description: str = Field(
        default="",
        description="row description text — may contain numbers like '6091' "
        "that MUST NOT be treated as amounts",
    )
    debit: str = Field(default="", description="debit amount, number-as-string no commas; empty = no debit")
    credit: str = Field(default="", description="credit amount, number-as-string no commas; empty = no credit")
    amount: str = Field(
        default="",
        description="derived: debit if debit>0 else credit (number-as-string). "
        "Always sourced from Debit/Credit column — never description.",
    )
    direction: Literal["deposit", "withdrawal", ""] = Field(
        default="",
        description="'deposit' = bank goes up (debit>0); 'withdrawal' = bank goes down (credit>0)",
    )
    balance: str = Field(default="", description="running balance, number-as-string")

    # Provenance: where did each numeric field come from?
    debit_ref: Optional[FieldRef] = Field(default=None)
    credit_ref: Optional[FieldRef] = Field(default=None)
    balance_ref: Optional[FieldRef] = Field(default=None)

    raw_row_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="original column→cell mapping for audit / re-parse",
    )

    @field_validator(
        "transaction_date", "transaction_date_raw", "voucher_no",
        "account_code", "description", "debit", "credit", "amount", "balance",
        mode="before",
    )
    @classmethod
    def _coerce_gl_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def _coerce_direction(cls, v):
        if v is None or v == "":
            return ""
        if v in ("deposit", "withdrawal"):
            return v
        return ""

    @field_validator("raw_row_data", mode="before")
    @classmethod
    def _coerce_raw_row(cls, v):
        return {} if v is None else v


class GeneralLedgerDocument(BaseModel):
    """A GL document — many rows + summary metadata."""

    document_type: Literal["general_ledger"] = "general_ledger"
    period_start: str = Field(default="", description="YYYY-MM-DD or empty")
    period_end: str = Field(default="", description="YYYY-MM-DD or empty")
    account_name: str = Field(default="", description="bank account / GL account name")
    account_number: str = Field(default="", description="account number if printed")
    opening_balance: str = Field(default="")
    closing_balance: str = Field(default="")
    entries: List[GLEntry] = Field(default_factory=list)

    # v118.35.0.51 · 顶层 str 字段 None→"" 兜底(同 BankStatementDocument)
    @field_validator(
        "period_start", "period_end", "account_name", "account_number",
        "opening_balance", "closing_balance",
        mode="before",
    )
    @classmethod
    def _coerce_gl_doc_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, v):
        return [] if v is None else v


class BankStatementEntry(BaseModel):
    """One row of a Bank Statement.

    Field-source contract (enforced by validators.validate_bank_entry):
    - deposit / withdrawal / balance MUST come from their respective columns
    - amount = deposit if deposit > 0 else withdrawal
    - description / reference number text MUST NOT be assigned to amount
    """

    transaction_date: str = Field(default="")
    transaction_date_raw: str = Field(default="")
    description: str = Field(default="")
    reference: str = Field(default="", description="reference / transaction code")
    deposit: str = Field(default="", description="money in / เงินเข้า / credit column")
    withdrawal: str = Field(default="", description="money out / เงินออก / debit column")
    amount: str = Field(default="", description="derived: deposit if deposit>0 else withdrawal")
    direction: Literal["deposit", "withdrawal", ""] = Field(default="")
    balance: str = Field(default="", description="running balance")

    deposit_ref: Optional[FieldRef] = Field(default=None)
    withdrawal_ref: Optional[FieldRef] = Field(default=None)
    balance_ref: Optional[FieldRef] = Field(default=None)

    # v118.35.0.11 · raw_row_data 字段从 BankStatementEntry 删除 · 80+ 行流水 ×
    # 每行 ~150 token raw_row_data dict = 输出超 8192 → JSON 截断 · 改后 token
    # 预算砍掉一半 · 跟 max_output_tokens 16384 一起把截断率压到 0

    @field_validator(
        "transaction_date", "transaction_date_raw", "description",
        "reference", "deposit", "withdrawal", "amount", "balance",
        mode="before",
    )
    @classmethod
    def _coerce_bank_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def _coerce_direction(cls, v):
        if v is None or v == "":
            return ""
        if v in ("deposit", "withdrawal"):
            return v
        return ""


class BankStatementDocument(BaseModel):
    document_type: Literal["bank_statement"] = "bank_statement"
    bank_name: str = Field(default="")
    bank_code: str = Field(default="", description="kbank/bbl/scb/etc. or empty")
    account_name: str = Field(default="")
    account_number: str = Field(default="")
    account_last4: str = Field(default="")
    period_start: str = Field(default="")
    period_end: str = Field(default="")
    opening_balance: str = Field(default="")
    closing_balance: str = Field(default="")
    entries: List[BankStatementEntry] = Field(default_factory=list)

    # v118.35.0.51 · 顶层 str 字段 None→"" 兜底(Gemini 对续页/无期初常返 null · 否则 schema 崩)
    @field_validator(
        "bank_name", "bank_code", "account_name", "account_number", "account_last4",
        "period_start", "period_end", "opening_balance", "closing_balance",
        mode="before",
    )
    @classmethod
    def _coerce_doc_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, v):
        return [] if v is None else v


class VatReportEntry(BaseModel):
    """One row of a VAT report (销项/进项税报告)."""

    seq_no: str = Field(default="", description="row sequence number on report")
    transaction_date: str = Field(default="")
    transaction_date_raw: str = Field(default="")
    invoice_no: str = Field(default="")
    customer_name: str = Field(default="")
    customer_tax: str = Field(default="", description="13-digit Thai tax ID")
    customer_branch: str = Field(default="", description="买方分公司 / สำนักงานใหญ่ etc.")
    subtotal: str = Field(default="", description="净额, number-as-string")
    vat: str = Field(default="")
    total: str = Field(default="")

    invoice_no_ref: Optional[FieldRef] = Field(default=None)
    subtotal_ref: Optional[FieldRef] = Field(default=None)
    vat_ref: Optional[FieldRef] = Field(default=None)
    total_ref: Optional[FieldRef] = Field(default=None)

    raw_row_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "seq_no", "transaction_date", "transaction_date_raw", "invoice_no",
        "customer_name", "customer_tax", "customer_branch",
        "subtotal", "vat", "total",
        mode="before",
    )
    @classmethod
    def _coerce_vat_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("raw_row_data", mode="before")
    @classmethod
    def _coerce_raw_row(cls, v):
        return {} if v is None else v


class VatReportDocument(BaseModel):
    document_type: Literal["vat_report"] = "vat_report"
    seller_name: str = Field(default="", description="申报方公司名 (报告主体)")
    seller_tax: str = Field(default="")
    period_year: str = Field(default="", description="public year, e.g. '2026'")
    period_month: str = Field(default="", description="'01'..'12'")
    total_subtotal: str = Field(default="")
    total_vat: str = Field(default="")
    total_total: str = Field(default="")
    entries: List[VatReportEntry] = Field(default_factory=list)

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, v):
        return [] if v is None else v


class GenericTableDocument(BaseModel):
    """Fallback for unknown document types — just preserves the table grid."""

    document_type: Literal["generic_table"] = "generic_table"
    headers: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("headers", mode="before")
    @classmethod
    def _coerce_headers(cls, v):
        return [] if v is None else v

    @field_validator("rows", mode="before")
    @classmethod
    def _coerce_rows(cls, v):
        return [] if v is None else v


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

    # 2026-05-21 multi-schema refactor: per-field source provenance.
    # Optional — populated by Layer 2 / Layer 3 when the model returns
    # bbox / source_text info. Used by validators to enforce "amount only
    # from total/subtotal/vat columns".
    source_refs: Dict[str, FieldRef] = Field(
        default_factory=dict,
        description="map of field_name -> FieldRef (invoice_number / "
        "total_amount / subtotal / vat / seller_tax / buyer_tax / date)",
    )

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

    @field_validator("source_refs", mode="before")
    @classmethod
    def _coerce_source_refs(cls, v):
        return {} if v is None else v


NonInvoiceDocument = Union[
    GeneralLedgerDocument,
    BankStatementDocument,
    VatReportDocument,
    GenericTableDocument,
]


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
        default=0.0, ge=0.0, le=1.0,
        description="aggregate page confidence (min of critical-field confidences)",
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
