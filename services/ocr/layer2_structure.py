# -*- coding: utf-8 -*-
"""
services/ocr/layer2_structure.py

Layer 2 of the new OCR pipeline: Gemini Flash-Lite field extraction.

Takes the text output from layer 1 (Vision API) and uses Gemini 2.5 Flash-Lite
to map that text into structured `ThaiInvoice` fields. This layer is text-only
by design: character recognition is layer 1's job; layer 2 just "reads Thai
and fills the form".

Key design choices:
- Text-only input (no images sent to Gemini at this layer)
- Strict JSON schema in prompt + `response_mime_type="application/json"`
- temperature=0.0 for deterministic field extraction
- 1 retry on JSON parse failure (per user spec, then ValueError)
- Per-page extraction; aggregation across pages is pipeline.py's job
- Lazy singleton model cache (per api_key + model_name combo)
- No business logic, no fallback to other layers — those belong in pipeline.py

Auth:
- Reads env GOOGLE_API_KEY first, falls back to GEMINI_API_KEY for compat
  with existing Pearnly .env

Public API:
    extract_from_text(text, ...)         -> ThaiInvoice
    extract_from_page(page, ...)         -> Layer2PageResult  (with metadata)
    extract_from_layer1(result, ...)     -> Layer2Result      (all pages)

Custom exceptions (all subclass Layer2Error, parallel to layer1):
    Layer2AuthError       (missing / invalid API key, NOT retryable)
    Layer2QuotaError      (rate limit / quota, retry after backoff)
    Layer2TransientError  (timeout / 5xx / network, potentially retryable)
    Layer2Error           (everything else / unknown)

ValueError is raised SEPARATELY for JSON-related failures after the retry
budget is exhausted (per user spec: "Gemini 返回非法 JSON → 重试 1 次 →
仍失败抛 ValueError 让上层处理").
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Optional, Tuple

from pydantic import ValidationError

from .schemas import (
    BankStatementDocument,
    BusinessDocumentType,
    GeneralLedgerDocument,
    GenericTableDocument,
    Layer1Result,
    Layer2PageResult,
    Layer2Result,
    Page,
    ThaiInvoice,
    VatReportDocument,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================
DEFAULT_MODEL = os.environ.get("OCR_FLASHLITE_MODEL", "gemini-2.5-flash-lite")
DEFAULT_MAX_RETRIES = 1
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_TEMPERATURE = 0.0
# v118.35.0.11 · 8192 → 16384 · raw_row_data 字段从 BankStatementEntry schema
# 物理删除后 · 单 entry token 砍掉一半 · 但极大流水 Excel(80-100 行交易) +
# 长描述字段 还是有可能撞 8192 · 16384 给足空间.
DEFAULT_MAX_OUTPUT_TOKENS = 16384

# v118.35.0.11 · 重试 prompt 精简成最小必要字段 · 针对 bank_statement 截断场景
_RETRY_TRIM_HINT = (
    "\n\nIMPORTANT — your previous response was truncated mid-string and "
    "could not be parsed as JSON. On this retry, output ONLY the core "
    "fields per entry: date, description, amount, balance. "
    "OMIT all `raw_row_data` / `*_ref` / source provenance objects. "
    "Reply with a single valid JSON object, no fences, no markdown."
)

# Skip Gemini call if text is shorter than this (likely garbage / blank page)
MIN_TEXT_LENGTH = 20

# Truncate input text to bound token cost on accidentally-large pages.
# Real Thai invoices fit comfortably in 5000-8000 chars; 30000 is a safety net.
MAX_TEXT_LENGTH = 30000


# ============================================================
# Exception hierarchy
# ============================================================
class Layer2Error(Exception):
    """Base exception for layer 2 errors. Catch this for generic dispatch."""


class Layer2AuthError(Layer2Error):
    """Missing or invalid GOOGLE_API_KEY / GEMINI_API_KEY (NOT retryable)."""


class Layer2QuotaError(Layer2Error):
    """Quota or rate-limit exceeded. Retry after backoff."""


class Layer2TransientError(Layer2Error):
    """Network / timeout / 5xx. Potentially retryable."""


# ============================================================
# Per-document-type prompts (2026-05-21 multi-schema refactor)
# ============================================================
# Each business document type gets its own prompt + output schema. The
# CRITICAL design rule: GL files MUST only treat Debit/Credit column values
# as amounts. Description-column numbers (e.g. '6091', 'JV681130.1',
# '1112-07', 'QP10280137') MUST NOT be parsed as amount/debit/credit.
# Same principle for Bank Statements: only deposit/withdrawal/balance.

_GL_SYSTEM_PROMPT = """You are an accountant reading a General Ledger (GL) report. The input is plain text extracted from a GL print-out or spreadsheet. Your job: parse each transaction row into a strict JSON schema.

Output ONE JSON object (no markdown fences, no prose, just JSON):

{
  "document_type": "general_ledger",
  "period_start": "YYYY-MM-DD or empty string",
  "period_end": "YYYY-MM-DD or empty string",
  "account_name": "bank/GL account name or empty",
  "account_number": "account number or empty",
  "opening_balance": "number-as-string, no commas, or empty",
  "closing_balance": "number-as-string, no commas, or empty",
  "entries": [
    {
      "transaction_date": "YYYY-MM-DD or empty",
      "transaction_date_raw": "date text as printed",
      "voucher_no": "voucher / journal / document number (e.g. JV681130.1, QP10280137) or empty",
      "account_code": "account code (e.g. 1112-07) or empty",
      "description": "row description text (Thai or English) — may contain digits like '6091' which are NOT amounts",
      "debit": "number-as-string from the Debit / เดบิต column, no commas, empty if no debit",
      "credit": "number-as-string from the Credit / เครดิต column, no commas, empty if no credit",
      "amount": "debit if debit>0 else credit (derived number-as-string)",
      "direction": "deposit | withdrawal | empty",
      "balance": "running balance from the Balance / ยอดคงเหลือ column, or empty",
      "debit_ref":   {"value": "number", "source_text": "as printed", "source_column": "Debit"   } or null,
      "credit_ref":  {"value": "number", "source_text": "as printed", "source_column": "Credit"  } or null,
      "balance_ref": {"value": "number", "source_text": "as printed", "source_column": "Balance" } or null,
      "raw_row_data": {"column header": "cell text"}
    }
  ]
}

PROVENANCE — MANDATORY:
For every non-empty debit / credit / balance you fill, ALSO fill the matching
*_ref object with `source_column` set to the EXACT column-header text where
you read that number from (e.g. "Debit", "เดบิต", "Credit", "เครดิต",
"Balance", "ยอดคงเหลือ"). If you read the number from a Description /
Voucher No. / Account Code column, FILL source_column with that header
EXACTLY — downstream validators will then reject and clear the field. Do NOT
guess or omit source_column when the value is non-empty.

CRITICAL RULES — VIOLATIONS ARE BUGS:

1. AMOUNT SOURCING (most important):
   - debit / credit / balance / amount fields MAY ONLY contain values from the
     Debit / Credit / Balance columns of the GL.
   - The following columns are NEVER amounts: Description / รายการ / คำอธิบาย,
     Account Code / รหัสบัญชี, Voucher No. / เลขที่เอกสาร, Journal No., Reference.
   - Example: if you see "6091" in the Description column, '6091' goes in
     `description`. It MUST NOT appear in `debit`, `credit`, `amount`, or `balance`.
   - Example: 'JV681130.1' is a voucher_no, never an amount.
   - Example: '1112-07' is an account_code, never an amount.

2. DIRECTION DERIVATION:
   - debit > 0  →  direction = "deposit"     (bank account goes UP / เงินฝาก)
   - credit > 0 →  direction = "withdrawal"  (bank account goes DOWN / ถอนเงิน)
   - both 0 / both blank → direction = "" (skip — likely a header or summary row)

3. AMOUNT DERIVATION:
   - amount = debit if debit > 0 else credit
   - Never sum debit + credit into amount. They are mutually exclusive in a row.

4. DATES: convert Buddhist year (>=2400) to Gregorian by subtracting 543.
   ALWAYS preserve original text in transaction_date_raw.

5. NUMBERS: no commas, no currency symbols, no parentheses. "12,450.00" → "12450.00".
   Negative numbers stay negative ("-500.00").

6. SKIP rows that are pure subtotals / openings / closings / page headers
   (e.g. "ยอดยกมา", "ยอดยกไป", "Balance forward", "Subtotal"). They go into
   opening_balance / closing_balance, NOT entries.

7. raw_row_data is for audit: dump the original column→cell mapping as you
   read it. If you cannot identify columns, leave it as an empty object {}.

If the text is clearly NOT a General Ledger (e.g. a tax invoice was uploaded
into the GL slot by mistake), return:
  {"document_type": "general_ledger", "entries": [], "account_name": "(not a GL)"}
"""

_BANK_STATEMENT_SYSTEM_PROMPT = """You are an accountant reading a Bank Statement. The input is plain text extracted from a bank PDF. Your job: parse each transaction row into a strict JSON schema.

Output ONE JSON object (no markdown fences, no prose, just JSON):

{
  "document_type": "bank_statement",
  "bank_name": "full bank name or empty",
  "bank_code": "kbank / bbl / scb / ktb / kkp / bay / ttb / empty",
  "account_name": "account holder name or empty",
  "account_number": "full account number or empty",
  "account_last4": "last 4 digits of account or empty",
  "period_start": "YYYY-MM-DD or empty",
  "period_end": "YYYY-MM-DD or empty",
  "opening_balance": "number-as-string or empty",
  "closing_balance": "number-as-string or empty",
  "entries": [
    {
      "transaction_date": "YYYY-MM-DD or empty",
      "transaction_date_raw": "as printed",
      "description": "transaction description / remark",
      "reference": "reference code / transaction code or empty",
      "deposit": "number-as-string from Deposit / Credit / เงินเข้า / ฝาก column, or empty",
      "withdrawal": "number-as-string from Withdrawal / Debit / เงินออก / ถอน column, or empty",
      "amount": "deposit if deposit>0 else withdrawal (derived)",
      "direction": "deposit | withdrawal | empty",
      "balance": "running balance from Balance / ยอดคงเหลือ column, or empty",
      "deposit_ref":    {"value": "number", "source_text": "as printed", "source_column": "Deposit"    } or null,
      "withdrawal_ref": {"value": "number", "source_text": "as printed", "source_column": "Withdrawal" } or null,
      "balance_ref":    {"value": "number", "source_text": "as printed", "source_column": "Balance"    } or null
    }
  ]
}

PROVENANCE — MANDATORY:
For every non-empty deposit / withdrawal / balance, ALSO fill the matching
*_ref object with `source_column` set to the EXACT column-header text the
number came from. Allowed columns: "Deposit" / "เงินเข้า" / "ฝาก" (deposit),
"Withdrawal" / "เงินออก" / "ถอน" (withdrawal), "Balance" / "ยอดคงเหลือ".
If the source was actually a Description / Reference / Account-No column,
fill source_column with that header verbatim — validators reject these.

CRITICAL RULES — VIOLATIONS ARE BUGS:

1. AMOUNT SOURCING:
   - deposit / withdrawal / balance / amount fields MAY ONLY contain values from
     the Deposit / Withdrawal / Balance columns.
   - Reference codes, transaction codes, account-number digits, remark text
     digits MUST NEVER be parsed into amount fields.

2. DIRECTION:
   - deposit > 0    → direction = "deposit"
   - withdrawal > 0 → direction = "withdrawal"

3. AMOUNT DERIVATION: amount = deposit if deposit > 0 else withdrawal.

4. DATES: convert Buddhist (>=2400) by -543. Preserve raw text.

5. NUMBERS: no commas, no THB / ฿. Negative numbers stay negative.

If the text is clearly NOT a bank statement, return:
  {"document_type": "bank_statement", "entries": [], "bank_name": "(not a bank statement)"}
"""

_VAT_REPORT_SYSTEM_PROMPT = """You are an accountant reading a Thai VAT report (รายงานภาษีขาย / รายงานภาษีซื้อ). Each row is one invoice. Your job: parse rows into strict JSON.

Output ONE JSON object (no markdown, no prose, just JSON):

{
  "document_type": "vat_report",
  "seller_name": "the report-filing company name or empty",
  "seller_tax": "13-digit Thai tax ID of the filing company or empty",
  "period_year": "Gregorian 4-digit year, e.g. '2026'",
  "period_month": "'01'..'12'",
  "total_subtotal": "report total net amount or empty",
  "total_vat": "report total VAT amount or empty",
  "total_total": "report grand total or empty",
  "entries": [
    {
      "seq_no": "row sequence number or empty",
      "transaction_date": "YYYY-MM-DD or empty",
      "transaction_date_raw": "as printed",
      "invoice_no": "invoice number",
      "customer_name": "buyer name",
      "customer_tax": "13-digit Thai tax ID or empty",
      "customer_branch": "branch / สำนักงานใหญ่ or empty",
      "subtotal": "net amount (number-as-string)",
      "vat": "VAT amount (number-as-string)",
      "total": "total amount (number-as-string)",
      "raw_row_data": {"column header": "cell text"}
    }
  ]
}

CRITICAL RULES:
1. Buddhist year (>=2400) converted to Gregorian by -543. period_year is Gregorian.
2. Numbers: no commas, no currency.
3. Tax IDs: exactly 13 digits, no dashes/spaces. Empty if not found.
4. Skip total/subtotal/page-footer rows — those go into the document-level
   total_subtotal / total_vat / total_total fields.
"""

_GENERIC_TABLE_SYSTEM_PROMPT = """You are reading a tabular document of unknown business type. Extract the table grid into a strict JSON object:

{
  "document_type": "generic_table",
  "headers": ["col1", "col2", ...],
  "rows": [
    {"col1": "value", "col2": "value", ...}
  ]
}

Output ONLY the JSON. Preserve cell text exactly as printed. Do NOT interpret
numbers as amounts or dates — keep them as strings. Skip blank rows.
"""


# ============================================================
# Original invoice prompt (unchanged behavior path)
# ============================================================
_SYSTEM_PROMPT = """You are an accountant extracting structured data from Thai tax invoice text. The text has already been OCR'd by another engine; your job is purely to interpret and map it to JSON. Do NOT correct typos or "improve" company names.

Output ONE JSON object matching this schema (no markdown fences, no explanation, just JSON):

{
  "document_type": "tax_invoice" | "receipt" | "credit_note" | "other",
  "is_not_invoice": false,
  "is_copy_or_duplicate": false,
  "invoice_number": "string or null",
  "date": "YYYY-MM-DD Gregorian or null",
  "date_raw": "exact date text as printed",
  "seller_name": "string",
  "seller_tax": "13-digit Thai tax ID or empty string",
  "seller_addr": "string",
  "buyer_name": "string",
  "buyer_tax": "13-digit Thai tax ID or empty string",
  "buyer_addr": "string",
  "subtotal": "number-as-string",
  "vat": "number-as-string",
  "wht_rate": "number-as-string",
  "wht_amount": "number-as-string",
  "total_amount": "number-as-string or null",
  "items": [{"name": "...", "qty": "...", "price": "...", "subtotal": "..."}],
  "notes": "remark text",
  "category": "3-5 char summary in items' language (e.g. 餐饮, ค่าขนส่ง)",
  "source_refs": {
    "invoice_number": {"value": "...", "source_text": "as printed", "source_column": "Invoice No."} or omit,
    "total_amount":   {"value": "...", "source_text": "as printed", "source_column": "Total"     } or omit,
    "subtotal":       {"value": "...", "source_text": "as printed", "source_column": "Subtotal"  } or omit,
    "vat":            {"value": "...", "source_text": "as printed", "source_column": "VAT"       } or omit,
    "seller_tax":     {"value": "...", "source_text": "as printed", "source_column": "Tax ID"    } or omit,
    "buyer_tax":      {"value": "...", "source_text": "as printed", "source_column": "Tax ID"    } or omit,
    "date":           {"value": "...", "source_text": "as printed", "source_column": "Date"      } or omit
  }
}

PROVENANCE — fill source_refs for amount + tax-id + date fields:
For each non-empty amount field (total_amount / subtotal / vat / wht_amount),
fill source_refs[<field>].source_column with the printed label of the cell
the number came from (e.g. "Total" / "ยอดรวม" / "จำนวนเงิน" / "Subtotal" /
"VAT" / "ภาษีมูลค่าเพิ่ม"). If the number came from a Description / Remark /
Address / Tax-ID-column-by-accident, fill that label EXACTLY — downstream
validators will reject and force needs_review. Do NOT invent column names.

CRITICAL RULES:
1. DATE: Buddhist year (>= 2400) MUST be converted to Gregorian by subtracting 543. e.g. 2569 -> 2026. ALWAYS fill date_raw with the original text.
2. NAMES & ADDRESSES: Copy EXACTLY as printed (Thai or English). Do NOT auto-correct or standardize. e.g. keep คะแฟ as คะแฟ, do NOT change to คาเฟ่.
3. ITEMS: Extract all unique line items. If the same name+qty+price appears multiple times (delivery note + receipt are commonly merged in Thai invoices), keep ONE copy only.
4. NUMBERS: No currency symbols, no commas (e.g., "12450.00").
5. TAX IDs: Exactly 13 digits, no dashes/spaces. Empty string if not found.
6. WHT (หัก ณ ที่จ่าย / ภ.ง.ด.3 / ภ.ง.ด.53): Common rates 1/2/3/5%. wht_rate is the number ONLY ("3" not "3%"). Only extract if printed; do NOT guess.
7. is_not_invoice: true ONLY if the text is clearly not an invoice (letter, contract, blank page, signature page).
8. is_copy_or_duplicate: true if the text contains สำเนา / COPY / DUPLICATE markers.
"""

_USER_PROMPT_PREFIX = "Extract from this OCR text:\n\n"


# ============================================================
# Public API
# ============================================================
def extract_from_text(
    text: str,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> ThaiInvoice:
    """Extract ThaiInvoice fields from a single OCR text blob.

    Primitive operation. For richer metadata (token counts, latency, retries),
    use `extract_from_page` instead.

    Args:
        text: OCR text (typically a Page.full_text from layer 1)
        api_key: API key override; defaults to env GOOGLE_API_KEY then GEMINI_API_KEY
        model_name: Gemini model id; defaults to env OCR_FLASHLITE_MODEL or
            "gemini-2.5-flash-lite"
        max_retries: JSON-parse retries before ValueError (default 1 per spec)
        timeout: per-API-call timeout in seconds (default 60)

    Returns:
        ThaiInvoice. Empty / missing fields stay at their schema defaults.

    Raises:
        ValueError: Gemini returned invalid JSON or empty response after
            max_retries retries
        Layer2AuthError: no API key, invalid key, or permission denied
        Layer2QuotaError: 429 / quota exceeded
        Layer2TransientError: timeout / 5xx / unavailable
        Layer2Error: other Gemini API errors
    """
    invoice, _meta = _extract_internal(
        text,
        api_key=api_key,
        model_name=model_name,
        max_retries=max_retries,
        timeout=timeout,
    )
    return invoice


def extract_from_page(
    page: Page,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    document_type: BusinessDocumentType = "auto",
) -> Layer2PageResult:
    """Extract structured data from a single layer-1 Page.

    Routes by document_type (2026-05-21 multi-schema refactor):
        - "auto" / "invoice"        → invoice prompt → ThaiInvoice
        - "bank_statement"          → bank prompt → BankStatementDocument
        - "general_ledger"          → GL prompt → GeneralLedgerDocument
        - "vat_report"              → VAT prompt → VatReportDocument
        - "generic_table"           → generic table prompt → GenericTableDocument

    Non-invoice docs return Layer2PageResult with `document` populated and
    `invoice` left at is_not_invoice=True for backwards compat.

    Empty pages (no text after strip) are skipped — no API call is made.

    Raises:
        Same as extract_from_text. The page_number is included in error msg.
    """
    t0 = time.time()

    # Build text from Page — prefer structured table_rows when available
    # (Excel/CSV/Word direct-read path), else use full_text.
    text_input = _page_to_text(page)

    if not text_input or not text_input.strip():
        return Layer2PageResult(
            page_number=page.page_number,
            invoice=ThaiInvoice(is_not_invoice=True),
            document_type=document_type,
            elapsed_ms=int((time.time() - t0) * 1000),
            skipped=True,
        )

    # Invoice / auto path → existing behavior, returns ThaiInvoice
    if document_type in ("auto", "invoice"):
        try:
            invoice, meta = _extract_internal(
                text_input,
                api_key=api_key,
                model_name=model_name,
                max_retries=max_retries,
                timeout=timeout,
            )
        except (ValueError, Layer2Error) as e:
            raise type(e)(f"layer2: page {page.page_number}: {e}") from e

        return Layer2PageResult(
            page_number=page.page_number,
            invoice=invoice,
            document_type=document_type,
            document=None,
            elapsed_ms=int((time.time() - t0) * 1000),
            input_tokens=meta["input_tokens"],
            output_tokens=meta["output_tokens"],
            retries=meta["retries"],
        )

    # Non-invoice doc types — route to the per-type prompt+schema
    try:
        document, meta = _extract_doc_internal(
            text_input,
            document_type=document_type,
            api_key=api_key,
            model_name=model_name,
            max_retries=max_retries,
            timeout=timeout,
            page_number=page.page_number,
        )
    except (ValueError, Layer2Error) as e:
        raise type(e)(f"layer2: page {page.page_number}: {e}") from e

    return Layer2PageResult(
        page_number=page.page_number,
        invoice=ThaiInvoice(is_not_invoice=True),
        document_type=document_type,
        document=document,
        elapsed_ms=int((time.time() - t0) * 1000),
        input_tokens=meta["input_tokens"],
        output_tokens=meta["output_tokens"],
        retries=meta["retries"],
    )


def _page_to_text(page: Page) -> str:
    """Convert a Page to plain text for Layer 2 input.

    When page has structured table_rows (table_path / Excel/CSV/Word),
    serialize them with headers preserved so Layer 2 can identify columns.
    Else use Page.full_text as-is.
    """
    if page.table_rows is not None and page.table_headers is not None:
        # Pipe-delimited grid keeps column structure obvious to the LLM
        header_line = " | ".join(page.table_headers)
        body_lines = []
        for row in page.table_rows:
            cells = [str(row.get(h, "")) for h in page.table_headers]
            body_lines.append(" | ".join(cells))
        return header_line + "\n" + "\n".join(body_lines)
    return page.full_text


def extract_from_layer1(
    layer1_result: Layer1Result,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    document_type: BusinessDocumentType = "auto",
) -> Layer2Result:
    """Process every Page in a Layer1Result, returning a Layer2Result.

    Per-page extraction; one ThaiInvoice per Page. Multi-page invoices are
    aggregated by invoice_grouper (downstream, outside layer 2's scope).

    Failure semantics: the first failing page propagates its exception.
    Successful pages BEFORE the failure are NOT returned. Caller (pipeline.py)
    that wants partial-success recovery should loop over Page itself.

    Args:
        layer1_result: output of services.ocr.layer1_vision.extract_*
        api_key, model_name, max_retries, timeout: see extract_from_text

    Returns:
        Layer2Result with one Layer2PageResult per Page from layer 1

    Raises:
        Same as extract_from_text, surfaced on the first failing page.
    """
    t0 = time.time()
    page_results = []
    for page in layer1_result.pages:
        page_results.append(
            extract_from_page(
                page,
                api_key=api_key,
                model_name=model_name,
                max_retries=max_retries,
                timeout=timeout,
                document_type=document_type,
            )
        )

    return Layer2Result(
        pages=page_results,
        elapsed_ms=int((time.time() - t0) * 1000),
        model=model_name,
    )


# ============================================================
# Internal: per-document-type extraction (2026-05-21 refactor)
# ============================================================
_DOC_PROMPTS: dict = {
    "general_ledger": _GL_SYSTEM_PROMPT,
    "bank_statement": _BANK_STATEMENT_SYSTEM_PROMPT,
    "vat_report": _VAT_REPORT_SYSTEM_PROMPT,
    "generic_table": _GENERIC_TABLE_SYSTEM_PROMPT,
}

_DOC_SCHEMAS: dict = {
    "general_ledger": GeneralLedgerDocument,
    "bank_statement": BankStatementDocument,
    "vat_report": VatReportDocument,
    "generic_table": GenericTableDocument,
}


def _extract_doc_internal(
    text: str,
    document_type: BusinessDocumentType,
    api_key: Optional[str],
    model_name: str,
    max_retries: int,
    timeout: int,
    page_number: int,
):
    """Extract per-document-type schema (GL / Bank / VAT / Table).

    Picks the matching prompt + Pydantic schema by document_type, calls
    Gemini with the same retry logic as invoice extraction, validates the
    result against the schema, returns (document, metadata).
    """
    if not isinstance(text, str):
        raise TypeError(f"layer2: text must be str, got {type(text).__name__}")

    cleaned = text.strip()
    if len(cleaned) < MIN_TEXT_LENGTH:
        # Too short — return empty document of the right type
        schema_cls = _DOC_SCHEMAS[document_type]
        return (
            schema_cls(),
            {"input_tokens": 0, "output_tokens": 0, "retries": 0},
        )

    if len(cleaned) > MAX_TEXT_LENGTH:
        logger.warning(
            "layer2: input text %d chars truncated to %d (doc_type=%s)",
            len(cleaned), MAX_TEXT_LENGTH, document_type,
        )
        cleaned = cleaned[:MAX_TEXT_LENGTH]

    key = (
        api_key
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )
    if not key:
        raise Layer2AuthError(
            "layer2: GOOGLE_API_KEY (or GEMINI_API_KEY) env var not set"
        )

    prompt_prefix = _DOC_PROMPTS[document_type]
    schema_cls = _DOC_SCHEMAS[document_type]

    data, meta = _call_gemini_with_retry(
        cleaned,
        api_key=key.strip(),
        model_name=model_name,
        max_retries=max_retries,
        timeout=timeout,
        system_prompt_override=prompt_prefix,
    )

    try:
        document = schema_cls(**data)
    except ValidationError as e:
        raise ValueError(
            f"layer2: Gemini JSON parsed but failed {schema_cls.__name__} schema: {e}"
        ) from e

    return document, meta


# ============================================================
# Internal: shared extraction core
# ============================================================
def _extract_internal(
    text: str,
    api_key: Optional[str],
    model_name: str,
    max_retries: int,
    timeout: int,
) -> Tuple[ThaiInvoice, dict]:
    """Core extraction: validates text, calls Gemini with retry, parses JSON,
    validates against ThaiInvoice. Returns (invoice, metadata).

    metadata keys: input_tokens, output_tokens, retries
    """
    if not isinstance(text, str):
        raise TypeError(f"layer2: text must be str, got {type(text).__name__}")

    cleaned = text.strip()
    if len(cleaned) < MIN_TEXT_LENGTH:
        # Too short to be a real invoice; return empty marked is_not_invoice
        # without an API call.
        return (
            ThaiInvoice(is_not_invoice=True),
            {"input_tokens": 0, "output_tokens": 0, "retries": 0},
        )

    if len(cleaned) > MAX_TEXT_LENGTH:
        logger.warning(
            "layer2: input text %d chars truncated to %d",
            len(cleaned),
            MAX_TEXT_LENGTH,
        )
        cleaned = cleaned[:MAX_TEXT_LENGTH]

    key = (
        api_key
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )
    if not key:
        raise Layer2AuthError(
            "layer2: GOOGLE_API_KEY (or GEMINI_API_KEY) env var not set"
        )

    data, meta = _call_gemini_with_retry(
        cleaned,
        api_key=key.strip(),
        model_name=model_name,
        max_retries=max_retries,
        timeout=timeout,
    )

    try:
        invoice = ThaiInvoice(**data)
    except ValidationError as e:
        raise ValueError(
            f"layer2: Gemini JSON parsed but failed ThaiInvoice schema: {e}"
        ) from e

    return invoice, meta


def _call_gemini_with_retry(
    text: str,
    api_key: str,
    model_name: str,
    max_retries: int,
    timeout: int,
    system_prompt_override: Optional[str] = None,
) -> Tuple[dict, dict]:
    """Make Gemini API call with JSON-parse retry budget.

    Retries ONLY on JSON parse failure / empty response. Network / auth /
    quota errors propagate immediately (no point retrying them at this layer
    — pipeline.py decides whether to retry transient errors).

    When system_prompt_override is provided, that prompt is used instead of
    the default invoice prompt (multi-schema refactor).

    Returns (data: dict, metadata: dict)
    metadata keys: input_tokens, output_tokens, retries
    """
    model = _get_model(api_key=api_key, model_name=model_name)
    sys_prompt = system_prompt_override if system_prompt_override else _SYSTEM_PROMPT
    base_prompt = sys_prompt + "\n\n" + _USER_PROMPT_PREFIX + text

    last_parse_error: Optional[str] = None
    last_raw_preview: str = ""

    for attempt in range(max_retries + 1):
        # v118.35.0.5 · 重试时追加"精简输出"指令 · 救 token 上限截断场景
        prompt = base_prompt + (_RETRY_TRIM_HINT if attempt > 0 else "")
        try:
            response = model.generate_content(
                prompt,
                request_options={"timeout": timeout},
            )
        except Exception as e:
            # Network / auth / quota / unknown — classify and propagate
            raise _classify_gemini_exception(e) from e

        raw = (response.text or "").strip() if hasattr(response, "text") else ""

        # Capture token usage (best effort)
        input_tokens = 0
        output_tokens = 0
        try:
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
                output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        except Exception:  # pragma: no cover  (defensive only)
            pass

        if not raw:
            last_parse_error = "empty response"
            last_raw_preview = ""
            logger.warning(
                "layer2: empty response (attempt %d/%d)",
                attempt + 1,
                max_retries + 1,
            )
            if attempt < max_retries:
                continue
            raise ValueError(
                f"layer2: Gemini returned empty response after "
                f"{max_retries + 1} attempts"
            )

        try:
            data = _parse_json(raw)
        except json.JSONDecodeError as e:
            last_parse_error = str(e)
            last_raw_preview = raw[:300]
            logger.warning(
                "layer2: JSON parse failed (attempt %d/%d): %s; raw[:200]=%r",
                attempt + 1,
                max_retries + 1,
                e,
                raw[:200],
            )
            if attempt < max_retries:
                continue
            raise ValueError(
                f"layer2: Gemini returned invalid JSON after "
                f"{max_retries + 1} attempts: {last_parse_error}; "
                f"raw[:300]={last_raw_preview!r}"
            ) from e

        return data, {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "retries": attempt,
        }

    # Defensive fallback (loop should always either return or raise above)
    raise ValueError(
        f"layer2: unreachable; last parse error: {last_parse_error}"
    )


def _parse_json(text: str) -> dict:
    """Parse Gemini's response as JSON, stripping markdown fences if present.

    With response_mime_type='application/json' Gemini SHOULD not add ```json
    fences. But occasionally it does anyway. Be defensive.

    Raises json.JSONDecodeError on parse failure.
    """
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl > 0:
            s = s[first_nl + 1 :]
        else:
            s = s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip()
    obj = json.loads(s)
    if not isinstance(obj, dict):
        # Gemini returned a list / scalar / etc. — treat as parse failure
        raise json.JSONDecodeError(
            f"expected JSON object, got {type(obj).__name__}",
            s,
            0,
        )
    return obj


def _classify_gemini_exception(e: Exception) -> Exception:
    """Translate raw google-generativeai SDK exception into Layer2 hierarchy.

    The SDK's exception types vary across versions; rather than match
    exception classes directly, we sniff the message + type name. This is
    less precise than catch-by-class but more portable.
    """
    name = type(e).__name__
    msg = str(e)[:400]
    msg_lower = msg.lower()

    # Auth / permission errors
    if (
        name in ("Unauthenticated", "PermissionDenied")
        or "permission denied" in msg_lower
        or "unauthenticated" in msg_lower
        or "api key not valid" in msg_lower
        or "invalid api key" in msg_lower
        or "403" in msg
        or "401" in msg
    ):
        return Layer2AuthError(f"layer2: auth ({name}): {msg}")

    # Quota / rate limit
    if (
        name in ("ResourceExhausted",)
        or "429" in msg
        or "quota" in msg_lower
        or "resource_exhausted" in msg_lower
        or "rate limit" in msg_lower
    ):
        return Layer2QuotaError(f"layer2: quota ({name}): {msg}")

    # Transient (timeout / 5xx / network)
    if (
        name in ("DeadlineExceeded", "ServiceUnavailable", "InternalServerError", "Timeout")
        or "timeout" in msg_lower
        or "deadline" in msg_lower
        or "unavailable" in msg_lower
        or "503" in msg
        or "502" in msg
        or "504" in msg
        or "500" in msg
        or "connection" in msg_lower
    ):
        return Layer2TransientError(f"layer2: transient ({name}): {msg}")

    return Layer2Error(f"layer2: {name}: {msg}")


# ============================================================
# Model lazy singleton (keyed by api_key + model_name)
# ============================================================
_model_cache: dict = {}
_model_lock = threading.Lock()


def _get_model(api_key: str, model_name: str):
    """Return a GenerativeModel for the given (api_key, model_name).

    Cached up to 10 distinct combinations to bound memory. Each cache entry
    is a fully-configured GenerativeModel (handles its own connection pool
    internally so we don't need a separate lock for usage, only for init).
    """
    cache_key = (api_key, model_name)

    if cache_key in _model_cache:
        return _model_cache[cache_key]

    with _model_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]

        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "layer2: google-generativeai required. "
                "Install: pip install google-generativeai"
            ) from e

        # Note: direct endpoint (no Cloudflare proxy). If/when dev machine
        # cannot reach generativelanguage.googleapis.com, plumb a proxy via
        # env var rather than hardcoding here.
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
                "response_mime_type": "application/json",
            },
        )

        # Bound cache size — pop oldest if at limit
        if len(_model_cache) >= 10:
            _model_cache.pop(next(iter(_model_cache)))
        _model_cache[cache_key] = model

        logger.info("layer2: GenerativeModel initialized: %s", model_name)
        return model
