"""Client-rules API: list / create / update / deactivate customer-tunable rules.

A separate router from the document routes (the main project keeps one
*_routes.py per concern). Writes are authorised against the caller's workspace
visibility and validated per rule_type in the DAL; a bad body is a 400, a
duplicate active rule for the same subject is a 409.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

import psycopg2
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from core import db
from routes.knowledge_common import authorize_write, resolve_caller
from services.knowledge import rules_dal
from services.knowledge.schema import ClientRule

router = APIRouter(prefix="/api/knowledge/rules", tags=["knowledge-rules"])


class RuleCreate(BaseModel):
    rule_type: str
    subject_type: str
    subject_key: Optional[str] = None
    rule_body: dict = {}
    workspace_client_id: Optional[int] = None
    severity: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class RulePatch(BaseModel):
    rule_body: Optional[dict] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None


def _rule_out(rule: ClientRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "workspace_client_id": rule.workspace_client_id,
        "rule_type": rule.rule_type,
        "subject_type": rule.subject_type,
        "subject_key": rule.subject_key,
        "rule_body": rule.rule_body,
        "severity": rule.severity,
        "is_active": rule.is_active,
        "effective_from": rule.effective_from.isoformat() if rule.effective_from else None,
        "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
        "origin": rule.origin,
    }


@router.get("")
def list_rules(
    request: Request, rule_type: Optional[str] = None, include_inactive: bool = False
) -> dict[str, Any]:
    # include_inactive: the settings UI lists disabled rules too (greyed, re-enableable);
    # the engine's ruleset loader stays active-only and is unaffected.
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        rules = rules_dal.list_client_rules(
            cur,
            tenant_id=identity.tenant_id,
            accessible_ids=accessible,
            rule_type=rule_type,
            include_inactive=include_inactive,
        )
    return {"rules": [_rule_out(r) for r in rules]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_rule(request: Request, body: RuleCreate) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    authorize_write(accessible, body.workspace_client_id)
    try:
        with db.get_cursor_rls(identity.tenant_id, commit=True) as cur:
            rule = rules_dal.create_client_rule(
                cur,
                tenant_id=identity.tenant_id,
                workspace_client_id=body.workspace_client_id,
                rule_type=body.rule_type,
                subject_type=body.subject_type,
                subject_key=body.subject_key,
                rule_body=body.rule_body,
                severity=body.severity,
                effective_from=body.effective_from,
                effective_to=body.effective_to,
                created_by=identity.user_id,
            )
    except rules_dal.RuleValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except psycopg2.errors.UniqueViolation as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "an active rule already exists for this subject"
        ) from exc
    return _rule_out(rule)


@router.patch("/{rule_id}")
def update_rule(request: Request, rule_id: int, body: RulePatch) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    try:
        with db.get_cursor_rls(identity.tenant_id, commit=True) as cur:
            rule = rules_dal.update_client_rule(
                cur,
                tenant_id=identity.tenant_id,
                rule_id=rule_id,
                accessible_ids=accessible,
                rule_body=body.rule_body,
                severity=body.severity,
                is_active=body.is_active,
            )
    except rules_dal.RuleValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rule not found")
    return _rule_out(rule)


@router.delete("/{rule_id}")
def delete_rule(request: Request, rule_id: int) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id, commit=True) as cur:
        deactivated = rules_dal.deactivate_client_rule(
            cur, tenant_id=identity.tenant_id, rule_id=rule_id, accessible_ids=accessible
        )
    if not deactivated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rule not found")
    return {"status": "deactivated", "rule_id": rule_id}
