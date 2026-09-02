# -*- coding: utf-8 -*-
"""Read-only ERP formal-confirmation status used between review and push."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _check_history_access, _tid
from services.erp import team_access
from services.intake_bridge import erp_confirmation_access

router = APIRouter()


class ConfirmationStatusRequest(BaseModel):
    history_ids: list[str] = Field(..., min_length=1, max_length=500)
    workspace_client_id: int


@router.post("/api/ocr/convert-documents/status")
async def confirmation_status(req: ConfirmationStatusRequest, request: Request):
    """Verify formal records; shared confirmation derives scope from each stored history."""
    user = get_current_user_from_request(request)
    _check_history_access(user)
    erp_confirmation_access.require_formal_conversion_entry(user)
    tenant_id = _tid(user)
    team_access.assert_owned_histories(request, user, req.history_ids)
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
        return erp_confirmation_access.confirmation_status(
            cur,
            request,
            user,
            tenant_id,
            req.workspace_client_id,
            req.history_ids,
        )
