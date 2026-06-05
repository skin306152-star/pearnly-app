"""Persistence for client_rules and the engine's rule loader.

load_client_rules pulls a tenant's active, in-effect rules (firm-wide plus the
current account set) and indexes them into a ClientRuleSet; firm rules are
ordered first so a client-specific row overwrites the firm default for the same
subject. Writes are validated per rule_type before they hit the table. Every
query is tenant-scoped, and reads honour workspace-client visibility.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from psycopg2.extras import Json

from services.knowledge.rules.context import ClientRuleSet
from services.knowledge.schema import (
    ORIGIN_MANUAL,
    RULE_ACCOUNTING_PERIOD,
    RULE_AMOUNT_LIMIT,
    RULE_FEATURE_TOGGLE,
    RULE_NO_AUTO_PUSH_CATEGORY,
    RULE_SUPPLIER_ALLOWLIST,
    RULE_SUPPLIER_FORCE_REVIEW,
    RULE_TYPES,
    RULE_WHT_RATE,
    SUBJECT_CATEGORY,
    SUBJECT_CONTRACT,
    SUBJECT_GLOBAL,
    SUBJECT_SUPPLIER,
    SUBJECT_TYPES,
    ClientRule,
)
from services.knowledge.access import AccessibleIds, workspace_filter

_CR_COLS = (
    "id, tenant_id, workspace_client_id, rule_type, subject_type, subject_key, "
    "rule_body, severity, is_active, effective_from, effective_to, origin, created_at"
)


class RuleValidationError(ValueError):
    """A client_rules write whose body or subject does not fit its rule_type."""


def _as_rule(row: dict) -> ClientRule:
    return ClientRule(
        id=row["id"],
        tenant_id=str(row["tenant_id"]),
        workspace_client_id=row["workspace_client_id"],
        rule_type=row["rule_type"],
        subject_type=row["subject_type"],
        subject_key=row["subject_key"],
        rule_body=row["rule_body"] or {},
        severity=row["severity"],
        is_active=row["is_active"],
        effective_from=row["effective_from"],
        effective_to=row["effective_to"],
        origin=row["origin"],
        created_at=row["created_at"],
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuleValidationError(message)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_rule(rule_type: str, subject_type: str, subject_key, body: dict) -> None:
    """Reject a write whose shape does not match its rule_type. Raises on invalid."""
    _require(rule_type in RULE_TYPES, f"unknown rule_type: {rule_type}")
    _require(subject_type in SUBJECT_TYPES, f"unknown subject_type: {subject_type}")
    body = body or {}

    if rule_type == RULE_FEATURE_TOGGLE:
        _require(subject_type == SUBJECT_GLOBAL, "feature_toggle is global")
        _require(bool(subject_key), "feature_toggle needs a subject_key (toggle name)")
        _require(isinstance(body.get("enabled"), bool), "feature_toggle body needs enabled:bool")
    elif rule_type in (RULE_SUPPLIER_ALLOWLIST, RULE_SUPPLIER_FORCE_REVIEW):
        _require(subject_type == SUBJECT_SUPPLIER, f"{rule_type} subject must be supplier")
        _require(bool(subject_key), f"{rule_type} needs a subject_key (seller_tax_id)")
    elif rule_type == RULE_AMOUNT_LIMIT:
        _require(
            subject_type in (SUBJECT_SUPPLIER, SUBJECT_CATEGORY, SUBJECT_CONTRACT, SUBJECT_GLOBAL),
            "amount_limit subject must be supplier|category|contract|global",
        )
        # A global limit applies to every invoice (replaces the old large_invoice
        # alert); only the scoped subjects need a subject_key.
        _require(
            subject_type == SUBJECT_GLOBAL or bool(subject_key),
            "amount_limit needs a subject_key unless global",
        )
        _require(_is_number(body.get("limit")), "amount_limit body needs limit:number")
        _require(body.get("basis", "total") in ("total", "net"), "basis must be total|net")
        _require(
            body.get("period", "per_invoice") in ("per_invoice", "monthly"),
            "period must be per_invoice|monthly",
        )
    elif rule_type == RULE_NO_AUTO_PUSH_CATEGORY:
        _require(subject_type == SUBJECT_CATEGORY, "no_auto_push_category subject must be category")
        _require(bool(subject_key), "no_auto_push_category needs a category subject_key")
    elif rule_type == RULE_WHT_RATE:
        _require(subject_type == SUBJECT_CATEGORY, "wht_rate subject must be category")
        _require(bool(subject_key), "wht_rate needs a category subject_key")
        _require(_is_number(body.get("expected_rate")), "wht_rate body needs expected_rate:number")
    elif rule_type == RULE_ACCOUNTING_PERIOD:
        _require(subject_type == SUBJECT_GLOBAL, "accounting_period is global")
        mode = body.get("mode")
        _require(
            mode in ("fixed", "current_month", "prev_month"),
            "accounting_period mode must be fixed|current_month|prev_month",
        )
        if mode == "fixed":
            _require(
                bool(body.get("period_start")) and bool(body.get("period_end")),
                "fixed accounting_period needs period_start and period_end",
            )


def load_client_rules(
    cur, *, tenant_id: str, workspace_client_id: Optional[int], on_date: Optional[date] = None
) -> ClientRuleSet:
    on_date = on_date or date.today()
    cur.execute(
        f"SELECT {_CR_COLS} FROM client_rules "
        "WHERE tenant_id = %s AND is_active "
        "AND (workspace_client_id IS NULL OR workspace_client_id = %s) "
        "AND (effective_from IS NULL OR effective_from <= %s) "
        "AND (effective_to IS NULL OR effective_to >= %s) "
        "ORDER BY workspace_client_id NULLS FIRST, id",
        (tenant_id, workspace_client_id, on_date, on_date),
    )
    return ClientRuleSet.from_rules([_as_rule(r) for r in cur.fetchall()])


def create_client_rule(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int],
    rule_type: str,
    subject_type: str,
    subject_key: Optional[str],
    rule_body: dict,
    severity: Optional[str] = None,
    effective_from: Optional[date] = None,
    effective_to: Optional[date] = None,
    created_by: Optional[str] = None,
) -> ClientRule:
    validate_rule(rule_type, subject_type, subject_key, rule_body)
    cur.execute(
        "INSERT INTO client_rules "
        "(tenant_id, workspace_client_id, rule_type, subject_type, subject_key, "
        " rule_body, severity, effective_from, effective_to, origin, created_by) "
        f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_CR_COLS}",
        (
            tenant_id,
            workspace_client_id,
            rule_type,
            subject_type,
            subject_key,
            Json(rule_body or {}),
            severity,
            effective_from,
            effective_to,
            ORIGIN_MANUAL,
            created_by,
        ),
    )
    return _as_rule(cur.fetchone())


def list_client_rules(
    cur,
    *,
    tenant_id: str,
    accessible_ids: AccessibleIds,
    rule_type: Optional[str] = None,
    include_inactive: bool = False,
) -> list[ClientRule]:
    # The engine loads active rules only; the settings UI passes include_inactive
    # so disabled rules stay listed (greyed) and can be re-enabled.
    active_clause = "" if include_inactive else " AND is_active"
    where, params = workspace_filter(accessible_ids)
    sql = f"SELECT {_CR_COLS} FROM client_rules WHERE tenant_id = %s{active_clause}" + where
    args: list = [tenant_id, *params]
    if rule_type is not None:
        sql += " AND rule_type = %s"
        args.append(rule_type)
    sql += " ORDER BY id"
    cur.execute(sql, args)
    return [_as_rule(r) for r in cur.fetchall()]


def get_client_rule(
    cur, *, tenant_id: str, rule_id: int, accessible_ids: AccessibleIds
) -> Optional[ClientRule]:
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        f"SELECT {_CR_COLS} FROM client_rules WHERE tenant_id = %s AND id = %s" + where,
        [tenant_id, rule_id, *params],
    )
    row = cur.fetchone()
    return _as_rule(row) if row is not None else None


def update_client_rule(
    cur,
    *,
    tenant_id: str,
    rule_id: int,
    accessible_ids: AccessibleIds,
    rule_body: Optional[dict] = None,
    severity: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[ClientRule]:
    """Patch a rule's body / severity / active flag, returning the updated row."""
    existing = get_client_rule(
        cur, tenant_id=tenant_id, rule_id=rule_id, accessible_ids=accessible_ids
    )
    if existing is None:
        return None
    new_body = existing.rule_body if rule_body is None else rule_body
    if rule_body is not None:
        validate_rule(existing.rule_type, existing.subject_type, existing.subject_key, new_body)
    cur.execute(
        "UPDATE client_rules SET rule_body = %s, severity = %s, is_active = %s, "
        f"updated_at = now() WHERE tenant_id = %s AND id = %s RETURNING {_CR_COLS}",
        (
            Json(new_body),
            existing.severity if severity is None else severity,
            existing.is_active if is_active is None else is_active,
            tenant_id,
            rule_id,
        ),
    )
    row = cur.fetchone()
    return _as_rule(row) if row is not None else None


def deactivate_client_rule(
    cur, *, tenant_id: str, rule_id: int, accessible_ids: AccessibleIds
) -> bool:
    """Soft-delete: mark inactive so it stops loading but stays auditable."""
    where, params = workspace_filter(accessible_ids)
    cur.execute(
        "UPDATE client_rules SET is_active = false, updated_at = now() "
        "WHERE tenant_id = %s AND id = %s AND is_active" + where,
        [tenant_id, rule_id, *params],
    )
    return cur.rowcount > 0


def record_feedback(cur, *, tenant_id: str, rule_id: int, accepted: bool) -> bool:
    """Bump accepted_count or dismissed_count when a user judges a finding."""
    column = "accepted_count" if accepted else "dismissed_count"
    cur.execute(
        f"UPDATE client_rules SET {column} = {column} + 1 " "WHERE tenant_id = %s AND id = %s",
        (tenant_id, rule_id),
    )
    return cur.rowcount > 0


def increment_hit_counts(cur, *, tenant_id: str, rule_ids: Sequence[int]) -> None:
    """Count findings produced by client rules (skips global rules with no id)."""
    ids = [rid for rid in rule_ids if rid is not None]
    if not ids:
        return
    cur.execute(
        "UPDATE client_rules SET hit_count = hit_count + 1 "
        "WHERE tenant_id = %s AND id = ANY(%s::bigint[])",
        (tenant_id, list(ids)),
    )
