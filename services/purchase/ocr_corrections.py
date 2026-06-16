# -*- coding: utf-8 -*-
"""Deterministic OCR field cleanup before purchase drafts are built.

These rules only fix values that can be corrected from arithmetic or stable
Thai document conventions. Anything uncertain is left for review.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

_CENT = Decimal("0.01")
_DATE_RE = re.compile(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\s*$")
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TAX_RE = re.compile(r"\d{13}")
_TH_BRANCH_RE = re.compile(r"(?:สาขา|branch|br\.?)\D{0,12}(\d{3,5})", re.I)


def _dec(v: Any) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip()) if v not in (None, "") else Decimal("0")
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _money(v: Decimal) -> str:
    return format(v.quantize(_CENT), "f")


def _clean_tax_id(value: Any) -> str:
    text = str(value or "")
    matches = _TAX_RE.findall(text.replace(" ", ""))
    return matches[0] if len(matches) == 1 else ""


def _year_from_two_digits(yy: int) -> int:
    today_year = date.today().year
    candidates = [y for y in (2000 + yy, 2500 + yy - 543) if 2000 <= y <= today_year + 1]
    return min(candidates, key=lambda y: abs(today_year - y)) if candidates else 2000 + yy


def _normalize_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if _ISO_RE.match(raw):
        return raw
    m = _DATE_RE.match(raw)
    if not m:
        return raw
    day, month, year = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if year < 100:
        year = _year_from_two_digits(year)
    elif year >= 2400:
        year -= 543
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return raw


def _is_branch_number_as_invoice(fields: dict, invoice_no: str) -> bool:
    digits = re.sub(r"\D", "", invoice_no or "")
    if not digits or digits != str(invoice_no or "").strip() or len(digits) > 5:
        return False
    haystack = " ".join(str(fields.get(k) or "") for k in ("seller_name", "seller_addr", "notes"))
    for match in _TH_BRANCH_RE.finditer(haystack):
        if match.group(1).lstrip("0") == digits.lstrip("0"):
            return True
    return False


def _is_vat_seven_percent(subtotal: Decimal, vat: Decimal) -> bool:
    if subtotal <= 0 or vat <= 0:
        return False
    expected = (subtotal * Decimal("0.07")).quantize(_CENT)
    return abs(expected - vat) <= Decimal("0.05")


def normalize_fields(fields: dict | None) -> dict:
    """Return a cleaned copy of OCR fields.

    Rules are deliberately conservative:
    - tax IDs keep only one visible 13-digit Thai ID;
    - branch numbers are not accepted as invoice numbers;
    - dates are normalized for common Thai DD/MM/YY and Buddhist-year formats;
    - missing subtotal/VAT/total is inferred only when arithmetic is exact.
    """
    src = dict(fields or {})
    out = dict(src)
    corrections: list[str] = list(src.get("_corrections") or [])

    for key in ("seller_tax", "buyer_tax"):
        cleaned = _clean_tax_id(src.get(key))
        if cleaned and cleaned != src.get(key):
            out[key] = cleaned
            corrections.append(f"{key}_normalized")

    inv_no = str(src.get("invoice_number") or "").strip()
    if inv_no and _is_branch_number_as_invoice(src, inv_no):
        out["invoice_number"] = ""
        corrections.append("invoice_number_branch_removed")
    elif inv_no:
        out["invoice_number"] = inv_no

    norm_date = _normalize_date(src.get("date"))
    if norm_date != (src.get("date") or ""):
        out["date"] = norm_date
        corrections.append("date_normalized")

    subtotal = _dec(src.get("subtotal"))
    vat = _dec(src.get("vat"))
    total = _dec(src.get("total_amount"))

    if subtotal <= 0 and total > 0 and vat > 0 and total >= vat:
        subtotal = total - vat
        out["subtotal"] = _money(subtotal)
        corrections.append("subtotal_inferred_from_total_vat")

    if vat <= 0 and subtotal > 0 and total > subtotal:
        diff = total - subtotal
        if _is_vat_seven_percent(subtotal, diff):
            vat = diff
            out["vat"] = _money(vat)
            corrections.append("vat_inferred_from_total_subtotal")

    if total <= 0 and subtotal > 0 and vat > 0:
        total = subtotal + vat
        out["total_amount"] = _money(total)
        corrections.append("total_inferred_from_subtotal_vat")

    if corrections:
        out["_corrections"] = sorted(set(corrections))
    return out
