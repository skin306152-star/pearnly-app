"""Category D — completeness / mandatory fields (Thai Revenue Code 86/4).

Strict only for a full tax invoice; abbreviated tickets and receipts are not
held to the same bar. The Thai tax-invoice marker is ใบกำกับภาษี.
"""

from __future__ import annotations

from services.knowledge.rules.context import (
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    Finding,
    Invoice,
    RuleContext,
)

DOC_FULL_TAX_INVOICE = "full_tax_invoice"
_TAX_INVOICE_MARKER = "ใบกำกับภาษี"


def _is_full_tax_invoice(invoice: Invoice) -> bool:
    return invoice.doc_type == DOC_FULL_TAX_INVOICE


def r_field_01_marker(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not _is_full_tax_invoice(invoice):
        return []
    if _TAX_INVOICE_MARKER in (invoice.raw_text or ""):
        return []
    return [
        Finding(
            rule_id="R-FIELD-01",
            severity=SEVERITY_MEDIUM,
            message_key="risk.missing_tax_invoice_marker",
            evidence={"doc_type": invoice.doc_type},
        )
    ]


def r_field_02_seller(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    missing = [
        name
        for name, value in (
            ("seller_name", invoice.seller_name),
            ("seller_address", invoice.seller_address),
            ("seller_tax_id", invoice.seller_tax_id),
        )
        if not value
    ]
    if not missing:
        return []
    return [
        Finding(
            rule_id="R-FIELD-02",
            severity=SEVERITY_MEDIUM,
            message_key="risk.seller_incomplete",
            evidence={"missing": missing},
        )
    ]


def r_field_03_buyer(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not _is_full_tax_invoice(invoice):
        return []
    missing = [
        name
        for name, value in (
            ("buyer_name", invoice.buyer_name),
            ("buyer_tax_id", invoice.buyer_tax_id),
        )
        if not value
    ]
    if not missing:
        return []
    return [
        Finding(
            rule_id="R-FIELD-03",
            severity=SEVERITY_MEDIUM,
            message_key="risk.buyer_incomplete",
            evidence={"missing": missing},
        )
    ]


def r_field_04_invoice_identity(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    missing = [
        name
        for name, value in (
            ("invoice_no", invoice.invoice_no),
            ("invoice_date", invoice.invoice_date),
        )
        if not value
    ]
    if not missing:
        return []
    return [
        Finding(
            rule_id="R-FIELD-04",
            severity=SEVERITY_HIGH,
            message_key="risk.invoice_identity_incomplete",
            evidence={"missing": missing},
        )
    ]


def r_field_05_amounts(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    present = [
        name
        for name, value in (
            ("net_amount", invoice.net_amount),
            ("vat_amount", invoice.vat_amount),
            ("total_amount", invoice.total_amount),
        )
        if value is not None
    ]
    if len(present) >= 2:
        return []
    return [
        Finding(
            rule_id="R-FIELD-05",
            severity=SEVERITY_MEDIUM,
            message_key="risk.amounts_incomplete",
            evidence={"present": present},
        )
    ]


RULES = [
    r_field_01_marker,
    r_field_02_seller,
    r_field_03_buyer,
    r_field_04_invoice_identity,
    r_field_05_amounts,
]
