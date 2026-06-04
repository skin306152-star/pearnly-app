"""Category A — legality / format rules (mostly global).

The Thai tax-id check digit (MOD-11) is implemented here and must be validated
against known-good/known-bad ids in the tests, not trusted from the spec alone.
Dates are normalised from the Buddhist era (พ.ศ.) to the Gregorian era before
any comparison, since OCR returns whatever the document printed.
"""

from __future__ import annotations

import re
from datetime import date

from services.knowledge.rules.context import (
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    Finding,
    Invoice,
    RuleContext,
)

_THAI_HQ = "สำนักงานใหญ่"
_BUDDHIST_OFFSET = 543
_BUDDHIST_THRESHOLD = 2400  # a year this large is certainly Buddhist-era


def valid_thai_tax_id(value: str) -> bool:
    """13 digits whose last digit is the MOD-11 check of the first 12."""
    if not value or not re.fullmatch(r"\d{13}", value):
        return False
    digits = [int(c) for c in value]
    weighted = sum(digits[i] * (13 - i) for i in range(12))
    check = (11 - (weighted % 11)) % 10
    return digits[12] == check


def _is_placeholder(value: str) -> bool:
    return bool(value) and len(set(value)) == 1  # all-same-digit, e.g. 0000000000000


def parse_invoice_date(raw: str) -> date | None:
    """Parse common invoice date formats and normalise a Buddhist year."""
    if not raw:
        return None
    match = re.search(r"(\d{1,4})\D(\d{1,2})\D(\d{1,4})", raw.strip())
    if not match:
        return None
    a, b, c = (int(x) for x in match.groups())
    year, month, day = (a, b, c) if a > 31 else (c, b, a)
    if year >= _BUDDHIST_THRESHOLD:
        year -= _BUDDHIST_OFFSET
    try:
        return date(year, month, day)
    except ValueError:
        return None


def r_taxid_01_seller(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.seller_tax_id:
        return []
    if valid_thai_tax_id(invoice.seller_tax_id):
        return []
    return [
        Finding(
            rule_id="R-TAXID-01",
            severity=SEVERITY_HIGH,
            message_key="risk.seller_tax_id_invalid",
            evidence={"seller_tax_id": invoice.seller_tax_id},
        )
    ]


def r_taxid_02_buyer(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.buyer_tax_id:
        return []
    if valid_thai_tax_id(invoice.buyer_tax_id):
        return []
    return [
        Finding(
            rule_id="R-TAXID-02",
            severity=SEVERITY_HIGH,
            message_key="risk.buyer_tax_id_invalid",
            evidence={"buyer_tax_id": invoice.buyer_tax_id},
        )
    ]


def r_taxid_03_placeholder(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    findings: list[Finding] = []
    for field_name, value in (
        ("seller_tax_id", invoice.seller_tax_id),
        ("buyer_tax_id", invoice.buyer_tax_id),
    ):
        if value and _is_placeholder(value):
            findings.append(
                Finding(
                    rule_id="R-TAXID-03",
                    severity=SEVERITY_MEDIUM,
                    message_key="risk.tax_id_placeholder",
                    evidence={"field": field_name, "value": value},
                )
            )
    return findings


def r_date_01_legal(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.invoice_date:
        return []  # absence is R-FIELD-04's concern
    parsed = parse_invoice_date(invoice.invoice_date)
    if parsed is None:
        return [
            Finding(
                rule_id="R-DATE-01",
                severity=SEVERITY_HIGH,
                message_key="risk.invoice_date_unparseable",
                evidence={"invoice_date": invoice.invoice_date, "normalized": None},
            )
        ]
    today = ctx.today or date.today()
    if parsed > today:
        return [
            Finding(
                rule_id="R-DATE-01",
                severity=SEVERITY_MEDIUM,
                message_key="risk.invoice_date_future",
                evidence={
                    "invoice_date": invoice.invoice_date,
                    "normalized": parsed.isoformat(),
                },
            )
        ]
    return []


def _accounting_window(mode: str, today: date, body: dict) -> tuple[date | None, date | None]:
    if mode == "fixed":
        start = body.get("period_start")
        end = body.get("period_end")
        return (
            date.fromisoformat(start) if start else None,
            date.fromisoformat(end) if end else None,
        )
    month = today.month if mode == "current_month" else today.month - 1
    year = today.year
    if month == 0:
        month, year = 12, year - 1
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    return start, end


def r_date_02_accounting_period(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    rule = ctx.rules.accounting_period
    if rule is None or not invoice.invoice_date:
        return []
    parsed = parse_invoice_date(invoice.invoice_date)
    if parsed is None:
        return []  # R-DATE-01 already reports an unparseable date
    today = ctx.today or date.today()
    start, end = _accounting_window(rule.rule_body.get("mode", "fixed"), today, rule.rule_body)
    if (start and parsed < start) or (end and parsed >= end):
        return [
            Finding(
                rule_id="R-DATE-02",
                severity=rule.severity or SEVERITY_MEDIUM,
                message_key="risk.invoice_date_out_of_period",
                evidence={
                    "invoice_date": parsed.isoformat(),
                    "period_start": start.isoformat() if start else None,
                    "period_end": end.isoformat() if end else None,
                },
                client_rule_id=rule.id,
            )
        ]
    return []


def r_branch_01_format(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    branch = invoice.seller_branch
    if not branch:
        return []
    if re.fullmatch(r"\d{5}", branch.strip()) or _THAI_HQ in branch:
        return []
    return [
        Finding(
            rule_id="R-BRANCH-01",
            severity=SEVERITY_LOW,
            message_key="risk.branch_format",
            evidence={"seller_branch": branch},
        )
    ]


RULES = [
    r_taxid_01_seller,
    r_taxid_02_buyer,
    r_taxid_03_placeholder,
    r_date_01_legal,
    r_date_02_accounting_period,
    r_branch_01_format,
]
