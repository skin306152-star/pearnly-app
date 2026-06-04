"""Inputs and outputs for the dead-rules engine.

An Invoice is the OCR-parsed document the rules read; a RuleContext carries
everything a rule needs beyond the invoice itself — the tenant's loaded
client_rules, the workspace entity's own tax id (for ownership checks), today's
date, and the duplicate-lookup callables. Dedup queries are injected rather than
performed here so the rules stay pure and unit-testable without a database; the
caller (P5 / the route) supplies real lookups, tests supply fakes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from services.knowledge.schema import (
    RULE_ACCOUNTING_PERIOD,
    RULE_AMOUNT_LIMIT,
    RULE_FEATURE_TOGGLE,
    RULE_NO_AUTO_PUSH_CATEGORY,
    RULE_SUPPLIER_ALLOWLIST,
    RULE_SUPPLIER_FORCE_REVIEW,
    RULE_WHT_RATE,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    ClientRule,
)

# Money comparisons use this absolute tolerance to avoid float/rounding noise.
AMOUNT_TOLERANCE = 0.01

_SEVERITY_RANK = {SEVERITY_LOW: 0, SEVERITY_MEDIUM: 1, SEVERITY_HIGH: 2}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message_key: str
    evidence: dict
    client_rule_id: Optional[int] = None


@dataclass
class RuleResult:
    risk_level: str
    needs_human_review: bool
    findings: list[Finding]


def summarize(findings: list[Finding]) -> RuleResult:
    """Roll findings into a risk level (max severity) and human-review flag."""
    if not findings:
        return RuleResult(risk_level=SEVERITY_LOW, needs_human_review=False, findings=[])
    top = max(findings, key=lambda f: _SEVERITY_RANK.get(f.severity, 0)).severity
    needs_review = any(f.severity == SEVERITY_HIGH for f in findings)
    return RuleResult(risk_level=top, needs_human_review=needs_review, findings=findings)


@dataclass
class Invoice:
    seller_tax_id: Optional[str] = None
    seller_name: Optional[str] = None
    seller_address: Optional[str] = None
    seller_branch: Optional[str] = None
    buyer_tax_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_address: Optional[str] = None
    invoice_no: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: str = "THB"
    line_items: list[dict] = field(default_factory=list)
    net_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None
    doc_type: Optional[str] = None
    tax_exempt: bool = False  # zero-rated / exempt: VAT=0 is legal, skip VAT math
    is_multipage: bool = False
    pages: list[dict] = field(default_factory=list)  # per-page {net,vat,total} amounts
    raw_text: str = ""
    category: Optional[str] = None
    declared_wht_rate: Optional[float] = None

    @classmethod
    def from_payload(cls, payload: dict) -> "Invoice":
        """Build from an OCR payload dict, ignoring unknown keys."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in payload.items() if k in known})


_NoDuplicate = Callable[..., object]


@dataclass
class ClientRuleSet:
    """Loaded client_rules indexed for O(1) lookup during a rules run."""

    toggles: dict[str, bool] = field(default_factory=dict)
    allowlisted_suppliers: set[str] = field(default_factory=set)
    force_review_suppliers: dict[str, ClientRule] = field(default_factory=dict)
    amount_limits: dict[tuple[str, str], ClientRule] = field(default_factory=dict)
    no_push_categories: dict[str, ClientRule] = field(default_factory=dict)
    wht_rates: dict[str, ClientRule] = field(default_factory=dict)
    accounting_period: Optional[ClientRule] = None

    def toggle(self, name: str) -> bool:
        return self.toggles.get(name, False)

    @classmethod
    def from_rules(cls, rules: list[ClientRule]) -> "ClientRuleSet":
        """Index a tenant's active rules. Client-specific rows (already preferred
        by the loader) overwrite firm-wide ones sharing the same subject."""
        ruleset = cls()
        for rule in rules:
            ruleset._add(rule)
        return ruleset

    def _add(self, rule: ClientRule) -> None:
        key = rule.subject_key or ""
        if rule.rule_type == RULE_FEATURE_TOGGLE:
            self.toggles[key] = bool(rule.rule_body.get("enabled", False))
        elif rule.rule_type == RULE_SUPPLIER_ALLOWLIST:
            self.allowlisted_suppliers.add(key)
        elif rule.rule_type == RULE_SUPPLIER_FORCE_REVIEW:
            self.force_review_suppliers[key] = rule
        elif rule.rule_type == RULE_AMOUNT_LIMIT:
            self.amount_limits[(rule.subject_type, key)] = rule
        elif rule.rule_type == RULE_NO_AUTO_PUSH_CATEGORY:
            self.no_push_categories[key] = rule
        elif rule.rule_type == RULE_WHT_RATE:
            self.wht_rates[key] = rule
        elif rule.rule_type == RULE_ACCOUNTING_PERIOD:
            self.accounting_period = rule


@dataclass
class RuleContext:
    tenant_id: str
    workspace_client_id: Optional[int] = None
    workspace_client_tax_id: Optional[str] = None
    rules: ClientRuleSet = field(default_factory=ClientRuleSet)
    today: Optional[date] = None
    # (seller_tax_id, invoice_no) -> existing history id, or None.
    find_exact_duplicate: Callable[[str, str], Optional[str]] = lambda s, n: None
    # (seller_tax_id, total_amount, invoice_date) -> list of candidate history ids.
    find_suspected_duplicates: Callable[[str, Optional[float], Optional[str]], list] = (
        lambda s, t, d: []
    )


def severity_for(rule_id: str, default: str, ctx_rule: Optional[ClientRule]) -> str:
    """A client_rules row may override a rule's default severity."""
    if ctx_rule is not None and ctx_rule.severity:
        return ctx_rule.severity
    return default


__all__ = [
    "AMOUNT_TOLERANCE",
    "ClientRuleSet",
    "Finding",
    "Invoice",
    "RuleContext",
    "RuleResult",
    "SEVERITY_HIGH",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "severity_for",
    "summarize",
]
