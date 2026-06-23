# -*- coding: utf-8 -*-
"""
services/ocr/pdf_utils.py

Small utility helpers around PDF inspection — used by callers that need
to peek at a PDF without running the full pipeline (e.g., quota / page
count validation BEFORE deciding to OCR).

Migrated from the legacy `ocr_engine.count_pdf_pages` so the rest of
that legacy module (EasyOCR + regex field extraction) can be deleted.

Public API:
    count_pdf_pages(pdf_bytes) -> int
    render_page_png(path, page, dpi) -> Optional[bytes]
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def count_pdf_pages(pdf_bytes: bytes) -> int:
    """Count pages in a PDF without rendering any image.

    Args:
        pdf_bytes: raw PDF file bytes

    Returns:
        Number of pages (>= 0). Returns 0 on any parse error (invalid PDF,
        empty bytes, corrupted file, etc.) — caller should treat 0 as
        "cannot use this PDF" and reject with an appropriate user-facing
        error.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        logger.error("pdf_utils: PyMuPDF (fitz) not installed: %s", e)
        return 0

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        n = doc.page_count
        doc.close()
        return n
    except Exception as e:
        logger.error("pdf_utils: cannot count PDF pages: %s", e)
        return 0


def render_page_png(path: str, page: int = 1, dpi: int = 144) -> Optional[bytes]:
    """Rasterize one page of a stored PDF to PNG bytes for inline viewing.

    Args:
        path: absolute path to the PDF on disk
        page: 1-based page number; clamped to [1, page_count]
        dpi: render resolution (144 keeps Thai receipt text legible at zoom)

    Returns:
        PNG bytes, or None on any failure (missing/corrupt PDF) — the caller
        turns None into a 404/422 rather than serving a broken image.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        logger.error("pdf_utils: PyMuPDF (fitz) not installed: %s", e)
        return None

    doc = None
    try:
        doc = fitz.open(path)
        if doc.page_count == 0:
            return None
        idx = max(0, min(page - 1, doc.page_count - 1))
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = doc.load_page(idx).get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png")
    except Exception as e:
        logger.error("pdf_utils: cannot render PDF page: %s", e)
        return None
    finally:
        if doc is not None:
            doc.close()
