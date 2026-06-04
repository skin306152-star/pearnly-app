# -*- coding: utf-8 -*-
"""Bridge: run the knowledge dead-rules engine from the OCR exception hook.

This is the single rule source: it replaces exception_checks' former inline
invoice rules (duplicate / amount_missing / math_mismatch / tax_id) with the
rules engine in services.knowledge, so there is one rule source instead of two.

It maps the OCR field dict to an Invoice, builds a RuleContext (the tenant's
client_rules plus tenant-scoped duplicate lookups over ocr_history), runs the
engine, and writes each enabled Finding to the existing exception store —
honouring the same per-(seller, rule) whitelist. confidence_low and the LINE
reminders stay in exception_checks; this only produces the rule findings and
reports back which were high-severity so the caller fires the same reminders.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core import db
from services.knowledge.rules.context import ClientRuleSet, Invoice, RuleContext
from services.knowledge.rules_dal import load_client_rules
from services.knowledge.rules_engine import run_rules
from services.knowledge.schema import SEVERITY_HIGH, ClientRule

logger = logging.getLogger("mr-pilot")

# Rule groups live in the unified path one group at a time, each turned on only
# once its simulate-trigger tests pass (plan P2). A finding whose rule_id is not
# enabled is still computed but not written, so enabling a group is one edit.
#   - R-VAT/R-SUM/R-LINE/R-MULTIPAGE/R-TAXID/R-DUP: replace the legacy inline
#     rules (math_mismatch -> arithmetic, tax_id -> R-TAXID, duplicate -> R-DUP).
#   - R-DATE: invoice-date legality (unparseable / future) + accounting period.
#   - R-SUP/R-LIMIT/R-CAT: customer rules — inert until a client_rule configures
#     them, so safe to enable now; this is the engine's net-new value.
# Held back until their inputs exist: R-WHT and R-WS (OCR carries no declared WHT
# rate or workspace tax id), R-BRANCH (no seller_branch field), and R-FIELD
# completeness (needs doc_type / address the OCR field dict does not provide;
# enabling as-is would over-report on every invoice).
ENABLED_RULE_PREFIXES = (
    "R-VAT",
    "R-SUM",
    "R-LINE",
    "R-MULTIPAGE",
    "R-TAXID",
    "R-DUP",
    "R-DATE",
    "R-SUP",
    "R-LIMIT",
    "R-CAT",
)


def _to_float(raw: Any) -> Optional[float]:
    """Parse an OCR money/number string to float; unparseable -> None."""
    if raw is None:
        return None
    try:
        s = str(raw).replace(",", "").replace("฿", "").replace("THB", "").strip()
        return float(s) if s else None
    except (TypeError, ValueError):
        return None


def _line_items(raw_items: Any) -> List[dict]:
    # OCR items are {name, qty, price, subtotal}; the engine reads
    # {qty, unit_price, amount}. Numbers are normalised so comma- or
    # currency-formatted OCR strings still feed the arithmetic rules.
    items: List[dict] = []
    for it in raw_items or []:
        if not isinstance(it, dict):
            continue
        items.append(
            {
                "qty": _to_float(it.get("qty")),
                "unit_price": _to_float(it.get("price")),
                "amount": _to_float(it.get("subtotal")),
            }
        )
    return items


def build_invoice(
    fields: Dict[str, Any],
    *,
    invoice_no: Optional[str],
    seller_name: Optional[str],
    total_amount: Optional[float],
) -> Invoice:
    """Translate the OCR field dict into the engine's Invoice (key names differ)."""
    fields = fields or {}
    return Invoice(
        seller_tax_id=fields.get("seller_tax") or None,
        seller_name=seller_name or fields.get("seller_name") or None,
        buyer_tax_id=fields.get("buyer_tax") or None,
        buyer_name=fields.get("buyer_name") or None,
        invoice_no=invoice_no or fields.get("invoice_number") or fields.get("invoice_no") or None,
        invoice_date=fields.get("invoice_date") or fields.get("date") or None,
        net_amount=_to_float(fields.get("subtotal")),
        vat_amount=_to_float(fields.get("vat")),
        total_amount=total_amount,
        line_items=_line_items(fields.get("items")),
        category=fields.get("category") or None,
    )


def _scope_sql(user_id: str, tenant_id: Optional[str]) -> tuple[str, list]:
    """Visibility predicate: the whole tenant when set, else just this user."""
    if tenant_id:
        return "user_id IN (SELECT id FROM users WHERE tenant_id = %s)", [tenant_id]
    return "user_id = %s", [user_id]


def _query_one_id(where: List[str], params: list) -> Optional[str]:
    try:
        with db.get_cursor() as cur:
            cur.execute(
                f"SELECT id FROM ocr_history WHERE {' AND '.join(where)} "
                "ORDER BY created_at DESC LIMIT 1",
                params,
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.warning("knowledge dedup exact lookup failed: %s", e)
        return None


def _query_ids(where: List[str], params: list, limit: int = 20) -> List[str]:
    try:
        with db.get_cursor() as cur:
            cur.execute(
                f"SELECT id FROM ocr_history WHERE {' AND '.join(where)} "
                f"ORDER BY created_at DESC LIMIT {int(limit)}",
                params,
            )
            return [str(r["id"]) for r in cur.fetchall()]
    except Exception as e:
        logger.warning("knowledge dedup suspected lookup failed: %s", e)
        return []


def make_dedup_lookups(
    *,
    user_id: str,
    tenant_id: Optional[str],
    exclude_history_id: str,
    seller_name: Optional[str],
):
    """Build the two tenant-scoped duplicate lookups the engine injects.

    ocr_history has no seller_tax column (it lives in the pages JSON), so the
    engine's seller_tax_id argument is unused; matches key on invoice_no / amount
    narrowed by seller_name, which the indexed columns support. Both always
    exclude the current row and stay within the tenant.
    """
    scope, scope_params = _scope_sql(user_id, tenant_id)

    def find_exact_duplicate(
        seller_tax_id: Optional[str], invoice_no: Optional[str]
    ) -> Optional[str]:
        if not invoice_no:
            return None
        where = [
            scope,
            "id <> %s::uuid",
            "invoice_no IS NOT NULL",
            "invoice_no <> ''",
            "LOWER(invoice_no) = LOWER(%s)",
        ]
        params = [*scope_params, exclude_history_id, invoice_no]
        if seller_name:
            where.append("seller_name IS NOT NULL AND LOWER(seller_name) = LOWER(%s)")
            params.append(seller_name)
        return _query_one_id(where, params)

    def find_suspected_duplicates(
        seller_tax_id: Optional[str], total_amount: Optional[float], invoice_date: Optional[str]
    ) -> List[str]:
        # Looser match for a re-upload under a different invoice_no: same seller
        # and same total within the tenant. invoice_date is not compared — OCR
        # returns it in mixed (incl. Buddhist-era) formats that do not align with
        # the stored date column.
        if total_amount is None or not seller_name:
            return []
        where = [
            scope,
            "id <> %s::uuid",
            "total_amount = %s",
            "seller_name IS NOT NULL AND LOWER(seller_name) = LOWER(%s)",
        ]
        params = [*scope_params, exclude_history_id, float(total_amount), seller_name]
        return _query_ids(where, params)

    return find_exact_duplicate, find_suspected_duplicates


def _load_ruleset(tenant_id: Optional[str], workspace_client_id: Optional[int]) -> ClientRuleSet:
    # Customer rules need a tenant and the client_rules table, which the
    # knowledge feature owns. Until KNOWLEDGE_ENABLED is set (and the table
    # provisioned) we skip the query entirely and run only the global rules, so
    # the engine works on day one without touching an unprovisioned table.
    if not tenant_id or os.environ.get("KNOWLEDGE_ENABLED") != "1":
        return ClientRuleSet()
    try:
        with db.get_cursor() as cur:
            return load_client_rules(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
            )
    except Exception as e:
        logger.warning("knowledge client_rules load failed (tenant=%s): %s", tenant_id, e)
        return ClientRuleSet()


def _resolve_workspace_client_id(
    user_id: str, tenant_id: Optional[str], history_id: str
) -> Optional[int]:
    # Client-specific rules scope by workspace_client_id; the hook is not given
    # one, so resolve it from the history row (the call sites stay untouched).
    scope, params = _scope_sql(user_id, tenant_id)
    try:
        with db.get_cursor() as cur:
            cur.execute(
                f"SELECT workspace_client_id FROM ocr_history WHERE id = %s::uuid AND {scope} LIMIT 1",
                [history_id, *params],
            )
            row = cur.fetchone()
            return row["workspace_client_id"] if row else None
    except Exception as e:
        logger.warning("knowledge workspace lookup failed (hid=%s): %s", history_id, e)
        return None


def build_context(
    *,
    user_id: str,
    tenant_id: Optional[str],
    workspace_client_id: Optional[int],
    exclude_history_id: str,
    seller_name: Optional[str],
) -> RuleContext:
    ruleset = _load_ruleset(tenant_id, workspace_client_id)
    find_exact, find_suspected = make_dedup_lookups(
        user_id=user_id,
        tenant_id=tenant_id,
        exclude_history_id=exclude_history_id,
        seller_name=seller_name,
    )
    return RuleContext(
        tenant_id=tenant_id or "",
        workspace_client_id=workspace_client_id,
        rules=ruleset,
        today=datetime.now(timezone.utc).date(),
        find_exact_duplicate=find_exact,
        find_suspected_duplicates=find_suspected,
    )


def _is_enabled(rule_id: str) -> bool:
    return any(rule_id.startswith(prefix) for prefix in ENABLED_RULE_PREFIXES)


def _rules_by_id(ruleset: ClientRuleSet) -> dict[int, ClientRule]:
    """Index the loaded client rules by id, for per-finding rule_body lookups.

    Only rule kinds that attach a client_rule_id to their findings are indexed
    (force-review, amount-limit, no-auto-push, wht, accounting-period); the
    allowlist/toggle kinds produce id-less findings, so they need no lookup.
    """
    rules: list[ClientRule] = []
    rules.extend(ruleset.force_review_suppliers.values())
    rules.extend(ruleset.amount_limits.values())
    rules.extend(ruleset.no_push_categories.values())
    rules.extend(ruleset.wht_rates.values())
    if ruleset.accounting_period is not None:
        rules.append(ruleset.accounting_period)
    return {rule.id: rule for rule in rules}


def _wants_line_push(finding, rules_by_id: dict[int, ClientRule]) -> bool:
    """A customer rule may opt into a LINE push regardless of severity.

    rule_body.notify_line is the "🔔 也推 LINE" option — it lets, e.g., an
    amount-limit rule ping the boss without being high-severity, replacing the
    retired large_invoice notification.
    """
    if not finding.client_rule_id:
        return False
    rule = rules_by_id.get(finding.client_rule_id)
    return bool(rule and rule.rule_body.get("notify_line"))


def run_and_record(
    *,
    history_id: str,
    user_id: str,
    tenant_id: Optional[str],
    seller_name: Optional[str],
    invoice_no: Optional[str],
    total_amount: Optional[float],
    fields: Dict[str, Any],
) -> List[str]:
    """Run the engine over one OCR result and write its enabled findings.

    Returns the rule_ids that should fire a LINE reminder: every high-severity
    finding, plus any finding whose customer rule opted into notify_line. The
    caller pushes the same LINE reminders the legacy path did.
    """
    history_id = str(history_id)
    workspace_client_id = _resolve_workspace_client_id(user_id, tenant_id, history_id)
    invoice = build_invoice(
        fields, invoice_no=invoice_no, seller_name=seller_name, total_amount=total_amount
    )
    ctx = build_context(
        user_id=user_id,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        exclude_history_id=history_id,
        seller_name=seller_name,
    )
    result = run_rules(invoice, ctx)
    rules_by_id = _rules_by_id(ctx.rules)

    line_push: List[str] = []
    for finding in result.findings:
        if not _is_enabled(finding.rule_id):
            continue
        if db.is_exception_whitelisted(user_id, tenant_id, seller_name, finding.rule_id):
            continue
        ex_id = db.insert_exception(
            user_id=user_id,
            tenant_id=tenant_id,
            history_id=history_id,
            rule_code=finding.rule_id,
            severity=finding.severity,
            seller_name=seller_name,
            invoice_no=invoice_no,
            total_amount=total_amount,
            detail={
                "message_key": finding.message_key,
                "evidence": finding.evidence,
                "client_rule_id": finding.client_rule_id,
            },
        )
        if not ex_id:
            continue
        if finding.severity == SEVERITY_HIGH or _wants_line_push(finding, rules_by_id):
            line_push.append(finding.rule_id)
    return line_push
