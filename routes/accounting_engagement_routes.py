"""ERP 商户与 Cowork 事务所的关系确认 API；默认由关系灰度闸隐藏。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import _log_op
from services.accounting_engagement import flags, lifecycle, store
from services.accounting_engagement.errors import (
    FIRM_INACTIVE,
    NOT_ACTIVE,
    WORKSPACE_MISMATCH,
    EngagementError,
)
from services.auth.entrance import COWORK, ERP
from services.authz.deps import get_authz, require_perm
from services.client_submission import store as submission_store
from services.client_submission.errors import DELIVERY_FAILED, PUBLIC_CODES

router = APIRouter()


class EngagementAcceptBody(BaseModel):
    workspace_client_id: int = Field(..., gt=0)


def _participant(request: Request, expected_entry: str, permission: str) -> dict:
    user = require_perm(request, permission)
    tenant_id = user.get("tenant_id")
    if not tenant_id or user.get("entry") != expected_entry:
        raise HTTPException(403, detail="ERR_ENGAGEMENT_FORBIDDEN")
    if not flags.enabled_for(str(tenant_id)):
        raise HTTPException(404, detail="not_found")
    return user


def _http_error(error: EngagementError) -> HTTPException:
    status_by_code = {
        FIRM_INACTIVE: 422,
        NOT_ACTIVE: 409,
        WORKSPACE_MISMATCH: 422,
    }
    return HTTPException(status_by_code.get(error.code, 403), detail=error.code)


def _public_row(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "id",
            "firm_tenant_id",
            "firm_workspace_client_id",
            "merchant_tenant_id",
            "merchant_workspace_client_id",
            "status",
            "merchant_accepted_at",
            "firm_accepted_at",
            "active_from",
            "ended_at",
            "created_at",
            "updated_at",
        )
    }


def _submission_summary(row: dict) -> dict:
    summary = {
        key: row.get(key)
        for key in (
            "id",
            "engagement_id",
            "source_tenant_id",
            "source_workspace_client_id",
            "source_document_type",
            "source_document_id",
            "source_revision",
            "target_tenant_id",
            "target_workspace_client_id",
            "status",
            "cowork_history_id",
            "attempts",
            "last_error",
            "created_at",
            "delivered_at",
            "updated_at",
        )
    }
    error = str(summary.get("last_error") or "")
    if error and error not in PUBLIC_CODES:
        summary["last_error"] = DELIVERY_FAILED
    return summary


def _submission_scope(request: Request, user: dict) -> list[int] | None:
    authz = get_authz(request, user)
    if authz.scope_mode != "assigned":
        return None
    return sorted(authz.workspace_ids or ())


def _submission_list(request: Request, user: dict, participant_side: str) -> dict:
    tenant_id = str(user["tenant_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        rows = submission_store.list_for_tenant(
            cur,
            tenant_id=tenant_id,
            participant_side=participant_side,
            workspace_client_ids=_submission_scope(request, user),
        )
    return {"submissions": [_submission_summary(row) for row in rows]}


def _submission_detail(
    request: Request, user: dict, submission_id: str, participant_side: str
) -> dict:
    tenant_id = str(user["tenant_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        row = submission_store.get_for_tenant(
            cur,
            tenant_id=tenant_id,
            submission_id=submission_id,
            participant_side=participant_side,
            workspace_client_ids=_submission_scope(request, user),
        )
    if not row:
        raise HTTPException(404, detail="not_found")
    return {
        "submission": {
            **_submission_summary(row),
            "snapshot": row.get("snapshot_json") or {},
            "original_file_available": bool(row.get("original_file_ref")),
        }
    }


@router.get("/api/erp/accounting-engagements")
async def list_merchant_engagements(request: Request):
    user = _participant(request, ERP, "settings.workspace.manage")
    tenant_id = str(user["tenant_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        rows = store.list_for_tenant(cur, tenant_id=tenant_id)
    return {"engagements": [_public_row(row) for row in rows]}


@router.post("/api/erp/accounting-engagements/{engagement_id}/accept")
async def accept_merchant_engagement(
    engagement_id: str, body: EngagementAcceptBody, request: Request
):
    user = _participant(request, ERP, "settings.workspace.manage")
    tenant_id = str(user["tenant_id"])
    try:
        with db.get_cursor_rls(
            tenant_id=tenant_id,
            user_id=str(user["id"]),
            commit=True,
        ) as cur:
            row = lifecycle.accept_merchant(
                cur,
                engagement_id=engagement_id,
                merchant_tenant_id=tenant_id,
                workspace_client_id=body.workspace_client_id,
            )
    except EngagementError as error:
        raise _http_error(error) from error
    _log_op(
        request,
        user,
        "erp.engagement.accept",
        target_type="accounting_engagement",
        target_id=engagement_id,
        details={"workspace_client_id": body.workspace_client_id, "status": row["status"]},
    )
    return {"ok": True, "engagement": _public_row(row)}


@router.get("/api/erp/client-submissions")
async def list_merchant_submissions(request: Request):
    user = _participant(request, ERP, "stockcard.report.view")
    return _submission_list(request, user, "source")


@router.get("/api/erp/client-submissions/{submission_id}")
async def get_merchant_submission(submission_id: UUID, request: Request):
    user = _participant(request, ERP, "stockcard.report.view")
    return _submission_detail(request, user, str(submission_id), "source")


@router.get("/api/cowork/accounting-engagements")
async def list_firm_engagements(request: Request):
    user = _participant(request, COWORK, "settings.workspace.manage")
    tenant_id = str(user["tenant_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        rows = store.list_for_tenant(cur, tenant_id=tenant_id)
    return {"engagements": [_public_row(row) for row in rows]}


@router.post("/api/cowork/accounting-engagements/{engagement_id}/accept")
async def accept_firm_engagement(engagement_id: str, body: EngagementAcceptBody, request: Request):
    user = _participant(request, COWORK, "settings.workspace.manage")
    tenant_id = str(user["tenant_id"])
    try:
        with db.get_cursor_rls(
            tenant_id=tenant_id,
            user_id=str(user["id"]),
            commit=True,
        ) as cur:
            row = lifecycle.accept_firm(
                cur,
                engagement_id=engagement_id,
                firm_tenant_id=tenant_id,
                workspace_client_id=body.workspace_client_id,
            )
    except EngagementError as error:
        raise _http_error(error) from error
    _log_op(
        request,
        user,
        "cowork.engagement.accept",
        target_type="accounting_engagement",
        target_id=engagement_id,
        details={"workspace_client_id": body.workspace_client_id, "status": row["status"]},
    )
    return {"ok": True, "engagement": _public_row(row)}


@router.get("/api/cowork/client-submissions")
async def list_firm_submissions(request: Request):
    user = _participant(request, COWORK, "acct.entry.view")
    return _submission_list(request, user, "target")


@router.get("/api/cowork/client-submissions/{submission_id}")
async def get_firm_submission(submission_id: UUID, request: Request):
    user = _participant(request, COWORK, "acct.entry.view")
    return _submission_detail(request, user, str(submission_id), "target")
