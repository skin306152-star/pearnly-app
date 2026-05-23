# -*- coding: utf-8 -*-
"""
services/ocr/layer3_fallback.py

Layer 3 of the new OCR pipeline: Gemini Flash visual fallback.

When the layer 1 + layer 2 chain produces a result with low confidence,
missing critical fields, or failing amount math, pipeline.py escalates to
layer 3. Layer 3 receives the ORIGINAL image, the layer 1 OCR text, the
(suspect) layer 2 ThaiInvoice, and the list of trigger reasons; it then
asks Gemini 2.5 Flash (with vision) to do a careful visual review and
output a corrected ThaiInvoice in the same schema.

Key design choices:
- Image + text + JSON multi-modal input (Flash, NOT Flash-Lite)
- Layer 3 does NOT decide when to run — pipeline.py does. Layer 3 only
  obeys: "I was called, here's the input, here's the output."
- Output schema is the SAME ThaiInvoice from layer 2 — downstream
  consumers (mrerp_xlsx_generator, archive.py, ...) can't tell whether
  the invoice came from layer 2 alone or layer 2 + layer 3.
- 1 retry on JSON parse failure, then Layer3FallbackError (NOT ValueError
  — pipeline.py decides whether to fall back to layer 2's output,
  emit a low-confidence-queue record, or hard-fail).
- Lazy singleton model cache (per api_key + model_name combo) — same
  pattern as layer 2.
- response_mime_type='application/json' + temperature=0.0 for determinism.

Auth:
- Reads env GOOGLE_API_KEY first, falls back to GEMINI_API_KEY (matches layer 2).

Public API:
    refine_with_image(image_bytes, layer1_text, layer2_invoice, trigger_reasons, ...)
        -> Tuple[ThaiInvoice, dict]
    refine_page(image_bytes, layer1_page, layer2_invoice, trigger_reasons, ...)
        -> Layer3PageResult

Custom exceptions:
    Layer3Error              base for catch-all
    Layer3FallbackError      JSON / empty response after retries (= main failure)
    Layer3AuthError          missing or invalid API key
    Layer3QuotaError         rate limit / quota
    Layer3TransientError     timeout / 5xx / network
"""

from __future__ import annotations

import io
import json
import logging
import os
import threading
import time
from typing import List, Optional, Tuple

from pydantic import ValidationError

from .schemas import (
    BusinessDocumentType,
    Layer3PageResult,
    Page,
    ThaiInvoice,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================
DEFAULT_MODEL = os.environ.get("OCR_FLASH_MODEL", "gemini-2.5-flash")
DEFAULT_MAX_RETRIES = 1
DEFAULT_TIMEOUT_SECONDS = 90  # longer than layer 2 — vision calls are slower
DEFAULT_TEMPERATURE = 0.0
# B2 fix: bumped from 4096 to 8192. Real-world Thai invoices serialized
# to JSON with all line items can exceed 4096 output tokens, leading to
# truncated unterminated-string JSON errors. 8192 leaves headroom for
# 50+ line items + long Thai company names + full address.
DEFAULT_MAX_OUTPUT_TOKENS = 8192

# Truncate layer 1 OCR text to avoid bloating the prompt on large pages.
# Layer 3 has the IMAGE for ground truth; OCR text is just a hint.
MAX_TEXT_LENGTH = 20000


# ============================================================
# Exception hierarchy
# ============================================================
class Layer3Error(Exception):
    """Base exception for layer 3 errors. Catch this for generic dispatch."""


class Layer3FallbackError(Layer3Error):
    """Layer 3 itself failed (JSON parse / empty response after retries).

    Per spec: do NOT crash pipeline.py. The caller decides whether to fall
    back to the (still imperfect) layer 2 ThaiInvoice, send to manual
    review queue, or hard-fail.
    """


class Layer3AuthError(Layer3Error):
    """Missing or invalid API key (NOT retryable)."""


class Layer3QuotaError(Layer3Error):
    """Quota or rate-limit exceeded. Retry after backoff."""


class Layer3TransientError(Layer3Error):
    """Network / timeout / 5xx. Potentially retryable."""


# ============================================================
# Prompt
# ============================================================
_SYSTEM_PROMPT = """You are an accountant doing a careful VISUAL review of a Thai tax invoice. Another OCR + LLM chain has already extracted fields, but the result was FLAGGED for visual review (see trigger reasons below).

Your task:
1. Look at the IMAGE carefully — especially areas mentioned in the trigger reasons.
2. Compare the image to (a) the OCR text from a previous engine and (b) the previous JSON extraction.
3. CORRECT any wrong fields, FILL IN any missing fields you can read clearly from the IMAGE.
4. Output the COMPLETE corrected ThaiInvoice JSON (not just diffs — full schema).
5. When the IMAGE and the previous extraction DISAGREE, trust the IMAGE.
6. When the IMAGE is unclear, fall back to the OCR text. When both are unclear, keep the previous value rather than guess.

Output ONE JSON object matching this schema (no markdown, no explanation, just JSON):

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
  "category": "3-5 char summary in items' language",
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

PROVENANCE — fill source_refs for amount + tax-id + date fields with the
exact printed column label of the cell the value came from. Validators
reject amounts sourced from Description / Remark / Address columns.

CRITICAL RULES (same as previous extraction; pay attention):
1. DATE: Buddhist year (>= 2400) MUST be converted to Gregorian by subtracting 543. e.g. 2569 -> 2026. ALWAYS fill date_raw with the original text.
2. NAMES & ADDRESSES: Copy EXACTLY as printed (Thai or English). Do NOT auto-correct or standardize.
3. ITEMS: Extract all unique line items. If same name+qty+price appears multiple times, keep ONE copy only.
4. NUMBERS: No currency symbols, no commas (e.g., "12450.00").
5. TAX IDs: Exactly 13 digits, no dashes/spaces. Empty string if not found.
6. WHT: Common rates 1/2/3/5%. wht_rate is the number ONLY ("3" not "3%").
7. AMOUNT ARITHMETIC: When trigger reasons mention amount mismatch, look carefully at subtotal/vat/total in the image. The correct relationship is: subtotal + vat = total_amount (within rounding tolerance).
8. is_not_invoice: true ONLY if the text is clearly not an invoice.
9. is_copy_or_duplicate: true if the text contains สำเนา / COPY / DUPLICATE markers.
"""


def _build_user_prompt(
    layer1_text: str, layer2_invoice: ThaiInvoice, trigger_reasons: List[str]
) -> str:
    """Assemble the user-message text block (image is sent separately)."""
    if len(layer1_text) > MAX_TEXT_LENGTH:
        layer1_text = layer1_text[:MAX_TEXT_LENGTH] + "\n[...truncated]"

    triggers_block = (
        "\n".join(f"  - {t}" for t in trigger_reasons)
        if trigger_reasons
        else "  - (no specific trigger; general visual review)"
    )

    prev_json = layer2_invoice.model_dump(mode="json")
    prev_json_str = json.dumps(prev_json, ensure_ascii=False, indent=2)

    return (
        "TRIGGER REASONS (why we are asking for visual review):\n"
        f"{triggers_block}\n\n"
        "OCR TEXT (from Vision API, may have minor character errors):\n"
        "=== OCR TEXT ===\n"
        f"{layer1_text}\n"
        "=== END OCR TEXT ===\n\n"
        "PREVIOUS EXTRACTION (may have errors flagged above):\n"
        "=== PREVIOUS JSON ===\n"
        f"{prev_json_str}\n"
        "=== END PREVIOUS JSON ===\n\n"
        "Now look at the IMAGE and output the CORRECTED JSON only."
    )


# ============================================================
# Public API
# ============================================================
def refine_with_image(
    image_bytes: bytes,
    layer1_text: str,
    layer2_invoice: ThaiInvoice,
    trigger_reasons: List[str],
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    document_type: BusinessDocumentType = "auto",
) -> Tuple[ThaiInvoice, dict]:
    """Refine a (suspect) ThaiInvoice using visual review of the source image.

    Primitive operation. For richer metadata + Page-aware result, use refine_page.

    Args:
        image_bytes: rendered image of the page being reviewed (PNG / JPG bytes,
            typically rendered from PDF by pipeline.py at 200 DPI)
        layer1_text: OCR text from layer 1 (Page.full_text)
        layer2_invoice: the suspect ThaiInvoice from layer 2 (to be corrected)
        trigger_reasons: human-readable list of why pipeline called layer 3,
            e.g. ["Vision confidence in 'total_amount' is 0.62 (< 0.85)",
                  "subtotal + vat (8516.13) != total_amount (8000.00)"]
        api_key: API key override; defaults to env GOOGLE_API_KEY then GEMINI_API_KEY
        model_name: Gemini model id; defaults to env OCR_FLASH_MODEL or "gemini-2.5-flash"
        max_retries: JSON-parse retries (default 1)
        timeout: per-API-call timeout in seconds (default 90)

    Returns:
        (corrected_invoice, metadata) where metadata has:
            input_tokens, output_tokens, retries

    Raises:
        Layer3FallbackError: invalid JSON / empty response after all retries
        Layer3AuthError: no API key / permission denied
        Layer3QuotaError: 429 / quota exceeded
        Layer3TransientError: timeout / 5xx / unavailable
        Layer3Error: other API errors
        TypeError: bad input types
    """
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise TypeError(f"layer3: image_bytes must be bytes, got {type(image_bytes).__name__}")
    if not image_bytes:
        raise TypeError("layer3: image_bytes is empty")
    if not isinstance(layer1_text, str):
        raise TypeError(f"layer3: layer1_text must be str, got {type(layer1_text).__name__}")
    if not isinstance(layer2_invoice, ThaiInvoice):
        raise TypeError(
            f"layer3: layer2_invoice must be ThaiInvoice, got " f"{type(layer2_invoice).__name__}"
        )

    # 2026-05-21 multi-schema refactor: Layer 3 visual fallback currently
    # supports ONLY invoice/auto. Non-invoice doc types (GL/Bank/VAT) go
    # through Layer 2 with their dedicated prompts; if their confidence is
    # low, pipeline.py routes them to needs_review queue rather than firing
    # the invoice-shaped Layer 3. We accept document_type for forward
    # compat — when it's a non-invoice type, log + still do invoice refine
    # (the caller in pipeline.py should not have called us here).
    if document_type not in ("auto", "invoice"):
        logger.warning(
            "layer3: called with document_type=%s — invoice prompt will be used "
            "(non-invoice visual fallback not implemented; pipeline should "
            "route these to needs_review instead)",
            document_type,
        )

    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise Layer3AuthError("layer3: GOOGLE_API_KEY (or GEMINI_API_KEY) env var not set")

    data, meta = _call_gemini_with_retry(
        image_bytes=bytes(image_bytes),
        layer1_text=layer1_text,
        layer2_invoice=layer2_invoice,
        trigger_reasons=list(trigger_reasons or []),
        api_key=key.strip(),
        model_name=model_name,
        max_retries=max_retries,
        timeout=timeout,
    )

    try:
        invoice = ThaiInvoice(**data)
    except ValidationError as e:
        raise Layer3FallbackError(
            f"layer3: Gemini JSON parsed but failed ThaiInvoice schema: {e}"
        ) from e

    return invoice, meta


def refine_page(
    image_bytes: bytes,
    layer1_page: Page,
    layer2_invoice: ThaiInvoice,
    trigger_reasons: List[str],
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    document_type: BusinessDocumentType = "auto",
) -> Layer3PageResult:
    """Refine layer 2's invoice for one Page using visual fallback.

    Convenience wrapper: takes a layer 1 Page (for text + page_number),
    returns a Layer3PageResult with metadata.

    Args:
        image_bytes: the rendered image of THIS page (pipeline.py is
            responsible for rendering — layer 3 does not render PDFs)
        layer1_page: the layer 1 Page corresponding to this image (used
            for layer1_text via .full_text and page_number)
        layer2_invoice: the layer 2 ThaiInvoice for this page
        trigger_reasons: see refine_with_image
        api_key, model_name, max_retries, timeout: see refine_with_image

    Returns:
        Layer3PageResult: corrected invoice + per-call metadata

    Raises:
        Same as refine_with_image. The page_number is added to error msg.
    """
    t0 = time.time()
    try:
        invoice, meta = refine_with_image(
            image_bytes=image_bytes,
            layer1_text=layer1_page.full_text,
            layer2_invoice=layer2_invoice,
            trigger_reasons=trigger_reasons,
            api_key=api_key,
            model_name=model_name,
            max_retries=max_retries,
            timeout=timeout,
            document_type=document_type,
        )
    except (Layer3Error, TypeError) as e:
        # Preserve exception type for caller dispatch; add page context
        raise type(e)(f"layer3: page {layer1_page.page_number}: {e}") from e

    elapsed_ms = int((time.time() - t0) * 1000)
    return Layer3PageResult(
        page_number=layer1_page.page_number,
        invoice=invoice,
        elapsed_ms=elapsed_ms,
        input_tokens=meta["input_tokens"],
        output_tokens=meta["output_tokens"],
        retries=meta["retries"],
        trigger_reasons=list(trigger_reasons or []),
        model=model_name,
    )


# ============================================================
# Internal: Gemini call + retry + parse
# ============================================================
def _call_gemini_with_retry(
    image_bytes: bytes,
    layer1_text: str,
    layer2_invoice: ThaiInvoice,
    trigger_reasons: List[str],
    api_key: str,
    model_name: str,
    max_retries: int,
    timeout: int,
) -> Tuple[dict, dict]:
    """Build prompt + image, call Gemini, retry on JSON parse failure.

    Returns (data: dict, metadata: dict)
    metadata keys: input_tokens, output_tokens, retries
    """
    try:
        from PIL import Image
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "layer3: Pillow (PIL) required for image input. " "Install: pip install pillow"
        ) from e

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        # Force load so we catch decode errors here, not deep in Gemini SDK
        pil_image.load()
    except Exception as e:
        raise TypeError(f"layer3: image_bytes not a valid image: {type(e).__name__}: {e}") from e

    base_user_prompt = _build_user_prompt(layer1_text, layer2_invoice, trigger_reasons)
    model = _get_model(api_key=api_key, model_name=model_name)

    last_parse_error: Optional[str] = None
    last_raw_preview: str = ""

    # B2 fix: retry prompt enhancement — on retry, append explicit JSON
    # hygiene instructions to reduce chance of malformed JSON. Gemini Flash
    # has been observed to emit unterminated strings mid-response,
    # especially when serializing long Thai text. The retry hint tells the
    # model what specifically went wrong.
    _RETRY_HINT_BASE = (
        "\n\nIMPORTANT — your previous response was invalid JSON. Common "
        "failure modes:\n"
        "  1. Unterminated string (missing closing double-quote)\n"
        "  2. Unescaped newline inside a string value\n"
        "  3. Missing comma between fields\n"
        "  4. Trailing comma after last field\n"
        "Output exactly ONE complete JSON object. Close every string with a "
        "double-quote. Replace any literal newlines inside string values with "
        "spaces. Do NOT use markdown code fences. Do NOT add commentary "
        "before or after the JSON."
    )

    for attempt in range(max_retries + 1):
        # B2 fix: on retry, augment the user prompt with JSON hygiene rules
        if attempt == 0:
            current_user_prompt = base_user_prompt
        else:
            current_user_prompt = (
                base_user_prompt
                + _RETRY_HINT_BASE
                + f"\n\nPrevious parse error: {last_parse_error}"
            )
        try:
            response = model.generate_content(
                [_SYSTEM_PROMPT, pil_image, current_user_prompt],
                request_options={"timeout": timeout},
            )
        except Exception as e:
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
        except Exception:  # pragma: no cover (defensive)
            pass

        if not raw:
            last_parse_error = "empty response"
            last_raw_preview = ""
            logger.warning(
                "layer3: empty response (attempt %d/%d)",
                attempt + 1,
                max_retries + 1,
            )
            if attempt < max_retries:
                continue
            raise Layer3FallbackError(
                f"layer3: Gemini returned empty response after " f"{max_retries + 1} attempts"
            )

        try:
            data = _parse_json(raw)
        except json.JSONDecodeError as e:
            last_parse_error = str(e)
            last_raw_preview = raw[:300]
            logger.warning(
                "layer3: JSON parse failed (attempt %d/%d): %s; raw[:200]=%r",
                attempt + 1,
                max_retries + 1,
                e,
                raw[:200],
            )
            if attempt < max_retries:
                continue
            raise Layer3FallbackError(
                f"layer3: Gemini returned invalid JSON after "
                f"{max_retries + 1} attempts: {last_parse_error}; "
                f"raw[:300]={last_raw_preview!r}"
            ) from e

        return data, {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "retries": attempt,
        }

    raise Layer3FallbackError(f"layer3: unreachable; last parse error: {last_parse_error}")


def _parse_json(text: str) -> dict:
    """Parse Gemini's response as JSON, stripping markdown fences if present.

    Mirrors layer2_structure._parse_json; same defensive logic.
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
        raise json.JSONDecodeError(
            f"expected JSON object, got {type(obj).__name__}",
            s,
            0,
        )
    return obj


def _classify_gemini_exception(e: Exception) -> Exception:
    """Translate raw google-generativeai SDK exception into Layer3 hierarchy.

    Mirrors layer2_structure._classify_gemini_exception. We sniff message
    + type name because the SDK's exception classes vary across versions.
    """
    name = type(e).__name__
    msg = str(e)[:400]
    msg_lower = msg.lower()

    if (
        name in ("Unauthenticated", "PermissionDenied")
        or "permission denied" in msg_lower
        or "unauthenticated" in msg_lower
        or "api key not valid" in msg_lower
        or "invalid api key" in msg_lower
        or "403" in msg
        or "401" in msg
    ):
        return Layer3AuthError(f"layer3: auth ({name}): {msg}")

    if (
        name in ("ResourceExhausted",)
        or "429" in msg
        or "quota" in msg_lower
        or "resource_exhausted" in msg_lower
        or "rate limit" in msg_lower
    ):
        return Layer3QuotaError(f"layer3: quota ({name}): {msg}")

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
        return Layer3TransientError(f"layer3: transient ({name}): {msg}")

    return Layer3Error(f"layer3: {name}: {msg}")


# ============================================================
# Model lazy singleton (keyed by api_key + model_name)
# ============================================================
_model_cache: dict = {}
_model_lock = threading.Lock()


def _get_model(api_key: str, model_name: str):
    """Return a GenerativeModel for the given (api_key, model_name).

    Cached up to 10 distinct combinations. Same pattern as layer 2.
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
                "layer3: google-generativeai required. " "Install: pip install google-generativeai"
            ) from e

        # Direct endpoint (no Cloudflare proxy). If/when dev machine cannot
        # reach generativelanguage.googleapis.com, plumb a proxy via env var.
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
                "response_mime_type": "application/json",
            },
        )

        if len(_model_cache) >= 10:
            _model_cache.pop(next(iter(_model_cache)))
        _model_cache[cache_key] = model

        logger.info("layer3: GenerativeModel initialized: %s", model_name)
        return model
