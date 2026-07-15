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
from typing import Optional, Tuple

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


def render_page_png(path: str, page: int = 1, dpi: int = 144) -> Optional[Tuple[bytes, int]]:
    """Rasterize one page of a stored PDF to PNG bytes for inline viewing.

    Args:
        path: absolute path to the PDF on disk
        page: 1-based page number; clamped to [1, page_count]
        dpi: render resolution (144 keeps Thai receipt text legible at zoom)

    Returns:
        (PNG bytes, total page count), or None on any failure (missing/corrupt
        PDF) — the caller turns None into a 404/422 rather than serving a broken
        image. total page count lets the front-end page through multi-page PDFs
        (一份 PDF 装多张发票时翻页看每一页).

    留底加密后不再用这个路径入口(密文喂 fitz 会炸);history 走 read_bytes 解密后调
    render_page_png_bytes。此入口留给明文/临时文件与既有单测。
    """
    try:
        with open(path, "rb") as fh:
            return render_page_png_bytes(fh.read(), page=page, dpi=dpi)
    except OSError as e:
        logger.error("pdf_utils: cannot open PDF: %s", e)
        return None


def render_page_png_bytes(
    pdf_bytes: bytes, page: int = 1, dpi: int = 144
) -> Optional[Tuple[bytes, int]]:
    """同 render_page_png,但吃已在内存的 PDF 字节——留底走加密后,调用方先解密再渲染,不落临时明文盘。"""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        logger.error("pdf_utils: PyMuPDF (fitz) not installed: %s", e)
        return None

    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count == 0:
            return None
        total = doc.page_count
        idx = max(0, min(page - 1, total - 1))
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = doc.load_page(idx).get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png"), total
    except Exception as e:
        logger.error("pdf_utils: cannot render PDF page: %s", e)
        return None
    finally:
        if doc is not None:
            doc.close()
