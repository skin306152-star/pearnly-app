# -*- coding: utf-8 -*-
"""Owner-only managed Express endpoint lifecycle HTTP boundary."""

from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.auth import get_current_user_from_request
from services.authz.deps import require_perm
from services.auth.entrance import require_erp_portal
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for
from services.erp.shared_express_lifecycle import change_shared_express_endpoint

router = APIRouter()


def _reject_controls(value: str) -> str:
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("reason must not contain control characters")
    return value


class _BaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    expected_generation: int = Field(..., ge=1)
    reason: str = Field(default="", max_length=200)

    _reason_safe = field_validator("reason")(_reject_controls)


class RebindRequest(_BaseRequest):
    target_workspace_client_id: int = Field(..., gt=0)
    confirm_target_workspace_client_id: int = Field(..., gt=0)


class EnableRequest(_BaseRequest):
    pass


class DisableRequest(_BaseRequest):
    pass


class RevokeRequest(_BaseRequest):
    confirm: bool = False


def _source_workspace(request: Request) -> int:
    raw = request.headers.get("X-Workspace-Client-Id")
    if raw is None or not raw.strip().isdigit() or int(raw.strip()) <= 0:
        raise HTTPException(400, detail="workspace.required")
    return int(raw.strip())


def _guard(request: Request, user=None):
    user = user or get_current_user_from_request(request)
    require_erp_portal(user)
    if user.get("is_super_admin") or user.get("entry") not in {"main", "cowork", "erp"}:
        raise HTTPException(403, detail="authz.entrance_scope")
    if not erp_shared_express_endpoint_enabled_for(user.get("tenant_id")):
        raise HTTPException(404, detail="erp.shared_endpoint_unavailable")
    return user, _source_workspace(request)


def _run(request: Request, endpoint_id: str, action: str, req: _BaseRequest, user):
    user, source = _guard(request, user)
    target = getattr(req, "target_workspace_client_id", None)
    if action == "rebind" and target != req.confirm_target_workspace_client_id:
        raise HTTPException(400, detail="erp.target_workspace_confirmation_mismatch")
    confirm = bool(getattr(req, "confirm", False))
    if action == "revoke" and not confirm:
        raise HTTPException(400, detail="erp.revoke_confirmation_required")
    client = request.client
    return change_shared_express_endpoint(
        user=user,
        endpoint_id=endpoint_id,
        action=action,
        operation_id=str(req.operation_id),
        expected_generation=req.expected_generation,
        source_workspace_id=source,
        target_workspace_id=target,
        reason=req.reason,
        confirm=confirm,
        request_ip=client.host if client else None,
        request_ua=request.headers.get("user-agent"),
    )


@router.post("/api/erp/endpoints/{endpoint_id}/shared/rebind")
async def rebind_shared_express_endpoint(
    endpoint_id: str, request: Request, req: RebindRequest = Body(...)
):
    user = require_perm(request, "erp.endpoint.manage")
    return await asyncio.to_thread(_run, request, endpoint_id, "rebind", req, user)


@router.post("/api/erp/endpoints/{endpoint_id}/shared/enable")
async def enable_shared_express_endpoint(
    endpoint_id: str, request: Request, req: EnableRequest = Body(...)
):
    user = require_perm(request, "erp.endpoint.manage")
    return await asyncio.to_thread(_run, request, endpoint_id, "enable", req, user)


@router.post("/api/erp/endpoints/{endpoint_id}/shared/disable")
async def disable_shared_express_endpoint(
    endpoint_id: str, request: Request, req: DisableRequest = Body(...)
):
    user = require_perm(request, "erp.endpoint.manage")
    return await asyncio.to_thread(_run, request, endpoint_id, "disable", req, user)


@router.post("/api/erp/endpoints/{endpoint_id}/shared/revoke")
async def revoke_shared_express_endpoint(
    endpoint_id: str, request: Request, req: RevokeRequest = Body(...)
):
    user = require_perm(request, "erp.endpoint.manage")
    return await asyncio.to_thread(_run, request, endpoint_id, "revoke", req, user)
