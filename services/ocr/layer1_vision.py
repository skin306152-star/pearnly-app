# -*- coding: utf-8 -*-
"""
services/ocr/layer1_vision.py

Layer 1 of the new OCR pipeline: Google Cloud Vision API character recognition.

This module is the first real business module of the new architecture
(architecture.md). It calls Vision DOCUMENT_TEXT_DETECTION on each page of a
PDF (or a single image) and returns a structured Layer1Result containing
full text, every word's confidence, and bounding boxes — everything layer 2
(Flash-Lite field extraction) and layer 3 (Flash visual fallback) need.

Key design choices:
- PDF rendering via PyMuPDF (already a project dependency, used by
  gemini_engine.py and vision_engine.py)
- Vision API direct call to vision.googleapis.com (no Cloudflare proxy;
  verified by services/ocr/connectivity_check.py on both local and server)
- DPI 200 by default (architecture.md §7.5 recommendation for dense text)
- Language hints ["th", "en"] (Thai invoices are typically bilingual)
- No business logic, no retry, no fallback — those belong in pipeline.py
- Lazy singleton client (avoid reconnect cost across pages of one PDF)
- Custom exception hierarchy lets pipeline.py dispatch on error category

Public API:
    extract_from_path(path, ...)         -> Layer1Result
    extract_from_pdf_bytes(bytes, ...)   -> Layer1Result
    extract_from_image_bytes(bytes, ...) -> Layer1Result

Custom exceptions (all subclass Layer1Error):
    Layer1AuthError       (credentials / billing / permission, NOT retryable)
    Layer1QuotaError      (quota / rate-limit exceeded, retry after backoff)
    Layer1TransientError  (timeout / 5xx / network, potentially retryable)
    Layer1PDFError        (PDF cannot be parsed or rendered)
    Layer1Error           (everything else / unknown)

Environment:
    GOOGLE_APPLICATION_CREDENTIALS   path to Service Account JSON; required
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Union

from .schemas import (
    BoundingBox,
    Block,
    Layer1Result,
    Page,
    Paragraph,
    Word,
)

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================
DEFAULT_DPI = 200
DEFAULT_MAX_PAGES = 50
DEFAULT_LANGUAGE_HINTS: List[str] = ["th", "en"]
DEFAULT_TIMEOUT_SECONDS = 60

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp", ".gif"}
PDF_EXTENSIONS = {".pdf"}


# ============================================================
# Exception hierarchy
# ============================================================
class Layer1Error(Exception):
    """Base exception for layer 1 OCR errors. Catch this to handle any
    layer-1 failure generically; use subclasses for targeted dispatch."""


class Layer1AuthError(Layer1Error):
    """Credentials / authentication / billing / permission failure.

    NOT retryable — usually means GOOGLE_APPLICATION_CREDENTIALS is wrong,
    the project has billing disabled, or the Service Account lacks the
    Cloud Vision AI Service Agent role.
    """


class Layer1QuotaError(Layer1Error):
    """Quota or rate-limit exceeded. Retry after backoff."""


class Layer1TransientError(Layer1Error):
    """Network / timeout / 5xx error. Potentially retryable."""


class Layer1PDFError(Layer1Error):
    """PDF cannot be opened or rendered (corrupted, password-protected, etc.)."""


# ============================================================
# Public API
# ============================================================
def extract_from_path(
    path: Union[str, Path],
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    language_hints: Optional[List[str]] = None,
) -> Layer1Result:
    """Extract text + confidence + bboxes from a PDF or image file on disk.

    Auto-detects PDF vs image by file extension (see PDF_EXTENSIONS and
    IMAGE_EXTENSIONS module constants).

    Args:
        path: filesystem path to a PDF or image file
        max_pages: skip pages beyond this count (PDF only); default 50
        dpi: render DPI for PDF→image conversion (PDF only); default 200
        language_hints: Vision API language hints; defaults to ["th", "en"]

    Returns:
        Layer1Result with one Page per input page

    Raises:
        FileNotFoundError: path does not exist
        ValueError: unsupported file extension
        Layer1PDFError: PDF cannot be parsed or rendered
        Layer1AuthError, Layer1QuotaError, Layer1TransientError, Layer1Error
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"layer1: file not found: {p}")
    if not p.is_file():
        raise ValueError(f"layer1: path is not a file: {p}")

    ext = p.suffix.lower()
    file_bytes = p.read_bytes()

    if ext in PDF_EXTENSIONS:
        return extract_from_pdf_bytes(
            file_bytes,
            max_pages=max_pages,
            dpi=dpi,
            language_hints=language_hints,
        )
    if ext in IMAGE_EXTENSIONS:
        return extract_from_image_bytes(
            file_bytes,
            page_number=1,
            language_hints=language_hints,
        )

    raise ValueError(
        f"layer1: unsupported file extension {ext!r}; "
        f"supported: {sorted(PDF_EXTENSIONS | IMAGE_EXTENSIONS)}"
    )


def extract_from_pdf_bytes(
    pdf_bytes: bytes,
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    language_hints: Optional[List[str]] = None,
) -> Layer1Result:
    """Extract from raw PDF bytes.

    Each page is rendered to PNG at the given DPI via PyMuPDF, then sent to
    Vision API DOCUMENT_TEXT_DETECTION individually. Vision's batch /
    async PDF endpoints are NOT used here — they require GCS-hosted files
    and add operational complexity not justified at this layer.

    Args:
        pdf_bytes: raw PDF file bytes
        max_pages: cap on number of pages; pages beyond are silently skipped
            with a warning. PDF with 0 pages raises Layer1PDFError.
        dpi: render resolution; 200 is a good balance between accuracy and
            cost. Lower (100-150) saves cost but hurts dense-text accuracy.
        language_hints: Vision API language hints; defaults to ["th", "en"]

    Returns:
        Layer1Result with one Page per processed PDF page

    Raises:
        Layer1PDFError: PDF cannot be opened, has 0 pages, or render fails
        Layer1AuthError / Layer1QuotaError / Layer1TransientError / Layer1Error
            on Vision API failure for any page
    """
    if not pdf_bytes:
        raise Layer1PDFError("layer1: empty PDF bytes")

    lang_hints = list(language_hints) if language_hints else list(DEFAULT_LANGUAGE_HINTS)

    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "layer1: PyMuPDF (fitz) required for PDF rendering. "
            "Install: pip install pymupdf"
        ) from e

    t0 = time.time()

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise Layer1PDFError(
            f"layer1: cannot open PDF: {type(e).__name__}: {e}"
        ) from e

    try:
        total_pages = doc.page_count
        if total_pages == 0:
            raise Layer1PDFError("layer1: PDF has 0 pages")

        process_count = min(total_pages, max_pages)
        if total_pages > max_pages:
            logger.warning(
                "layer1: PDF has %d pages, processing first %d only",
                total_pages,
                max_pages,
            )

        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pages: List[Page] = []
        for i in range(process_count):
            try:
                fitz_page = doc.load_page(i)
                pix = fitz_page.get_pixmap(matrix=matrix, alpha=False)
                png_bytes = pix.tobytes("png")
            except Exception as e:
                raise Layer1PDFError(
                    f"layer1: render page {i + 1}/{total_pages} failed: "
                    f"{type(e).__name__}: {e}"
                ) from e

            page_result = _call_vision_for_image(
                png_bytes,
                page_number=i + 1,
                language_hints=lang_hints,
            )
            pages.append(page_result)
    finally:
        doc.close()

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info(
        "layer1: PDF done: %d page(s), %dms, avg_confidence=%.3f, dpi=%d",
        len(pages),
        elapsed_ms,
        _overall_avg_confidence(pages),
        dpi,
    )
    return Layer1Result(
        pages=pages,
        page_count=len(pages),
        elapsed_ms=elapsed_ms,
        language_hints=lang_hints,
        dpi=dpi,
    )


def extract_from_image_bytes(
    image_bytes: bytes,
    page_number: int = 1,
    language_hints: Optional[List[str]] = None,
) -> Layer1Result:
    """Extract from a single image's bytes (PNG / JPG / WEBP / etc.).

    Wraps the result in Layer1Result for API symmetry with PDF. `dpi` is set
    to 0 in the result since no rendering happened.

    Args:
        image_bytes: raw image file bytes (any format Vision accepts)
        page_number: page_number to assign to the resulting Page (default 1)
        language_hints: Vision API language hints; defaults to ["th", "en"]

    Returns:
        Layer1Result with exactly one Page

    Raises:
        Layer1AuthError / Layer1QuotaError / Layer1TransientError / Layer1Error
    """
    if not image_bytes:
        raise ValueError("layer1: empty image bytes")
    if page_number < 1:
        raise ValueError(f"layer1: page_number must be >= 1, got {page_number}")

    lang_hints = list(language_hints) if language_hints else list(DEFAULT_LANGUAGE_HINTS)
    t0 = time.time()
    page_result = _call_vision_for_image(
        image_bytes,
        page_number=page_number,
        language_hints=lang_hints,
    )
    elapsed_ms = int((time.time() - t0) * 1000)
    return Layer1Result(
        pages=[page_result],
        page_count=1,
        elapsed_ms=elapsed_ms,
        language_hints=lang_hints,
        dpi=0,
    )


# ============================================================
# Internal: Vision API call + proto translation
# ============================================================
def _call_vision_for_image(
    image_bytes: bytes,
    page_number: int,
    language_hints: List[str],
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Page:
    """Single Vision API call → Page.

    Handles known error modes (auth, billing, quota, timeout, transient,
    server) by translating google.api_core exceptions into our Layer1Error
    hierarchy. Empty / blank pages return a Page with empty content (not
    an error — a blank page in a PDF is a legitimate result).
    """
    # Eager env check: clearer error than letting auth fail deep in SDK
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        raise Layer1AuthError(
            "layer1: GOOGLE_APPLICATION_CREDENTIALS env var not set. "
            "Layer 1 requires Service Account credentials. "
            "See migration-plan.md decision 1."
        )

    try:
        from google.cloud import vision
        from google.api_core import exceptions as gax
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "layer1: google-cloud-vision required. "
            "Install: pip install google-cloud-vision"
        ) from e

    client = _get_client()
    image = vision.Image(content=image_bytes)
    image_context = vision.ImageContext(language_hints=language_hints)

    try:
        response = client.document_text_detection(
            image=image,
            image_context=image_context,
            timeout=timeout,
        )
    except gax.Unauthenticated as e:
        raise Layer1AuthError(
            f"layer1: page {page_number}: Unauthenticated: {e}"
        ) from e
    except gax.PermissionDenied as e:
        # Includes BILLING_DISABLED and SA missing IAM role
        raise Layer1AuthError(
            f"layer1: page {page_number}: PermissionDenied: {e}"
        ) from e
    except gax.ResourceExhausted as e:
        raise Layer1QuotaError(
            f"layer1: page {page_number}: quota / rate limit: {e}"
        ) from e
    except gax.DeadlineExceeded as e:
        raise Layer1TransientError(
            f"layer1: page {page_number}: timeout after {timeout}s: {e}"
        ) from e
    except (gax.ServiceUnavailable, gax.InternalServerError) as e:
        raise Layer1TransientError(
            f"layer1: page {page_number}: server error: {type(e).__name__}: {e}"
        ) from e
    except gax.GoogleAPICallError as e:
        raise Layer1Error(
            f"layer1: page {page_number}: API error: {type(e).__name__}: {e}"
        ) from e
    except Exception as e:
        raise Layer1Error(
            f"layer1: page {page_number}: unexpected: {type(e).__name__}: {e}"
        ) from e

    # API-level error embedded in response (rare but possible)
    error = getattr(response, "error", None)
    if error is not None and getattr(error, "code", 0) != 0:
        # Code 7 = PERMISSION_DENIED, 8 = RESOURCE_EXHAUSTED, 4 = DEADLINE_EXCEEDED
        code = error.code
        msg = error.message
        if code in (7, 16):
            raise Layer1AuthError(
                f"layer1: page {page_number}: API error code {code}: {msg}"
            )
        if code == 8:
            raise Layer1QuotaError(
                f"layer1: page {page_number}: API error code {code}: {msg}"
            )
        if code in (4, 13, 14):
            raise Layer1TransientError(
                f"layer1: page {page_number}: API error code {code}: {msg}"
            )
        raise Layer1Error(
            f"layer1: page {page_number}: API error code {code}: {msg}"
        )

    return _response_to_page(response, page_number=page_number)


def _response_to_page(response, page_number: int) -> Page:
    """Translate vision.AnnotateImageResponse into our Page schema.

    Vision API returns `full_text_annotation` with:
        .text                          str   full extracted text
        .pages[0].width / .height      int   image dimensions
        .pages[0].blocks[].paragraphs[].words[].symbols[]
                                              hierarchical structure
                                              each level has .confidence
                                              and .bounding_box.vertices

    We send one image per call so we always pick `full_text_annotation.pages[0]`.
    """
    fta = getattr(response, "full_text_annotation", None)
    if fta is None or not fta.text:
        # Blank page — return empty Page (not an error)
        return Page(
            page_number=page_number,
            width=0,
            height=0,
            full_text="",
            avg_confidence=0.0,
            blocks=[],
        )

    if not fta.pages:
        # Has text but no page structure — return text-only Page
        return Page(
            page_number=page_number,
            width=0,
            height=0,
            full_text=fta.text or "",
            avg_confidence=0.0,
            blocks=[],
        )

    proto_page = fta.pages[0]
    width = int(proto_page.width)
    height = int(proto_page.height)

    all_word_confs: List[float] = []
    blocks: List[Block] = []
    for proto_block in proto_page.blocks:
        paragraphs: List[Paragraph] = []
        for proto_para in proto_block.paragraphs:
            words: List[Word] = []
            for proto_word in proto_para.words:
                # word text = concat of symbol texts
                word_text = "".join(s.text for s in proto_word.symbols)
                word_conf = float(proto_word.confidence)
                all_word_confs.append(word_conf)
                words.append(
                    Word(
                        text=word_text,
                        confidence=word_conf,
                        bbox=_extract_bbox(proto_word.bounding_box),
                    )
                )
            paragraphs.append(
                Paragraph(
                    text=" ".join(w.text for w in words),
                    confidence=float(proto_para.confidence),
                    bbox=_extract_bbox(proto_para.bounding_box),
                    words=words,
                )
            )
        blocks.append(
            Block(
                text="\n".join(p.text for p in paragraphs),
                confidence=float(proto_block.confidence),
                bbox=_extract_bbox(proto_block.bounding_box),
                paragraphs=paragraphs,
            )
        )

    avg_conf = (sum(all_word_confs) / len(all_word_confs)) if all_word_confs else 0.0

    return Page(
        page_number=page_number,
        width=width,
        height=height,
        full_text=fta.text,
        avg_confidence=avg_conf,
        blocks=blocks,
    )


def _extract_bbox(bounding_poly) -> BoundingBox:
    """Convert vision.BoundingPoly to our BoundingBox.

    Vision returns 4 vertices in TL/TR/BR/BL order. In rare edge cases
    (e.g. boxes touching image edge) Vision may return fewer than 4
    vertices; we pad with the last vertex to satisfy our 4-vertex schema.
    """
    vertices = [(int(v.x), int(v.y)) for v in bounding_poly.vertices]
    if not vertices:
        return BoundingBox(vertices=[(0, 0), (0, 0), (0, 0), (0, 0)])
    while len(vertices) < 4:
        vertices.append(vertices[-1])
    return BoundingBox(vertices=vertices[:4])


def _overall_avg_confidence(pages: List[Page]) -> float:
    """Unweighted mean of per-page avg_confidence; 0.0 for empty pages list."""
    if not pages:
        return 0.0
    return sum(p.avg_confidence for p in pages) / len(pages)


# ============================================================
# Client lazy singleton
# ============================================================
_client_cache = None
_client_lock = threading.Lock()


def _get_client():
    """Lazy-singleton vision.ImageAnnotatorClient.

    Subsequent calls reuse the same client across pages of a PDF (avoids
    repeated gRPC handshake cost). Thread-safe via double-checked locking.
    The client itself is documented as thread-safe by google-cloud-vision.
    """
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    with _client_lock:
        if _client_cache is not None:
            return _client_cache
        from google.cloud import vision

        _client_cache = vision.ImageAnnotatorClient()
        logger.info("layer1: ImageAnnotatorClient initialized")
    return _client_cache
