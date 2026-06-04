"""Category B — arithmetic consistency rules (global).

All money comparisons use AMOUNT_TOLERANCE so float and rounding noise never
trips a finding. A rule whose inputs are missing skips quietly; absence is the
completeness rules' concern, not arithmetic's.
"""

from __future__ import annotations

from typing import Optional

from services.knowledge.rules.context import (
    AMOUNT_TOLERANCE,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    Finding,
    Invoice,
    RuleContext,
)

VAT_RATE = 0.07


def _num(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def r_vat_01_rate(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if invoice.tax_exempt:
        return []  # zero-rated / exempt: VAT 0 is legal
    net = _num(invoice.net_amount)
    vat = _num(invoice.vat_amount)
    if net is None or vat is None:
        return []
    expected = round(net * VAT_RATE, 2)
    if abs(vat - expected) <= AMOUNT_TOLERANCE:
        return []
    return [
        Finding(
            rule_id="R-VAT-01",
            severity=SEVERITY_HIGH,
            message_key="risk.vat_mismatch",
            evidence={"net_amount": net, "vat_amount": vat, "expected_vat": expected},
        )
    ]


def r_vat_02_total(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    net = _num(invoice.net_amount)
    vat = _num(invoice.vat_amount)
    total = _num(invoice.total_amount)
    if net is None or vat is None or total is None:
        return []
    if abs(total - (net + vat)) <= AMOUNT_TOLERANCE:
        return []
    return [
        Finding(
            rule_id="R-VAT-02",
            severity=SEVERITY_HIGH,
            message_key="risk.total_mismatch",
            evidence={"net_amount": net, "vat_amount": vat, "total_amount": total},
        )
    ]


def r_sum_01_lines(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    net = _num(invoice.net_amount)
    if net is None or not invoice.line_items:
        return []
    lines_sum = round(sum(_num(item.get("amount")) or 0.0 for item in invoice.line_items), 2)
    if abs(lines_sum - net) <= AMOUNT_TOLERANCE:
        return []
    return [
        Finding(
            rule_id="R-SUM-01",
            severity=SEVERITY_MEDIUM,
            message_key="risk.line_sum_mismatch",
            evidence={"lines_sum": lines_sum, "net_amount": net},
        )
    ]


def r_line_01_each(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    findings: list[Finding] = []
    for index, item in enumerate(invoice.line_items):
        qty = _num(item.get("qty"))
        unit_price = _num(item.get("unit_price"))
        amount = _num(item.get("amount"))
        if qty is None or unit_price is None or amount is None:
            continue
        if abs(qty * unit_price - amount) <= AMOUNT_TOLERANCE:
            continue
        findings.append(
            Finding(
                rule_id="R-LINE-01",
                severity=SEVERITY_LOW,
                message_key="risk.line_amount_mismatch",
                evidence={
                    "line_index": index,
                    "qty": qty,
                    "unit_price": unit_price,
                    "amount": amount,
                },
            )
        )
    return findings


def _page_sum(pages: list[dict], key: str) -> float:
    return round(sum(_num(p.get(key)) or 0.0 for p in pages), 2)


def r_multipage_01_aggregate(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if not invoice.is_multipage or not invoice.pages:
        return []
    mismatches = {}
    for key in ("net_amount", "vat_amount", "total_amount"):
        doc_value = _num(getattr(invoice, key))
        if doc_value is None:
            continue
        page_total = _page_sum(invoice.pages, key)
        if abs(page_total - doc_value) > AMOUNT_TOLERANCE:
            mismatches[key] = {"page_sum": page_total, "doc_value": doc_value}
    if not mismatches:
        return []
    return [
        Finding(
            rule_id="R-MULTIPAGE-01",
            severity=SEVERITY_MEDIUM,
            message_key="risk.multipage_mismatch",
            evidence={"pages": len(invoice.pages), "mismatches": mismatches},
        )
    ]


def r_wht_01_rate(invoice: Invoice, ctx: RuleContext) -> list[Finding]:
    if invoice.category is None or invoice.declared_wht_rate is None:
        return []
    rule = ctx.rules.wht_rates.get(invoice.category)
    if rule is None:
        return []
    expected = _num(rule.rule_body.get("expected_rate"))
    declared = _num(invoice.declared_wht_rate)
    if expected is None or declared is None or abs(declared - expected) < 1e-9:
        return []
    return [
        Finding(
            rule_id="R-WHT-01",
            severity=rule.severity or SEVERITY_MEDIUM,
            message_key="risk.wht_rate_mismatch",
            evidence={
                "category": invoice.category,
                "declared_rate": declared,
                "expected_rate": expected,
            },
            client_rule_id=rule.id,
        )
    ]


RULES = [
    r_vat_01_rate,
    r_vat_02_total,
    r_sum_01_lines,
    r_line_01_each,
    r_multipage_01_aggregate,
    r_wht_01_rate,
]
