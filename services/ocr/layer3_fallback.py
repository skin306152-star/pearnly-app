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
import time
from typing import List, Optional, Tuple

from pydantic import ValidationError

from .gemini_models import fallback as _ocr_fallback
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
# Layer3 是 OCR pipeline 的升级兜底档(layer1+2 低置信才到此)· 用更强模型兜底
# (默认 gemini-3.5-flash)· OCR_FALLBACK_MODEL="" 时退回 OCR_FLASH_MODEL。
DEFAULT_MODEL = _ocr_fallback() or os.environ.get("OCR_FLASH_MODEL", "gemini-2.5-flash")
DEFAULT_MAX_RETRIES = 1
# L3 timeout. History (doc 09): 90s was effectively unbounded; §3.3 then cut it to
# 15s for speed — but real L3 on thermal receipts needs 15–60s, so legitimate
# rescues (Punthai amount-fix ran 15.7s; "total missing" re-reads) got cut off and
# fell back to L2's wrong/empty value + needs_review = the accuracy regression.
# Triggers are already tightened (most receipts never reach L3), so a generous
# timeout only affects the few genuine rescues without slowing the common path.
# On timeout the caller still falls back to L2 + needs_review (never silent).
# Overridable via env for prod A/B without a code change.
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("OCR_L3_TIMEOUT_SECONDS", "45"))
# DEFAULT_TEMPERATURE / DEFAULT_MAX_OUTPUT_TOKENS → services/ocr/layer3_gemini.py(模块化深化)。

# Truncate layer 1 OCR text to avoid bloating the prompt on large pages.
# Layer 3 has the IMAGE for ground truth; OCR text is just a hint.
MAX_TEXT_LENGTH = 20000

from services.ocr.layer3_gemini import (  # noqa: F401 · re-export + refine 用
    Layer3Error,
    Layer3FallbackError,
    Layer3AuthError,
    Layer3QuotaError,
    Layer3TransientError,
    _parse_json,
    _classify_gemini_exception,
    _get_model,
)

# Layer3 异常类 → services/ocr/layer3_gemini.py(模块化深化)· 下方 re-import 回。


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
  "additional_invoices": [],
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
3. ITEMS: You can SEE the image — read EVERY line item top to bottom, miss none. Thermal/POS
   receipts wrap one item over 2-3 lines (name, then qty x unit-price, then line total); stitch
   them into ONE item (name, qty, price, subtotal). Count a row as an item only if it has a
   product/service name; SKIP subtotal / VAT / total / change / cash / discount / table-no /
   thank-you rows. Self-check: item subtotals should build toward the document subtotal — if you
   have fewer items than the receipt visibly lists, re-scan for missed rows. Keep ONE copy if the
   same name+qty+price is genuinely duplicated.
4. NUMBERS: No currency symbols, no commas (e.g., "12450.00").
5. TAX IDs: Exactly 13 digits, no dashes/spaces. Empty string if not found.
6. WHT: Common rates 1/2/3/5%. wht_rate is the number ONLY ("3" not "3%").
7. AMOUNT ARITHMETIC: When trigger reasons mention amount mismatch, look carefully at subtotal/vat/total in the image. The correct relationship is: subtotal + vat = total_amount (within rounding tolerance).
8. is_not_invoice: true ONLY if clearly not an invoice. A FUEL/PETROL receipt (Bangchak/PTT/Shell ·
   น้ำมัน/ดีเซล/liters+total) IS a receipt (TID/BATCH/TRACE = POS footer, NOT a reason to drop); is_not_invoice only for a bare card slip with no goods & no seller tax id.
9. is_copy_or_duplicate: true if the text contains สำเนา / COPY / DUPLICATE markers.
10. MULTIPLE INVOICES ON ONE PAGE (CRITICAL — a trigger reason may say a stacked
    invoice was missed): a single page image often contains TWO OR MORE separate
    tax invoices stacked vertically, each with its OWN invoice number, buyer, and
    total. Look at the WHOLE image top-to-bottom. Put the FIRST (topmost) invoice
    in the top-level fields and EACH remaining invoice as a COMPLETE object in the
    "additional_invoices" array. Every distinct invoice number visible on the page
    MUST appear exactly once (top-level or in additional_invoices) — never merge or
    drop one. Keep nested additional_invoices as []. Only one invoice → leave it [].
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
        model_name: Gemini model id; defaults to DEFAULT_MODEL (OCR_FALLBACK_MODEL,
            i.e. gemini-3.5-flash — layer 3 is the strong-model escalation tier)
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


# Gemini 传输层(_parse_json/_classify_gemini_exception/_get_model)→ services/ocr/layer3_gemini.py(模块化深化)。
