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
from .gemini_models import flash as _ocr_flash
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
DEFAULT_MODEL = _ocr_fallback() or _ocr_flash()
DEFAULT_MAX_RETRIES = 1
# L3 timeout (P1G-Perf · Zihao 2026-06-18). Prod escalates to gemini-2.5-pro,
# which kept hitting the old 45s ceiling then 504 — the user waits the full 45s
# only to fall back to L2 anyway. Cap L3 at 10s; on timeout the caller falls back
# to L2 + needs_review and the card is marked "โปรดตรวจสอบ" (never silent). Trades
# a few slow thermal-receipt rescues for a bounded main path — acceptable now that
# triggers are tightened (tax-id/category-only no longer escalate). Env-overridable.
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("OCR_L3_TIMEOUT_SECONDS", "10"))
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
    _RETRY_HINT_BASE,
    _parse_json,
    _classify_gemini_exception,
    _call_l3_via_gateway,
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
  "discount": "total discount as printed (ส่วนลด), number-as-string, empty if none",
  "total_amount": "FINAL net payable (Total/NET/ยอดสุทธิ), number-as-string or null",
  "cash_amount": "cash tendered (เงินสด/รับเงิน/CASH), empty if not printed",
  "change_amount": "change returned (เงินทอน/ทอน), empty if none",
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

PROVENANCE — fill source_refs for amount + tax-id + date fields with the exact printed column
label of the cell the value came from. Validators reject amounts from Description/Remark/Address.

CRITICAL RULES (same as previous extraction; pay attention):
1. DATE: Buddhist year (>= 2400) MUST be converted to Gregorian by subtracting 543. e.g. 2569 -> 2026. ALWAYS fill date_raw with the original text.
2. NAMES & ADDRESSES: Copy EXACTLY as printed (Thai or English). Do NOT auto-correct or standardize.
3. ITEMS: read EVERY line item top to bottom, miss none. Thermal/POS receipts wrap one item over
   2-3 lines (name, then qty x unit-price, then line total) — stitch into ONE item (name, qty,
   price, subtotal). A row is an item only if it has a product/service name; SKIP subtotal / VAT /
   total / change / cash / discount / table-no / thank-you rows. Self-check: item subtotals should
   build toward the document subtotal. Keep ONE copy if the same name+qty+price is duplicated.
4. NUMBERS: No currency symbols, no commas (e.g., "12450.00").
5. TAX IDs: Exactly 13 digits, no dashes/spaces. Empty string if not found.
6. WHT: Common rates 1/2/3/5%. wht_rate is the number ONLY ("3" not "3%").
7. AMOUNT ARITHMETIC: When trigger reasons mention amount mismatch, look carefully at subtotal/vat/total in the image. The correct relationship is: subtotal + vat = total_amount (within rounding tolerance).
7b. TOTAL vs PAYMENT: total_amount = FINAL net payable (Total/NET/ยอดสุทธิ), AFTER discount, NEVER
   the cash tendered or change. Cash (เงินสด/รับเงิน)→cash_amount, change (เงินทอน/ทอน)→change_amount,
   discount (ส่วนลด)→discount. "ยอดสุทธิ 110 / เงินสด 200 / เงินทอน 90" → total_amount=110 (NOT 200).
8. is_not_invoice: true ONLY if clearly not an invoice. A FUEL/PETROL receipt (Bangchak/PTT/Shell · น้ำมัน/ดีเซล/liters+total) IS a receipt (TID/BATCH/TRACE = POS footer); is_not_invoice only for a bare card slip with no goods & no seller tax id.
9. is_copy_or_duplicate: true if the text contains สำเนา / COPY / DUPLICATE markers.
10. MULTIPLE INVOICES ON ONE PAGE (CRITICAL — a trigger may say a stacked invoice was
    missed): one page can hold TWO+ separate tax invoices stacked vertically, each with its
    OWN invoice number, buyer, total. Scan the WHOLE image top-to-bottom; put the topmost in
    top-level fields and EACH remaining one as a COMPLETE object in "additional_invoices".
    Every distinct invoice number appears exactly once — never merge or drop. Nested
    additional_invoices stay []; one invoice → leave it [].
"""


# 抗锚定:L3 的定位是"看图复核",但把 Vision 全文 + 上一轮 JSON 一起摆进 prompt 后,
# 未被 trigger 点名的字段会被整段照抄 —— 2026-07-20 实测,佛历年 2569 被 Vision 读成
# 2559 时,L3 只修了被点名的金额,日期 0/4 沿用错值;补上本段后同样输入 4/4 读对,
# 金额不受影响。不点名具体字段,只把"图是唯一真相"从隐含期待写成显式规则。
_INDEPENDENT_REREAD = (
    "INDEPENDENT RE-READ (this overrides any habit of copying):\n"
    "The OCR TEXT and PREVIOUS JSON show what an EARLIER pass produced. They are evidence of\n"
    "what may be WRONG, never a source of truth. For EVERY field you output, read the characters\n"
    "off the IMAGE yourself. Where the image and the OCR TEXT disagree, the IMAGE WINS.\n"
    "Single-stroke digit confusions (5/6, 3/8, 0/9, 1/7) are the most common OCR failure and they\n"
    "do NOT look wrong in the text — the Buddhist-era year is the highest-risk field: read its four\n"
    "digits one by one off the image before writing date_raw."
)


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
        f"{_INDEPENDENT_REREAD}\n\n"
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
        timeout: per-API-call timeout in seconds (default DEFAULT_TIMEOUT_SECONDS)

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
    mime = f"image/{(pil_image.format or 'png').lower()}"
    return _call_l3_via_gateway(
        image_bytes,
        mime,
        _SYSTEM_PROMPT,
        base_user_prompt,
        api_key,
        model_name,
        max_retries,
        timeout,
    )


# Gemini 传输层(_parse_json/_classify_gemini_exception)→ services/ocr/layer3_gemini.py(模块化深化)。
