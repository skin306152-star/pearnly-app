"""Categories E & F — allowlists, ownership, and business bounds (client rules).

These read the tenant's loaded client_rules. The supplier allowlist is gated by
an explicit feature toggle so an empty allowlist can still be "enabled" (the
absence of data must not silently mean "off"). Amount limits enforce per-invoice
caps here; a monthly cap needs a running total and is left to a later phase.
"""

from __future__ import annotations

from services.knowledge.rules.context import (
    AMOUNT_TOLERANCE,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    Finding,
    Invoice,
    RuleContext,
)
from services.knowledge.schema import (
    RULE_SUPPLIER_ALLOWLIST,
    SUBJECT_CATEGORY,
    SUBJECT_SUPPLIER,
)


def r_sup_01_allowlist(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not ctx.rules.toggle(RULE_SUPPLIER_ALLOWLIST) or not invoice.seller_tax_id:
        return []
    if invoice.seller_tax_id in ctx.rules.allowlisted_suppliers:
        return []
    return [
        Finding(
            rule_id="R-SUP-01",
            severity=SEVERITY_MEDIUM,
            message_key="risk.supplier_not_allowlisted",
            evidence={
                "seller_tax_id": invoice.seller_tax_id,
                "seller_name": invoice.seller_name,
            },
        )
    ]


def r_sup_02_force_review(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.seller_tax_id:
        return []
    rule = ctx.rules.force_review_suppliers.get(invoice.seller_tax_id)
    if rule is None:
        return []
    return [
        Finding(
            rule_id="R-SUP-02",
            severity=rule.severity or SEVERITY_HIGH,
            message_key="risk.supplier_force_review",
            evidence={
                "seller_tax_id": invoice.seller_tax_id,
                "reason": rule.rule_body.get("reason"),
            },
            client_rule_id=rule.id,
        )
    ]


def r_ws_01_ownership(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not ctx.workspace_client_tax_id or not invoice.buyer_tax_id:
        return []
    if invoice.buyer_tax_id == ctx.workspace_client_tax_id:
        return []
    return [
        Finding(
            rule_id="R-WS-01",
            severity=SEVERITY_HIGH,
            message_key="risk.wrong_workspace",
            evidence={
                "buyer_tax_id": invoice.buyer_tax_id,
                "workspace_client_tax_id": ctx.workspace_client_tax_id,
            },
        )
    ]


def r_limit_01_amount(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    candidates = []
    if invoice.seller_tax_id:
        candidates.append((SUBJECT_SUPPLIER, invoice.seller_tax_id))
    if invoice.category:
        candidates.append((SUBJECT_CATEGORY, invoice.category))
    findings: list[Finding] = []
    for subject in candidates:
        rule = ctx.rules.amount_limits.get(subject)
        if rule is None or rule.rule_body.get("period", "per_invoice") != "per_invoice":
            continue
        basis = rule.rule_body.get("basis", "total")
        value = invoice.total_amount if basis == "total" else invoice.net_amount
        limit = rule.rule_body.get("limit")
        if value is None or limit is None or value <= limit + AMOUNT_TOLERANCE:
            continue
        findings.append(
            Finding(
                rule_id="R-LIMIT-01",
                severity=rule.severity or SEVERITY_HIGH,
                message_key="risk.amount_over_limit",
                evidence={"value": value, "limit": limit, "basis": basis},
                client_rule_id=rule.id,
            )
        )
    return findings


def r_cat_01_no_auto_push(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.category:
        return []
    rule = ctx.rules.no_push_categories.get(invoice.category)
    if rule is None:
        return []
    return [
        Finding(
            rule_id="R-CAT-01",
            severity=rule.severity or SEVERITY_MEDIUM,
            message_key="risk.category_no_auto_push",
            evidence={"category": invoice.category},
            client_rule_id=rule.id,
        )
    ]


RULES = [
    r_sup_01_allowlist,
    r_sup_02_force_review,
    r_ws_01_ownership,
    r_limit_01_amount,
    r_cat_01_no_auto_push,
]
