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
    Layer1Result,
    Layer2PageResult,
    Layer2Result,
    Page,
    ThaiInvoice,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================
DEFAULT_MODEL = os.environ.get("OCR_FLASHLITE_MODEL", "gemini-2.5-flash-lite")
DEFAULT_MAX_RETRIES = 1
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_OUTPUT_TOKENS = 4096

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
# Prompt
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
  "category": "3-5 char summary in items' language (e.g. 餐饮, ค่าขนส่ง)"
}

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
) -> Layer2PageResult:
    """Extract ThaiInvoice from a single layer-1 Page, with per-call metadata.

    Empty pages (no text after strip) are skipped — no API call is made.
    The returned Layer2PageResult has `skipped=True` and an empty ThaiInvoice
    with `is_not_invoice=True`.

    Args:
        page: a Page from Layer1Result.pages
        api_key, model_name, max_retries, timeout: see extract_from_text

    Returns:
        Layer2PageResult: invoice + page_number + tokens + retries + elapsed

    Raises:
        Same as extract_from_text. The page_number is included in error msg.
    """
    t0 = time.time()

    if not page.full_text or not page.full_text.strip():
        return Layer2PageResult(
            page_number=page.page_number,
            invoice=ThaiInvoice(is_not_invoice=True),
            elapsed_ms=int((time.time() - t0) * 1000),
            skipped=True,
        )

    try:
        invoice, meta = _extract_internal(
            page.full_text,
            api_key=api_key,
            model_name=model_name,
            max_retries=max_retries,
            timeout=timeout,
        )
    except (ValueError, Layer2Error) as e:
        # Re-raise with page context; preserve original type for caller dispatch
        raise type(e)(f"layer2: page {page.page_number}: {e}") from e

    return Layer2PageResult(
        page_number=page.page_number,
        invoice=invoice,
        elapsed_ms=int((time.time() - t0) * 1000),
        input_tokens=meta["input_tokens"],
        output_tokens=meta["output_tokens"],
        retries=meta["retries"],
    )


def extract_from_layer1(
    layer1_result: Layer1Result,
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
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
            )
        )

    return Layer2Result(
        pages=page_results,
        elapsed_ms=int((time.time() - t0) * 1000),
        model=model_name,
    )


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
) -> Tuple[dict, dict]:
    """Make Gemini API call with JSON-parse retry budget.

    Retries ONLY on JSON parse failure / empty response. Network / auth /
    quota errors propagate immediately (no point retrying them at this layer
    — pipeline.py decides whether to retry transient errors).

    Returns (data: dict, metadata: dict)
    metadata keys: input_tokens, output_tokens, retries
    """
    model = _get_model(api_key=api_key, model_name=model_name)
    prompt = _SYSTEM_PROMPT + "\n\n" + _USER_PROMPT_PREFIX + text

    last_parse_error: Optional[str] = None
    last_raw_preview: str = ""

    for attempt in range(max_retries + 1):
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
