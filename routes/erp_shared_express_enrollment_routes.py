# -*- coding: utf-8 -*-
"""Owner-only Express endpoint enrollment route."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Request
from pydantic import BaseModel, ConfigDict, Field

from core.auth import get_current_user_from_request
from services.auth.entrance import require_erp_portal
from services.erp.shared_express_enrollment import enroll_legacy_express_endpoint
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for

router = APIRouter()


class EnrollRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_generation: int = Field(default=0, ge=0, le=0)


def _workspace_header(request: Request) -> int:
    raw = request.headers.get("X-Workspace-Client-Id")
    if raw is None or not raw.strip().isdigit() or int(raw.strip()) <= 0:
        from fastapi import HTTPException

        raise HTTPException(400, detail="workspace.required")
    return int(raw.strip())


@router.post("/api/erp/endpoints/{endpoint_id}/shared/enroll")
async def enroll_shared_express_endpoint(
    endpoint_id: str, request: Request, req: Optional[EnrollRequest] = Body(default=None)
):
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    if user.get("is_super_admin") or user.get("entry") not in {"main", "cowork", "erp"}:
        from fastapi import HTTPException

        raise HTTPException(403, detail="authz.entrance_scope")
    if not erp_shared_express_endpoint_enabled_for(user.get("tenant_id")):
        from fastapi import HTTPException

        raise HTTPException(404, detail="erp.shared_endpoint_unavailable")
    if req is not None and req.expected_generation != 0:
        from fastapi import HTTPException

        raise HTTPException(409, detail="erp.endpoint_generation_conflict")
    workspace_id = _workspace_header(request)
    client = request.client
    return enroll_legacy_express_endpoint(
        user=user,
        endpoint_id=endpoint_id,
        workspace_client_id=workspace_id,
        request_ip=client.host if client else None,
        request_ua=request.headers.get("user-agent"),
    )
