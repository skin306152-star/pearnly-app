"""Runtime reconstruction and arithmetic gates; no benchmark answers involved."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .bank_chain import _bank_chain
from .bank_parser import _bank_groups, parse_bank
from .common import dec
from .geometry import rows_from_payloads
from .gl_parser import _gl_chain, parse_gl


@dataclass
class Reconstruction:
    document: dict
    audit: list[dict]
    provenance: list[dict]
    issues: list[str]
    pages: int

    @property
    def arithmetic_passed(self) -> bool:
        # Arithmetic consistency does NOT establish transcription correctness.
        return not self.issues

    @property
    def requires_review(self) -> bool:
        return bool(self.issues or self.audit)


def check_document(document: dict, category: str, pages: int) -> list[str]:
    entries = document.get("entries") or []
    issues = []
    if not entries:
        return ["no_transaction_rows"]
    seen_pages = [int(row.get("page") or 0) for row in entries]
    if sorted(set(seen_pages)) != list(range(1, pages + 1)):
        issues.append("transaction_page_coverage_unverified")
    if seen_pages != sorted(seen_pages):
        issues.append("page_order_invalid")
    chain = (_bank_chain if category == "bank" else _gl_chain)(document)
    if chain["checked"] != len(entries) or chain["violation_count"]:
        issues.append("balance_chain_incomplete_or_broken")
    if chain["cross_page_checked"] != pages - 1:
        issues.append("cross_page_chain_incomplete")
    closing = dec(document.get("closing_balance"))
    if closing is None or closing != dec(entries[-1].get("balance")):
        issues.append("closing_balance_missing_or_mismatched")
    plus, minus = ("deposit", "withdrawal") if category == "bank" else ("debit", "credit")
    for row in entries:
        left, right = dec(row.get(plus)), dec(row.get(minus))
        if not row.get("transaction_date"):
            issues.append("transaction_date_missing")
        if left is None and right is None:
            issues.append("transaction_amount_missing")
        elif any(v is not None and v < 0 for v in (left, right)):
            issues.append("negative_unsigned_amount")
        elif left and right:
            issues.append("ambiguous_transaction_direction")
    if category == "gl":
        for field in ("debit", "credit"):
            printed = dec(document.get(f"total_{field}"))
            summed = sum((dec(row.get(field)) or Decimal(0) for row in entries), Decimal(0))
            if printed is not None and abs(printed - summed) > Decimal("0.01"):
                issues.append(f"printed_total_{field}_mismatch")
    return list(dict.fromkeys(issues))


def reconstruct(payloads: list[dict], category: str, *, expected_pages: int) -> Reconstruction:
    if category not in ("bank", "gl"):
        raise ValueError("Local reconstruction supports bank and gl only")
    rows, lines, tables, meta = rows_from_payloads(payloads)
    if meta["pages"] != expected_pages:
        raise ValueError("Enterprise OCR response page count differs from input")
    args = (lines, expected_pages, tables) if category == "bank" else (rows, expected_pages)
    document, audit, provenance = (parse_bank if category == "bank" else parse_gl)(*args)
    issues = check_document(document, category, expected_pages)
    if category == "bank":
        # Also count geometric date anchors; a perfectly balanced subset must
        # not pass just because omitted rows are invisible to arithmetic.
        anchors = sum(not group["carry"] for group in _bank_groups(lines))
        if anchors != len(document.get("entries") or []):
            issues.append("date_anchor_row_count_mismatch")
    return Reconstruction(document, audit, provenance, issues, expected_pages)
