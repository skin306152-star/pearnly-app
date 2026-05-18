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
"""

from __future__ import annotations

import logging

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
