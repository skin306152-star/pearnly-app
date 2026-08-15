# -*- coding: utf-8 -*-
"""DMS 订车单自动编号与已占用号扫描。"""

from __future__ import annotations

import logging
import re
from typing import Callable, Dict

logger = logging.getLogger(__name__)

BOOKING_DOCNO_MAX_TRIES = 25
BOOKING_LIST_PAGE_SIZE = 100
BOOKING_LIST_MAX_PAGES = 100


def is_duplicate_docno_error(body: str) -> bool:
    """DMS 单号重复报错(err::"เลขที่ใบจอง" ซ้ำ)。"""
    return body.startswith("err::") and "ซ้ำ" in body


def bump_docno(docno: str) -> str:
    """末尾连续数字段加一并保持位宽。"""
    index = len(docno)
    while index > 0 and docno[index - 1].isdigit():
        index -= 1
    head, tail = docno[:index], docno[index:]
    if not tail:
        return docno + "1"
    return head + str(int(tail) + 1).zfill(len(tail))


def listing_docnos(body: str, prefix: str, digits: int) -> set[str]:
    """订车列表 HTML 中与当前自动编号系列完全同形的单号。"""
    if not prefix or digits <= 0:
        return set()
    pattern = rf"(?<![A-Z0-9]){re.escape(prefix)}\d{{{digits}}}(?!\d)"
    return set(re.findall(pattern, body or ""))


def next_unoccupied_docno(
    candidate: str,
    digits: int,
    post_text: Callable[[str, Dict[str, str]], str],
) -> str:
    """从订车列表现有最大流水号之后开始，绕过失步的 DMS 自动编号器。"""
    if digits <= 0 or len(candidate) <= digits:
        return candidate
    prefix, suffix = candidate[:-digits], candidate[-digits:]
    if not suffix.isdigit():
        return candidate

    highest = int(suffix) - 1
    seen: set[str] = set()
    try:
        for page in range(1, BOOKING_LIST_MAX_PAGES + 1):
            body = post_text(
                "drfcbc/component/showdata.php",
                {
                    "sdtamt": str(BOOKING_LIST_PAGE_SIZE),
                    "sdtpage": str(page),
                    "sd": prefix,
                    "ftd": "1",
                    "selcolsort": "1",
                    "selcolsorttype": "2",
                },
            )
            page_docnos = listing_docnos(body, prefix, digits)
            new_docnos = page_docnos - seen
            if not new_docnos:
                break
            seen.update(new_docnos)
            highest = max(highest, *(int(value[-digits:]) for value in new_docnos))
            if len(page_docnos) < BOOKING_LIST_PAGE_SIZE:
                break
    except Exception as exc:
        logger.warning("[dms] booking docno listing failed; use autonum candidate: %s", exc)
        return candidate

    next_number = max(int(suffix), highest + 1)
    return f"{prefix}{str(next_number).zfill(digits)}"


__all__ = [
    "BOOKING_DOCNO_MAX_TRIES",
    "bump_docno",
    "is_duplicate_docno_error",
    "listing_docnos",
    "next_unoccupied_docno",
]
