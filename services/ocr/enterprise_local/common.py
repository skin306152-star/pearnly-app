"""Geometry-based extraction ported from the validated September 3 pilot."""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Sequence

TOL = Decimal("0.01")

from .geometry import (
    RowBox,
    TokenBox,
)


def dec(value: object) -> Decimal | None:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    text = text.replace(",", "").replace("฿", "").replace("$", "")
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        value_decimal = Decimal(match.group(0))
    except InvalidOperation:
        return None
    return -abs(value_decimal) if negative else value_decimal


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def money_equal(left: object, right: object) -> bool:
    a, b = dec(left), dec(right)
    return a is not None and b is not None and abs(a - b) <= TOL


def norm_id(value: object) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKC", str(value or "")).upper() if char.isalnum()
    )


def norm_tax(value: object) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def norm_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(char for char in text if char.isalnum())


DATE_RE = re.compile(r"(?<!\d)(\d{1,4})[-/.](\d{1,2})[-/.](\d{1,4})(?!\d)")


FLEX_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[-/. ]\s*(\d{1,2})\s*[-/. ]\s*(\d{2,4})(?!\d)")


TIME_RE = re.compile(r"(?<!\d)([0-2]?\d[:.]\d{2})(?!\d)")


MONEY_RE = re.compile(r"^[฿$B]?[-+]?\(?\d[\d,]*\.\d{1,2}\)?$", re.IGNORECASE)


def norm_date(value: object) -> str:
    match = DATE_RE.search(unicodedata.normalize("NFKC", str(value or "")))
    if not match:
        return ""
    a, b, c = (int(part) for part in match.groups())
    if a > 1900:
        year, month, day = a, b, c
    else:
        day, month, year = a, b, c
        if year < 100:
            year += 2000
    if year >= 2400:
        year -= 543
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return ""
    return f"{year:04d}-{month:02d}-{day:02d}"


def _money_tokens(row: RowBox) -> list[tuple[TokenBox, Decimal]]:
    output = []
    for token in row.tokens:
        compact = token.text.replace(" ", "")
        if MONEY_RE.fullmatch(compact):
            value = dec(compact)
            if value is not None:
                output.append((token, value))
    return sorted(output, key=lambda item: item[0].xc)


def _loose_money(value: object) -> Decimal | None:
    """Read OCR punctuation variants while still requiring printed cents."""

    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    if not text or ":" in text or TIME_RE.fullmatch(text):
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("() ").replace("฿", "").replace("$", "").replace("B", "")
    spaced_cents = re.fullmatch(r"([-+]?\d[\d.,]*(?:\s+\d+)*)\s+(\d{2})", text)
    if spaced_cents:
        integer = re.sub(r"\D", "", spaced_cents.group(1)) or "0"
        sign = "-" if spaced_cents.group(1).startswith("-") or negative else ""
        try:
            return Decimal(f"{sign}{integer}.{spaced_cents.group(2)}")
        except InvalidOperation:
            return None
    compact = text.replace(" ", "")
    if re.search(r"[OGS]", compact, re.IGNORECASE):
        mapped = compact.upper().translate(str.maketrans({"O": "0", "G": "6", "S": "5"}))
        if re.fullmatch(r"[-+]?\d[\d.,]*", mapped):
            compact = mapped
    if not re.fullmatch(r"[-+]?\d[\d.,]*", compact):
        return None
    separator = max(compact.rfind("."), compact.rfind(","))
    if separator < 0 or len(compact) - separator - 1 != 2:
        return None
    sign = "-" if compact.startswith("-") or negative else ""
    unsigned = compact.lstrip("+-")
    separator = max(unsigned.rfind("."), unsigned.rfind(","))
    integer = re.sub(r"\D", "", unsigned[:separator]) or "0"
    cents = re.sub(r"\D", "", unsigned[separator + 1 :])
    try:
        return Decimal(f"{sign}{integer}.{cents}")
    except InvalidOperation:
        return None


def _joined_token(left: TokenBox, right: TokenBox, text: str) -> TokenBox:
    confidences = [value for value in (left.confidence, right.confidence) if value is not None]
    starts = [value for value in (left.start, right.start) if value is not None]
    ends = [value for value in (left.end, right.end) if value is not None]
    return TokenBox(
        left.page,
        text,
        min(left.x0, right.x0),
        min(left.y0, right.y0),
        max(left.x1, right.x1),
        max(left.y1, right.y1),
        min(confidences) if confidences else None,
        min(starts) if starts else None,
        max(ends) if ends else None,
    )


def _loose_money_candidates(lines: Sequence[RowBox]) -> list[tuple[TokenBox, Decimal]]:
    output: list[tuple[TokenBox, Decimal]] = []
    for line in lines:
        tokens = sorted(line.tokens, key=lambda token: token.x0)
        for index, token in enumerate(tokens):
            value = _loose_money(token.text)
            if value is not None:
                output.append((token, value))
            combined = token
            combined_text = token.text
            for following in tokens[index + 1 : index + 3]:
                gap = following.x0 - combined.x1
                if gap > 0.004 or abs(following.yc - combined.yc) > 0.006:
                    break
                if not re.fullmatch(r"[\d., ]+", following.text):
                    break
                combined_text = f"{combined_text} {following.text}"
                combined = _joined_token(combined, following, combined_text)
                value = _loose_money(combined_text)
                if value is not None:
                    output.append((combined, value))
    unique: dict[tuple[Any, ...], tuple[TokenBox, Decimal]] = {}
    for token, value in output:
        key = (round(token.x0, 5), round(token.y0, 5), round(token.x1, 5), str(value))
        unique[key] = (token, value)
    return sorted(unique.values(), key=lambda pair: pair[0].xc)


def _strict_integer(token: TokenBox) -> str:
    text = unicodedata.normalize("NFKC", token.text).strip()
    return text if re.fullmatch(r"\d{1,6}", text) else ""


def _line_direction(text: str) -> str:
    compact = norm_text(text)
    deposit = ("รับ", "ฝาก", "เงินเข้า", "deposit", "creditinterest", "interestcredit")
    withdrawal = ("ถอน", "โอนเงิน", "ชำระ", "หัก", "ค่าธรรมเนียม", "withdraw", "payment", "debit")
    if any(norm_text(keyword) in compact for keyword in deposit):
        return "deposit"
    if any(norm_text(keyword) in compact for keyword in withdrawal):
        return "withdrawal"
    return ""


def _without_structural_tokens(row: RowBox, excluded: Iterable[TokenBox]) -> str:
    excluded_ids = {id(token) for token in excluded}
    parts = []
    for token in row.tokens:
        if id(token) in excluded_ids:
            continue
        text = token.text.strip()
        if not text or DATE_RE.fullmatch(text) or TIME_RE.fullmatch(text):
            continue
        parts.append(text)
    return " ".join(parts).strip(" |-_")


def _page_counts(entries: Sequence[dict[str, Any]], pages: int) -> list[int]:
    counts = [0] * pages
    for entry in entries:
        try:
            page = int(entry.get("page") or 1)
        except (TypeError, ValueError):
            page = 1
        if 1 <= page <= pages:
            counts[page - 1] += 1
    return counts
