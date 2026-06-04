"""Dead-rules engine orchestration.

Collects the per-category rule functions into one registry and runs them over an
invoice, rolling the findings into a RuleResult. Every rule is a pure function of
(Invoice, RuleContext) returning zero or more Findings — deterministic, no LLM,
no I/O. The registry order is the order findings are reported in.
"""

from __future__ import annotations

from services.knowledge.rules import (
    arithmetic,
    completeness,
    dedup,
    membership,
    validity,
)
from services.knowledge.rules.context import (
    Invoice,
    RuleContext,
    RuleResult,
    summarize,
)

# All first-batch rules, grouped by category in reporting order.
REGISTRY = [
    *validity.RULES,
    *arithmetic.RULES,
    *dedup.RULES,
    *completeness.RULES,
    *membership.RULES,
]


def run_rules(invoice: Invoice, ctx: RuleContext) -> RuleResult:
    findings = []
    for rule in REGISTRY:
        findings.extend(rule(invoice, ctx))
    return summarize(findings)
