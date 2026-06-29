# -*- coding: utf-8 -*-
"""
services/ocr/confidence.py

Confidence + provenance helpers used by pipeline.py triggers.

Purpose:
    Layer 1 (Vision API) gives us word-level confidence + bbox. Layer 2
    extracts structured fields from the text. To decide whether layer 3
    should refine, pipeline.py needs to know:
        1. For each critical field, what's the lowest-confidence word
           among the L1 words that contain (or are contained by) the
           extracted field value? This catches cases where Vision was
           uncertain about a character (like `/` misread as `1`).
        2. Did the extracted field value actually appear in the L1 OCR
           text at all? If not, it's likely hallucinated by L2.

These two checks are key to fixing B1 (IV69/NNNNN slash misread that
went undetected with the previous page-avg confidence trigger).

Public API:
    find_field_min_word_conf(layer1_page, field_value) -> Optional[float]
    check_field_in_l1_text(layer1_page, field_value) -> bool

Both functions are pure / read-only on Page; no side effects.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .schemas import Page, Word

# Minimum overlap (in chars, after normalization) required to count a word
# as "matching" a field value. Avoids spurious matches on common short
# substrings like single digits or short tokens.
MIN_OVERLAP_CHARS = 4

# Characters to normalize away when comparing words to field values.
# 空格/逗号:Vision 与 L2 任一侧都可能增删。连字符/斜杠/货币符:税号(0-1055-...)、
# 日期(28-02-2026)、金额(฿1,780.00)在 L1 文本与抽取值之间常以不同分隔呈现 —— 不剥就会
# 把"正确但分隔不同"的值误判成 L2 幻觉,白白升 L3 视觉复读(速度根因 · 见
# tests/unit/test_l1_containment_narrow.py)。真幻觉(数字本身不同)剥了也匹配不上,仍升 L3。
_NORMALIZE_PATTERN = re.compile(r"[\s,\-–—/฿]+")


def _normalize(s: str) -> str:
    """Strip whitespace/commas/分隔符/货币符 for matching. Lowercase for case-insensitivity."""
    return _NORMALIZE_PATTERN.sub("", s).lower()


def _all_words(page: Page) -> List[Word]:
    """Flatten the page's word hierarchy into a single list."""
    out: List[Word] = []
    for block in page.blocks:
        for paragraph in block.paragraphs:
            out.extend(paragraph.words)
    return out


def find_field_min_word_conf(page: Page, field_value: str) -> Optional[float]:
    """Find min confidence among L1 words that overlap with field_value.

    "Overlap" means: after normalizing both sides (strip whitespace +
    commas, lowercase), one is a substring of the other, AND the overlap
    is at least MIN_OVERLAP_CHARS long.

    Args:
        page: layer 1 Page (with words + confidence + bbox)
        field_value: the extracted field text from layer 2 (e.g. an
            invoice number, tax_id, total amount string)

    Returns:
        min confidence among matched words, or None if no L1 word matched
        (which itself is suspicious — see check_field_in_l1_text).
    """
    if not field_value:
        return None
    val_norm = _normalize(field_value)
    if len(val_norm) < MIN_OVERLAP_CHARS:
        return None  # too short to match reliably

    matched_confs: List[float] = []
    for word in _all_words(page):
        word_norm = _normalize(word.text)
        if not word_norm:
            continue
        # Overlap in either direction
        if val_norm in word_norm or word_norm in val_norm:
            overlap = min(len(val_norm), len(word_norm))
            if overlap >= MIN_OVERLAP_CHARS:
                matched_confs.append(word.confidence)

    if not matched_confs:
        return None
    return min(matched_confs)


def check_field_in_l1_text(page: Page, field_value: str) -> bool:
    """Return True if field_value appears (after normalization) in page.full_text.

    This is a cheaper "hallucination check" than find_field_min_word_conf —
    it just checks the full text without iterating words. Use both:
    find_field_min_word_conf for confidence, check_field_in_l1_text for
    presence.

    Args:
        page: layer 1 Page
        field_value: the extracted field text

    Returns:
        True if field_value appears in the OCR text (after normalization).
        False if not found (suggests hallucination by layer 2).
        True for empty values (so the caller doesn't double-flag missing
        fields that are caught by other rules).
    """
    if not field_value:
        return True
    val_norm = _normalize(field_value)
    if len(val_norm) < MIN_OVERLAP_CHARS:
        return True
    full_norm = _normalize(page.full_text or "")
    return val_norm in full_norm
