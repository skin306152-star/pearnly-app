"""Owner confirmation boundary for a managed Express live Profile."""

from __future__ import annotations

import asyncio
from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from services.auth.entrance import require_erp_portal
from services.authz.deps import require_perm
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for

router = APIRouter()


class ConfirmManagedProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_generation: int = Field(..., ge=1)
    confirm: bool


def _source_workspace(request: Request) -> int:
    raw = request.headers.get("X-Workspace-Client-Id")
    if raw is None or not raw.strip().isdigit() or int(raw.strip()) <= 0:
        raise HTTPException(400, detail="workspace.required")
    return int(raw.strip())


def _run_confirm(request: Request, endpoint_id: str, req: ConfirmManagedProfileRequest):
    user = require_perm(request, "erp.endpoint.manage")
    require_erp_portal(user)
    if user.get("is_super_admin") or user.get("entry") not in {"main", "cowork", "erp"}:
        raise HTTPException(403, detail="authz.entrance_scope")
    source_workspace_id = _source_workspace(request)
    if not erp_shared_express_endpoint_enabled_for(user.get("tenant_id")):
        raise HTTPException(404, detail="erp.shared_endpoint_unavailable")
    if not req.confirm:
        raise HTTPException(400, detail="erp.profile_confirmation_required")
    from services.erp.shared_express_live import ManagedLiveError, confirm_managed_live_profile

    client = request.client
    try:
        return confirm_managed_live_profile(
            user=user,
            endpoint_id=endpoint_id,
            source_workspace_id=source_workspace_id,
            expected_generation=req.expected_generation,
            confirm=req.confirm,
            request_ip=client.host if client else None,
            request_ua=request.headers.get("user-agent"),
        )
    except ManagedLiveError as exc:
        raise HTTPException(
            status_code=int(getattr(exc, "status", getattr(exc, "status_code", 500))),
            detail=str(getattr(exc, "code", "erp.managed_live_error")),
        ) from exc


@router.post("/api/erp/endpoints/{endpoint_id}/shared/profile/confirm")
async def confirm_managed_profile(
    endpoint_id: str, request: Request, req: ConfirmManagedProfileRequest = Body(...)
):
    return await asyncio.to_thread(_run_confirm, request, endpoint_id, req)


__all__ = ["ConfirmManagedProfileRequest", "confirm_managed_profile", "router"]
