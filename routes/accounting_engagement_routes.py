"""ERP 商户与 Cowork 事务所的关系确认 API；默认由关系灰度闸隐藏。"""

from __future__ import annotations

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
from services.authz.deps import require_perm

router = APIRouter()


class EngagementAcceptBody(BaseModel):
    workspace_client_id: int = Field(..., gt=0)


def _participant(request: Request, expected_entry: str) -> dict:
    user = require_perm(request, "settings.workspace.manage")
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


@router.get("/api/erp/accounting-engagements")
async def list_merchant_engagements(request: Request):
    user = _participant(request, ERP)
    tenant_id = str(user["tenant_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        rows = store.list_for_tenant(cur, tenant_id=tenant_id)
    return {"engagements": [_public_row(row) for row in rows]}


@router.post("/api/erp/accounting-engagements/{engagement_id}/accept")
async def accept_merchant_engagement(
    engagement_id: str, body: EngagementAcceptBody, request: Request
):
    user = _participant(request, ERP)
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


@router.get("/api/cowork/accounting-engagements")
async def list_firm_engagements(request: Request):
    user = _participant(request, COWORK)
    tenant_id = str(user["tenant_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        rows = store.list_for_tenant(cur, tenant_id=tenant_id)
    return {"engagements": [_public_row(row) for row in rows]}


@router.post("/api/cowork/accounting-engagements/{engagement_id}/accept")
async def accept_firm_engagement(engagement_id: str, body: EngagementAcceptBody, request: Request):
    user = _participant(request, COWORK)
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
