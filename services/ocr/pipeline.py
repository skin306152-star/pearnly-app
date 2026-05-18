# -*- coding: utf-8 -*-
"""
services/ocr/pipeline.py

Pipeline: orchestrate layer 1 + layer 2 + layer 3 for a complete OCR task.

What the pipeline does per page:
    1. Renders the page to PNG bytes (PDF input) / takes image bytes (image input)
    2. Runs layer 1 (Vision API): OCR text + word-level confidence + bboxes
    3. Runs layer 2 (Flash-Lite): text -> ThaiInvoice fields
    4. Evaluates trigger conditions (see _evaluate_triggers)
    5. Runs layer 3 (Flash visual fallback) ONLY for triggered pages
    6. Returns a unified PipelinePageResult per page + aggregate cost / latency

Trigger conditions (any one fires layer 3):
    - layer 1 page avg_confidence < CONFIDENCE_THRESHOLD (default 0.85)
    - layer 2 missing critical fields (invoice_number / total_amount)
    - amount math fails: |subtotal + vat - total_amount| > AMOUNT_TOLERANCE_THB
    - tax_id format invalid (non-empty but not 13 digits)
    - exception: `is_not_invoice=True` short-circuits — never trigger L3

Cost accounting (Gemini pricing as of 2026; updated to THB via THB_PER_USD):
    - Vision DOCUMENT_TEXT_DETECTION: $0.00150 / page (1000 free/month, ignored here)
    - Flash-Lite: $0.10/M input, $0.40/M output
    - Flash:      $0.30/M input, $2.50/M output

Public API:
    run_on_path(path, ...)         -> PipelineResult
    run_on_pdf_bytes(bytes, ...)   -> PipelineResult
    run_on_image_bytes(bytes, ...) -> PipelineResult

Env (all optional):
    OCR_PIPELINE_CONF_THRESHOLD   default 0.85
    OCR_PIPELINE_AMOUNT_TOL       default 0.5 (THB)
    OCR_PIPELINE_THB_PER_USD      default 35
    GOOGLE_APPLICATION_CREDENTIALS (required, for layer 1 / Vision)
    GOOGLE_API_KEY or GEMINI_API_KEY (required, for layers 2 + 3)

This module does NOT integrate with app.py. The integration (single
feature-flag swap of the 4 OCR entry points) is migration-plan step.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from .confidence import (
    check_field_in_l1_text,
    find_field_min_word_conf,
)
from .layer1_vision import (
    Layer1PDFError,
    extract_from_image_bytes as _l1_extract_image,
)
from .layer2_structure import (
    Layer2Error,
    extract_from_page as _l2_extract_page,
)
from .layer3_fallback import (
    Layer3AuthError,
    Layer3Error,
    Layer3FallbackError,
    Layer3QuotaError,
    Layer3TransientError,
    refine_page as _l3_refine_page,
)
from .schemas import (
    Page,
    PipelinePageResult,
    PipelineResult,
    ThaiInvoice,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants / env-tunable thresholds
# ============================================================
CONFIDENCE_THRESHOLD = float(os.environ.get("OCR_PIPELINE_CONF_THRESHOLD", "0.85"))
AMOUNT_TOLERANCE_THB = float(os.environ.get("OCR_PIPELINE_AMOUNT_TOL", "0.5"))
THB_PER_USD = float(os.environ.get("OCR_PIPELINE_THB_PER_USD", "35"))

# Template (invoice_number prefix) familiarity check — minimum seen instances
# before flagging a new pattern as anomalous, to avoid flagging the first
# invoice ever for a given seller.
MIN_INSTANCES_BEFORE_FLAGGING = int(
    os.environ.get("OCR_PIPELINE_PATTERN_MIN_INSTANCES", "2")
)

# Critical fields whose word-level confidence we check (B1 fix: replaces the
# page-avg confidence trigger which was too coarse).
CRITICAL_FIELDS = ("invoice_number", "total_amount", "seller_tax")
# date is checked separately because date_raw / date might both be present

# Gemini pricing (USD per 1M tokens unless noted). Update if Google changes pricing.
# Source: architecture.md §三 cost table back-calculated to per-token rates.
COST_VISION_PER_PAGE_USD = 0.00150
COST_FLASHLITE_INPUT_PER_M_USD = 0.10
COST_FLASHLITE_OUTPUT_PER_M_USD = 0.40
COST_FLASH_INPUT_PER_M_USD = 0.30
COST_FLASH_OUTPUT_PER_M_USD = 2.50

DEFAULT_DPI = 200
DEFAULT_MAX_PAGES = 50

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp", ".gif"}
PDF_EXTENSIONS = {".pdf"}


# ============================================================
# Invoice number pattern memory (B1 fix part: template familiarity)
# ============================================================
class InvoicePatternMemory:
    """Tracks invoice_number prefix patterns per seller_tax to catch anomalies.

    Pattern extraction: leading letters + up to 4 leading digits before any
    non-alphanumeric separator. Examples:
        IV69/00271  -> 'IV69'   (letters + 2 digits, stops at `/`)
        IV69100179  -> 'IV6910' (no separator; 4 digits captured)
        IV60/00304  -> 'IV60'   (different from IV69!)
        INV2026030204 -> 'INV2026'
        INV2026030002 -> 'INV2026'

    Anomaly logic: only flag if the seller_tax has been seen with >=
    MIN_INSTANCES_BEFORE_FLAGGING different invoices already (baseline
    built). Brand-new sellers don't get flagged.

    Current scope: in-memory only, per-Pipeline-process. For production
    integration with app.py, this can be initialized from
    db.get_seller_recent_invoices(seller_tax) or similar.
    """

    _PREFIX_RE = re.compile(r"^([A-Za-z]+)(\d{0,4})")

    def __init__(self):
        self._patterns: Dict[str, Set[str]] = {}
        self._instance_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    @classmethod
    def _extract_pattern(cls, invoice_number: str) -> Optional[str]:
        """Returns canonical pattern or None if no clean prefix."""
        if not invoice_number:
            return None
        m = cls._PREFIX_RE.match(invoice_number)
        if not m or not m.group(1):
            return None
        return (m.group(1) + m.group(2)).upper()

    def record(self, seller_tax: Optional[str], invoice_number: Optional[str]) -> None:
        """Record that this seller_tax issued an invoice with this pattern.

        Called after every page is processed. We deliberately record AFTER
        the (possibly-L3-corrected) final invoice, so the memory learns
        the corrected values.
        """
        if not seller_tax or not invoice_number:
            return
        pattern = self._extract_pattern(invoice_number)
        if not pattern:
            return
        with self._lock:
            self._patterns.setdefault(seller_tax, set()).add(pattern)
            self._instance_counts[seller_tax] = self._instance_counts.get(seller_tax, 0) + 1

    def check_anomaly(
        self,
        seller_tax: Optional[str],
        invoice_number: Optional[str],
    ) -> Optional[str]:
        """Return a trigger-reason string if pattern doesn't match any
        previously seen pattern for this seller_tax. None = OK or no baseline.

        Skips check if (a) inputs empty, (b) less than
        MIN_INSTANCES_BEFORE_FLAGGING invoices seen for this seller_tax.
        """
        if not seller_tax or not invoice_number:
            return None
        new_pattern = self._extract_pattern(invoice_number)
        if not new_pattern:
            return None
        with self._lock:
            known = self._patterns.get(seller_tax)
            instance_count = self._instance_counts.get(seller_tax, 0)
            if not known or instance_count < MIN_INSTANCES_BEFORE_FLAGGING:
                return None
            if new_pattern in known:
                return None
            return (
                f"invoice_number {invoice_number!r} pattern={new_pattern!r} "
                f"differs from known patterns {sorted(known)} for seller_tax "
                f"{seller_tax} ({instance_count} prior invoices)"
            )


# ============================================================
# Public API
# ============================================================
def run_on_path(
    path: Union[str, Path],
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    api_key: Optional[str] = None,
    enable_layer3: bool = True,
    fallback_to_layer2_on_layer3_error: bool = True,
    pattern_memory: Optional[InvoicePatternMemory] = None,
) -> PipelineResult:
    """End-to-end pipeline on a file path (auto-detects PDF vs image).

    Args:
        path: file path (PDF or image)
        max_pages: max pages to process from PDF (default 50)
        dpi: DPI for PDF page render (default 200; architecture.md §7.5)
        api_key: Gemini API key override (else from env GOOGLE_API_KEY / GEMINI_API_KEY)
        enable_layer3: disable to test L1+L2 only (default True)
        fallback_to_layer2_on_layer3_error: when L3 fails (Layer3FallbackError,
            quota, transient), keep L2's invoice and mark needs_manual_review.
            False = re-raise the L3 exception.

    Returns:
        PipelineResult with per-page details + aggregate cost

    Raises:
        FileNotFoundError: path not found
        ValueError: unsupported extension
        Layer1PDFError / Layer1AuthError / etc.: layer 1 failures (always propagate)
        Layer2AuthError / Layer2QuotaError / Layer2TransientError / Layer2Error:
            layer 2 failures (always propagate)
        Layer3AuthError: always propagate (auth not recoverable)
        Layer3FallbackError / Layer3QuotaError / Layer3TransientError:
            if fallback_to_layer2_on_layer3_error=False, propagate; else captured
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"pipeline: file not found: {p}")
    file_bytes = p.read_bytes()
    ext = p.suffix.lower()
    if ext in PDF_EXTENSIONS:
        return run_on_pdf_bytes(
            file_bytes,
            max_pages=max_pages,
            dpi=dpi,
            api_key=api_key,
            enable_layer3=enable_layer3,
            fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
            pattern_memory=pattern_memory,
        )
    if ext in IMAGE_EXTENSIONS:
        return run_on_image_bytes(
            file_bytes,
            api_key=api_key,
            enable_layer3=enable_layer3,
            fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
            pattern_memory=pattern_memory,
        )
    raise ValueError(
        f"pipeline: unsupported extension {ext!r}; "
        f"supported: {sorted(PDF_EXTENSIONS | IMAGE_EXTENSIONS)}"
    )


def run_on_pdf_bytes(
    pdf_bytes: bytes,
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    api_key: Optional[str] = None,
    enable_layer3: bool = True,
    fallback_to_layer2_on_layer3_error: bool = True,
    pattern_memory: Optional[InvoicePatternMemory] = None,
) -> PipelineResult:
    """Run pipeline on PDF bytes.

    Pipeline owns the PDF -> image rendering (so the image bytes are
    available for layer 3 without re-rendering).
    """
    if not pdf_bytes:
        raise Layer1PDFError("pipeline: empty PDF bytes")

    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "pipeline: PyMuPDF (fitz) required for PDF rendering"
        ) from e

    t0 = time.time()
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise Layer1PDFError(
            f"pipeline: cannot open PDF: {type(e).__name__}: {e}"
        ) from e

    page_image_bytes_list: List[bytes] = []
    try:
        total = doc.page_count
        if total == 0:
            raise Layer1PDFError("pipeline: PDF has 0 pages")
        process = min(total, max_pages)
        if total > max_pages:
            logger.warning(
                "pipeline: PDF has %d pages, processing first %d", total, max_pages
            )
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        for i in range(process):
            try:
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                page_image_bytes_list.append(pix.tobytes("png"))
            except Exception as e:
                raise Layer1PDFError(
                    f"pipeline: render page {i + 1}/{total} failed: "
                    f"{type(e).__name__}: {e}"
                ) from e
    finally:
        doc.close()

    page_results: List[PipelinePageResult] = []
    for i, image_bytes in enumerate(page_image_bytes_list, start=1):
        pr = _process_one_page(
            image_bytes,
            page_number=i,
            api_key=api_key,
            enable_layer3=enable_layer3,
            fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
            pattern_memory=pattern_memory,
        )
        page_results.append(pr)

    elapsed_ms = int((time.time() - t0) * 1000)
    cost_thb = _compute_total_cost(page_results)
    return PipelineResult(
        pages=page_results,
        page_count=len(page_results),
        elapsed_ms=elapsed_ms,
        estimated_cost_thb=cost_thb,
    )


def run_on_image_bytes(
    image_bytes: bytes,
    api_key: Optional[str] = None,
    enable_layer3: bool = True,
    fallback_to_layer2_on_layer3_error: bool = True,
    pattern_memory: Optional[InvoicePatternMemory] = None,
) -> PipelineResult:
    """Run pipeline on a single image's bytes (PNG / JPG / WEBP / etc.)."""
    if not image_bytes:
        raise ValueError("pipeline: empty image bytes")

    t0 = time.time()
    pr = _process_one_page(
        image_bytes,
        page_number=1,
        api_key=api_key,
        enable_layer3=enable_layer3,
        fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
        pattern_memory=pattern_memory,
    )
    elapsed_ms = int((time.time() - t0) * 1000)
    cost_thb = _compute_total_cost([pr])
    return PipelineResult(
        pages=[pr],
        page_count=1,
        elapsed_ms=elapsed_ms,
        estimated_cost_thb=cost_thb,
    )


# ============================================================
# Internal: per-page orchestration
# ============================================================
def _process_one_page(
    image_bytes: bytes,
    page_number: int,
    api_key: Optional[str],
    enable_layer3: bool,
    fallback_to_layer2_on_layer3_error: bool,
    pattern_memory: Optional[InvoicePatternMemory] = None,
) -> PipelinePageResult:
    """L1 -> L2 -> (maybe L3) for ONE page. Captures cost / latency / errors."""
    t_total = time.time()

    # --- Layer 1 ---
    t_l1 = time.time()
    l1_result = _l1_extract_image(image_bytes, page_number=page_number)
    l1_ms = int((time.time() - t_l1) * 1000)
    l1_page = l1_result.pages[0]

    # --- Layer 2 ---
    t_l2 = time.time()
    l2_result = _l2_extract_page(l1_page, api_key=api_key)
    l2_ms = int((time.time() - t_l2) * 1000)
    l2_invoice = l2_result.invoice

    # --- Trigger evaluation ---
    triggers = _evaluate_triggers(l1_page, l2_invoice, pattern_memory)

    # --- Layer 3 (conditional) ---
    invoice = l2_invoice
    layer_chain = ["L1", "L2"]
    l3_in_tokens = 0
    l3_out_tokens = 0
    l3_ms = 0
    needs_manual_review = False
    error_msg: Optional[str] = None

    if triggers and enable_layer3:
        try:
            l3_result = _l3_refine_page(
                image_bytes=image_bytes,
                layer1_page=l1_page,
                layer2_invoice=l2_invoice,
                trigger_reasons=triggers,
                api_key=api_key,
            )
            invoice = l3_result.invoice
            layer_chain = ["L1", "L2", "L3"]
            l3_in_tokens = l3_result.input_tokens
            l3_out_tokens = l3_result.output_tokens
            l3_ms = l3_result.elapsed_ms
        except Layer3AuthError:
            # Auth is never retryable / never fall-back-able — propagate
            raise
        except Layer3FallbackError as e:
            error_msg = f"L3 fallback error: {e}"
            logger.warning(
                "pipeline: L3 fallback error on page %d: %s", page_number, e
            )
            if fallback_to_layer2_on_layer3_error:
                layer_chain = ["L1", "L2", "L3_failed"]
                needs_manual_review = True
            else:
                raise
        except Layer3QuotaError as e:
            error_msg = f"L3 quota: {e}"
            logger.warning("pipeline: L3 quota on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = ["L1", "L2", "L3_quota"]
                needs_manual_review = True
            else:
                raise
        except Layer3TransientError as e:
            error_msg = f"L3 transient: {e}"
            logger.warning(
                "pipeline: L3 transient on page %d: %s", page_number, e
            )
            if fallback_to_layer2_on_layer3_error:
                layer_chain = ["L1", "L2", "L3_transient"]
                needs_manual_review = True
            else:
                raise
        except Layer3Error as e:
            # Other L3 errors — log + recover (same as fallback) to keep pipeline going
            error_msg = f"L3 error: {e}"
            logger.warning("pipeline: L3 error on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = ["L1", "L2", "L3_failed"]
                needs_manual_review = True
            else:
                raise

    total_ms = int((time.time() - t_total) * 1000)

    # Record final invoice pattern in pattern memory (after possible L3
    # correction). Subsequent pages benefit from this learned baseline.
    if pattern_memory is not None and not invoice.is_not_invoice:
        pattern_memory.record(invoice.seller_tax, invoice.invoice_number)

    return PipelinePageResult(
        page_number=page_number,
        invoice=invoice,
        layer_chain=layer_chain,
        trigger_reasons=triggers,
        layer1_avg_confidence=l1_page.avg_confidence,
        layer2_input_tokens=l2_result.input_tokens,
        layer2_output_tokens=l2_result.output_tokens,
        layer3_input_tokens=l3_in_tokens,
        layer3_output_tokens=l3_out_tokens,
        layer1_ms=l1_ms,
        layer2_ms=l2_ms,
        layer3_ms=l3_ms,
        total_ms=total_ms,
        needs_manual_review=needs_manual_review,
        error=error_msg,
    )


# ============================================================
# Internal: trigger logic
# ============================================================
def _evaluate_triggers(
    page: Page,
    invoice: ThaiInvoice,
    pattern_memory: Optional[InvoicePatternMemory] = None,
) -> List[str]:
    """Return list of trigger reason strings; empty list = layer 3 not needed.

    Exception: if invoice.is_not_invoice == True, return [] (no point sending
    a non-invoice through layer 3 visual review).

    Trigger rules (B1 fix replaces page-avg confidence with word-level
    per-critical-field confidence + L1-text containment check + pattern
    familiarity check):

    1. Critical fields missing (invoice_number, total_amount)
    2. Amount math fail (subtotal + vat != total)
    3. seller_tax format invalid (non-empty but not 13 digits)
    4. (NEW) Per-critical-field word-level confidence < threshold —
       finds matching L1 words and checks their min confidence. Catches
       things like Vision misreading `/` as `1` where the page average
       still looks high.
    5. (NEW) L1 text containment — extracted value does not appear in L1
       full_text (suggests layer 2 hallucinated the value).
    6. (NEW) Invoice pattern anomaly — extracted invoice_number prefix
       differs from previously seen patterns for this seller_tax.
    """
    if invoice.is_not_invoice:
        return []

    triggers: List[str] = []

    # Rule 1: critical fields missing
    if not invoice.invoice_number:
        triggers.append("invoice_number missing")
    if not invoice.total_amount:
        triggers.append("total_amount missing")

    # Rule 2: amount math
    math_reason = _check_amount_math(invoice)
    if math_reason:
        triggers.append(math_reason)

    # Rule 3: tax_id format
    if invoice.seller_tax:
        if not invoice.seller_tax.isdigit() or len(invoice.seller_tax) != 13:
            triggers.append(
                f"seller_tax format invalid: {invoice.seller_tax!r} "
                "(expected 13 digits)"
            )

    # Rule 4 (NEW): per-critical-field word-level confidence
    # For each non-empty critical field, find matching L1 words and check
    # their min confidence.
    for field_name in CRITICAL_FIELDS:
        value = getattr(invoice, field_name, None)
        if not value:
            continue  # missing was already caught by rule 1
        min_conf = find_field_min_word_conf(page, value)
        if min_conf is None:
            # No L1 word matched — handled by rule 5 below
            continue
        if min_conf < CONFIDENCE_THRESHOLD:
            triggers.append(
                f"{field_name}={value!r} word min conf {min_conf:.3f} "
                f"< threshold {CONFIDENCE_THRESHOLD}"
            )

    # Rule 4b: date — same check using date_raw (as printed) if available,
    # else the normalized date string
    date_val = invoice.date_raw or invoice.date
    if date_val:
        min_conf = find_field_min_word_conf(page, date_val)
        if min_conf is not None and min_conf < CONFIDENCE_THRESHOLD:
            triggers.append(
                f"date={date_val!r} word min conf {min_conf:.3f} "
                f"< threshold {CONFIDENCE_THRESHOLD}"
            )

    # Rule 5 (NEW): L1 containment — non-empty extracted critical fields
    # must appear in L1's full_text (after whitespace+comma normalization).
    # If absent, layer 2 likely hallucinated.
    for field_name in CRITICAL_FIELDS:
        value = getattr(invoice, field_name, None)
        if not value:
            continue
        if not check_field_in_l1_text(page, value):
            triggers.append(
                f"{field_name}={value!r} not found in L1 OCR text "
                "(possibly hallucinated by layer 2)"
            )

    # Rule 6 (NEW): template / pattern familiarity. Skipped silently if no
    # memory passed in or no baseline yet.
    if pattern_memory is not None and invoice.invoice_number:
        anomaly = pattern_memory.check_anomaly(
            invoice.seller_tax, invoice.invoice_number
        )
        if anomaly:
            triggers.append(anomaly)

    return triggers


def _check_amount_math(invoice: ThaiInvoice) -> Optional[str]:
    """Returns a trigger reason string if subtotal + vat != total within
    AMOUNT_TOLERANCE_THB, else None. If any of the 3 fields can't be parsed
    as a number, returns None (don't fire false trigger on a missing field —
    missing fields are caught by the dedicated checks)."""
    try:
        sub = float(invoice.subtotal) if invoice.subtotal else None
        vat = float(invoice.vat) if invoice.vat else None
        total = float(invoice.total_amount) if invoice.total_amount else None
    except (ValueError, TypeError):
        return "amount field not numeric (parse failed)"
    if sub is None or vat is None or total is None:
        return None  # can't check; another rule may fire
    expected = sub + vat
    diff = abs(expected - total)
    if diff > AMOUNT_TOLERANCE_THB:
        return (
            f"amount math fail: subtotal {sub:.2f} + vat {vat:.2f} "
            f"= {expected:.2f} != total {total:.2f} "
            f"(diff {diff:.2f} > {AMOUNT_TOLERANCE_THB})"
        )
    return None


# ============================================================
# Internal: cost
# ============================================================
def _compute_total_cost(page_results: List[PipelinePageResult]) -> float:
    """Sum estimated cost across pages, return THB.

    Notes:
        - Vision $0.00150/page applies even if a page is blank
        - Flash-Lite cost = (input * 0.10 + output * 0.40) / 1M tokens, USD
        - Flash cost = (input * 0.30 + output * 2.50) / 1M tokens, USD
        - Then * THB_PER_USD (default 35)
    """
    total_usd = 0.0
    for pr in page_results:
        # Vision per-page
        total_usd += COST_VISION_PER_PAGE_USD
        # Flash-Lite (always runs)
        total_usd += (pr.layer2_input_tokens / 1_000_000.0) * COST_FLASHLITE_INPUT_PER_M_USD
        total_usd += (pr.layer2_output_tokens / 1_000_000.0) * COST_FLASHLITE_OUTPUT_PER_M_USD
        # Flash (only if L3 ran successfully — tokens > 0 means it ran)
        if pr.layer3_input_tokens or pr.layer3_output_tokens:
            total_usd += (pr.layer3_input_tokens / 1_000_000.0) * COST_FLASH_INPUT_PER_M_USD
            total_usd += (pr.layer3_output_tokens / 1_000_000.0) * COST_FLASH_OUTPUT_PER_M_USD
    return total_usd * THB_PER_USD
