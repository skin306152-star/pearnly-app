# -*- coding: utf-8 -*-
"""
services/ocr/text_path.py

Layer 0: pypdf-based text extraction for electronic PDFs (e-Tax Invoice, etc).

Purpose: if a PDF has a real text layer (electronic invoice with embedded
fonts, e-Tax Invoice, etc), pypdf can extract text directly without going
through OCR. This skips Layer 1 Vision API entirely (~70% of pipeline
cost per architecture.md), leaving only Layer 2 Flash-Lite for AI field
mapping. Per architecture.md §四 ④:

    "如果客户上传的是泰国电子发票(e-Tax Invoice,有文本层的 PDF),
    直接 PDF 文本提取 + Flash-Lite 解析,完全跳过 Vision API,
    这部分文档成本降到 $0.0005/页"

Difference from the legacy [pdf_text_extractor.py](../../pdf_text_extractor.py):
    - Legacy module does BOTH text extraction AND regex-based field
      extraction (template-sensitive, brittle).
    - This module only does the TEXT extraction part; field extraction
      is delegated to Layer 2 Flash-Lite (AI, generalizes well).
    - Output is a Layer1Result-shaped object so pipeline.py can use it
      as a drop-in replacement for the Vision API call.

Public API:
    try_extract(pdf_bytes, max_pages=50, min_text_per_page=200) -> Optional[Layer1Result]
        Returns Layer1Result if pypdf gives >= min_text_per_page chars
        per page on average. Returns None for scanned PDFs / corrupted
        PDFs / no text layer — caller falls back to Vision.

Key design choices:
    - Threshold 200 chars/page matches existing pdf_text_extractor convention
    - No bbox / per-word confidence (pypdf doesn't provide these)
    - avg_confidence set to 1.0 placeholder (pypdf is direct text, trustable)
    - Empty blocks list — pipeline word-level confidence trigger will safely
      return None on text_path pages (other triggers still fire normally)
"""

from __future__ import annotations

import io
import logging
import time
from typing import List, Optional

from .schemas import Layer1Result, Page

logger = logging.getLogger(__name__)


DEFAULT_MIN_TEXT_PER_PAGE = 200
"""Minimum average characters per page to consider PDF as electronic.
Matches the threshold used by the legacy [pdf_text_extractor.py:36](../../pdf_text_extractor.py)
so behavior is consistent."""


def try_extract(
    pdf_bytes: bytes,
    max_pages: int = 50,
    min_text_per_page: int = DEFAULT_MIN_TEXT_PER_PAGE,
) -> Optional[Layer1Result]:
    """Try to extract text from a PDF's embedded text layer (skip OCR).

    Args:
        pdf_bytes: raw PDF file bytes
        max_pages: cap on pages to process; pages beyond are silently skipped
        min_text_per_page: minimum avg chars/page required to consider this
            PDF "electronic" (default 200). If actual average is below
            threshold, returns None and caller should run OCR.

    Returns:
        Layer1Result with one Page per processed PDF page (containing
        pypdf-extracted text, no bbox/conf), OR None if:
            - pypdf isn't installed
            - PDF can't be parsed
            - PDF has 0 pages
            - average chars/page is below threshold (scanned-only PDF)
            - any unexpected exception

    Notes:
        - Pages with extraction errors get empty text but still count
          toward the average (so a single bad page in a 10-page electronic
          PDF still passes threshold).
        - Returned Page objects have width=0, height=0 (we don't render
          for text_path); pipeline must render images itself if Layer 3
          visual fallback needs them.
    """
    if not pdf_bytes:
        return None

    try:
        import pypdf  # noqa: F401
    except ImportError:
        logger.info("text_path: pypdf not installed — skipping fast path")
        return None

    t0 = time.time()
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        logger.info(
            "text_path: pypdf cannot parse PDF — fallback to Vision · %s: %s",
            type(e).__name__, str(e)[:100],
        )
        return None

    n_pages_total = len(reader.pages)
    if n_pages_total == 0:
        return None

    process_count = min(n_pages_total, max_pages)
    page_texts: List[str] = []
    total_chars = 0
    for i in range(process_count):
        try:
            t = reader.pages[i].extract_text() or ""
        except Exception:
            t = ""
        page_texts.append(t)
        total_chars += len(t)

    avg = total_chars / max(len(page_texts), 1)
    if avg < min_text_per_page:
        logger.info(
            "text_path: avg %d chars/page < %d threshold — fallback to Vision",
            int(avg), min_text_per_page,
        )
        return None

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info(
        "text_path: HIT · %d page(s) · avg %d chars/page · %d ms",
        len(page_texts), int(avg), elapsed_ms,
    )

    pages = [
        Page(
            page_number=i + 1,
            width=0,  # not rendered by text_path
            height=0,
            full_text=text,
            avg_confidence=1.0,  # pypdf is direct extraction (no OCR uncertainty)
            blocks=[],  # no word-level structure from pypdf
        )
        for i, text in enumerate(page_texts)
    ]
    return Layer1Result(
        pages=pages,
        page_count=len(pages),
        elapsed_ms=elapsed_ms,
        engine="text_path",
        dpi=0,
    )
