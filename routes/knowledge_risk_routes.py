"""Risk-check API: run the dead-rules engine on an OCR history, fetch the result.

POST runs a fresh check (the OCR history is fetched through the host contract,
which enforces tenant/visibility); GET returns the latest recorded check for a
history. An OCR history the caller cannot see reads as not found.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from core import db
from services.authz.deps import require_perm
from routes.knowledge_common import resolve_caller
from services.knowledge import risk_check
from services.knowledge.schema import InvoiceRiskCheck

router = APIRouter(prefix="/api/knowledge/risk-checks", tags=["knowledge-risk"])


def _check_out(check: InvoiceRiskCheck) -> dict[str, Any]:
    return {
        "id": check.id,
        "history_id": check.history_id,
        "workspace_client_id": check.workspace_client_id,
        "risk_level": check.risk_level,
        "needs_human_review": check.needs_human_review,
        "findings": check.findings,
        "status": check.status,
        "human_status": check.human_status,
        "created_at": check.created_at.isoformat(),
    }


@router.post("/from-history/{history_id}")
def run_check(request: Request, history_id: str) -> dict[str, Any]:
    require_perm(request, "kb.doc.create")
    identity, _ = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id, commit=True) as cur:
        check = risk_check.run_risk_check(cur, identity=identity, history_id=history_id)
    if check is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ocr history not found")
    return _check_out(check)


@router.get("/{history_id}")
def latest_check(request: Request, history_id: str) -> dict[str, Any]:
    require_perm(request, "kb.doc.view")
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        check = risk_check.get_latest_risk_check(
            cur,
            tenant_id=identity.tenant_id,
            history_id=history_id,
            accessible_ids=accessible,
        )
    if check is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no risk check for this history")
    return _check_out(check)
