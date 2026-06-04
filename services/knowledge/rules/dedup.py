"""Category C — duplicate detection (global, needs prior-invoice lookup).

The lookups are injected on the RuleContext rather than queried here, so these
stay pure functions: tests pass fakes, P5 passes a real ocr_history-backed
lookup. Both lookups are already tenant-scoped by the caller.
"""

from __future__ import annotations

from services.knowledge.rules.context import (
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    Finding,
    Invoice,
    RuleContext,
)


def r_dup_01_exact(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.seller_tax_id or not invoice.invoice_no:
        return []
    existing = ctx.find_exact_duplicate(invoice.seller_tax_id, invoice.invoice_no)
    if not existing:
        return []
    return [
        Finding(
            rule_id="R-DUP-01",
            severity=SEVERITY_HIGH,
            message_key="risk.duplicate_exact",
            evidence={
                "existing_history_id": existing,
                "seller_tax_id": invoice.seller_tax_id,
                "invoice_no": invoice.invoice_no,
            },
        )
    ]


def r_dup_02_suspected(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.seller_tax_id:
        return []
    # An exact duplicate already covers this pair; only flag the looser match
    # when there is no exact one.
    if invoice.invoice_no and ctx.find_exact_duplicate(invoice.seller_tax_id, invoice.invoice_no):
        return []
    candidates = ctx.find_suspected_duplicates(
        invoice.seller_tax_id, invoice.total_amount, invoice.invoice_date
    )
    if not candidates:
        return []
    return [
        Finding(
            rule_id="R-DUP-02",
            severity=SEVERITY_MEDIUM,
            message_key="risk.duplicate_suspected",
            evidence={"candidate_history_ids": list(candidates)},
        )
    ]


RULES = [r_dup_01_exact, r_dup_02_suspected]
