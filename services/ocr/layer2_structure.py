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

from .layer2_gemini import (  # noqa: F401 · L2-A 纯搬家 re-export(调用方/COV4 测 0 改动)
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_TEMPERATURE,
    Layer2AuthError,
    Layer2Error,
    Layer2QuotaError,
    Layer2TransientError,
    _classify_gemini_exception,
    _get_model,
    _parse_json,
)

from .layer2_prompts import (  # noqa: F401 · L2-P 纯搬家 re-export(prompt 字节不变·调用方 0 改动)
    _BANK_STATEMENT_SYSTEM_PROMPT,
    _GENERIC_TABLE_SYSTEM_PROMPT,
    _GL_SYSTEM_PROMPT,
    _RETRY_TRIM_HINT,
    _SYSTEM_PROMPT,
    _USER_PROMPT_PREFIX,
    _VAT_REPORT_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================
DEFAULT_MODEL = os.environ.get("OCR_FLASHLITE_MODEL", "gemini-2.5-flash-lite")
DEFAULT_MAX_RETRIES = 1
DEFAULT_TIMEOUT_SECONDS = 60
# v118.35.0.11 · 8192 → 16384 · raw_row_data 字段从 BankStatementEntry schema
# 物理删除后 · 单 entry token 砍掉一半 · 但极大流水 Excel(80-100 行交易) +
# 长描述字段 还是有可能撞 8192 · 16384 给足空间.


# Skip Gemini call if text is shorter than this (likely garbage / blank page)
MIN_TEXT_LENGTH = 20

# Truncate input text to bound token cost on accidentally-large pages.
# Real Thai invoices fit comfortably in 5000-8000 chars; 30000 is a safety net.
MAX_TEXT_LENGTH = 30000


# ============================================================
# Exception hierarchy
# ============================================================


# ============================================================
# Per-document-type prompts (2026-05-21 multi-schema refactor)
# ============================================================
# Each business document type gets its own prompt + output schema. The
# CRITICAL design rule: GL files MUST only treat Debit/Credit column values
# as amounts. Description-column numbers (e.g. '6091', 'JV681130.1',
# '1112-07', 'QP10280137') MUST NOT be parsed as amount/debit/credit.
# Same principle for Bank Statements: only deposit/withdrawal/balance.


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
            len(cleaned),
            MAX_TEXT_LENGTH,
            document_type,
        )
        cleaned = cleaned[:MAX_TEXT_LENGTH]

    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise Layer2AuthError("layer2: GOOGLE_API_KEY (or GEMINI_API_KEY) env var not set")

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

    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise Layer2AuthError("layer2: GOOGLE_API_KEY (or GEMINI_API_KEY) env var not set")

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
        raise ValueError(f"layer2: Gemini JSON parsed but failed ThaiInvoice schema: {e}") from e

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
        # v118.35.0.25 · 埋点 · 记 Gemini 调用统计(给 Earn 监控面板 + LINE 告警用)
        import time as _t_v25

        _t_start = _t_v25.time()
        try:
            response = model.generate_content(
                prompt,
                request_options={"timeout": timeout},
            )
            try:
                from services.monitoring import record_gemini_call as _rec

                _rec(
                    success=True, http_status=200, latency_ms=int((_t_v25.time() - _t_start) * 1000)
                )
            except Exception:
                pass
        except Exception as e:
            try:
                from services.monitoring import record_gemini_call as _rec

                _http = 429 if ("ResourceExhausted" in type(e).__name__ or "429" in str(e)) else 500
                _rec(
                    success=False,
                    http_status=_http,
                    latency_ms=int((_t_v25.time() - _t_start) * 1000),
                )
            except Exception:
                pass
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
                f"layer2: Gemini returned empty response after " f"{max_retries + 1} attempts"
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
    raise ValueError(f"layer2: unreachable; last parse error: {last_parse_error}")


# ============================================================
# Model lazy singleton (keyed by api_key + model_name)
# ============================================================
