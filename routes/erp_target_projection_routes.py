# -*- coding: utf-8 -*-
"""Read-only web contract for the current ERP target projection."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, Request

from core.feature_flags import erp_target_projection_enabled_for
from services.auth.entrance import require_erp_portal
from services.authz.deps import require_perm
from services.erp import line_target_projection, shared_express_access, target_refresh, team_access
from services.erp.target_projection_contract import ProjectionContractError
from services.erp.target_projection_store import load_state

router = APIRouter()


def _parse_entities(raw: str) -> tuple[str, ...]:
    return tuple(value.strip().lower() for value in raw.split(",") if value.strip())


def _resolve_endpoint(user: dict, endpoint_id: str, request: Request | None = None) -> dict | None:
    assigned = team_access.assigned_endpoint_for_request(user, endpoint_id)
    if assigned is not None:
        return assigned
    if request is not None and shared_express_access.is_shared_endpoint_read(user):
        visible = shared_express_access.visible_endpoint_for_request(
            request,
            user,
            endpoint_id,
        )
        if visible is not None and visible.get("enabled") is True:
            return visible
    from core import db

    endpoint = db.get_erp_endpoint(str(user.get("id") or ""), endpoint_id)
    return endpoint if endpoint and endpoint.get("enabled") else None


def _endpoint_visible(user: dict, endpoint_id: str, request: Request | None = None) -> bool:
    return _resolve_endpoint(user, endpoint_id, request) is not None


def _read_projection(
    user: dict,
    endpoint_id: str,
    account_set_key: str | None,
    entity_types: str,
    request: Request | None = None,
) -> dict:
    require_erp_portal(user)
    if not erp_target_projection_enabled_for(user.get("tenant_id"), user.get("id")):
        raise HTTPException(404, detail="erp.target_projection_unavailable")
    if not _endpoint_visible(user, endpoint_id, request):
        raise HTTPException(404, detail="erp.endpoint_not_found")
    try:
        state = load_state(
            tenant_id=str(user["tenant_id"]),
            user_id=str(user["id"]),
            endpoint_id=endpoint_id,
            account_set_key=account_set_key,
            entity_types=_parse_entities(entity_types),
        )
    except ProjectionContractError as exc:
        raise HTTPException(400, detail=exc.code) from exc
    if state is None:
        raise HTTPException(404, detail="erp.target_projection_missing")
    return {"ok": True, "data": state}


def _refresh_projection(
    user: dict,
    endpoint_id: str,
    account_set_key: str | None,
    request: Request | None = None,
) -> dict:
    require_erp_portal(user)
    if not erp_target_projection_enabled_for(user.get("tenant_id"), user.get("id")):
        raise HTTPException(404, detail="erp.target_projection_unavailable")
    endpoint = _resolve_endpoint(user, endpoint_id, request)
    if endpoint is None:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    version = endpoint.get("agent_version") or config.get("companion_version")
    if adapter == "express" and not line_target_projection.supports_master_refresh(version):
        raise HTTPException(409, detail="erp.companion_update_required")
    try:
        refresh = target_refresh.request_refresh(
            tenant_id=str(user["tenant_id"]),
            user_id=str(user["id"]),
            endpoint_id=endpoint_id,
            account_set_key=account_set_key or target_refresh.ENDPOINT_SCOPE_KEY,
            adapter=adapter,
            reason="web_target_projection",
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    return {"ok": True, "refresh": refresh, "adapter": adapter}


def _refresh_status(
    user: dict,
    endpoint_id: str,
    request_id: str,
    request: Request | None = None,
) -> dict:
    require_erp_portal(user)
    if not erp_target_projection_enabled_for(user.get("tenant_id"), user.get("id")):
        raise HTTPException(404, detail="erp.target_projection_unavailable")
    if not _endpoint_visible(user, endpoint_id, request):
        raise HTTPException(404, detail="erp.endpoint_not_found")
    status = target_refresh.refresh_status(
        request_id,
        tenant_id=str(user["tenant_id"]),
        endpoint_id=endpoint_id,
    )
    if status is None:
        raise HTTPException(404, detail="erp.target_refresh_missing")
    return {"ok": True, "refresh": status}


@router.get("/api/erp/endpoints/{endpoint_id}/target-projection")
async def erp_target_projection(
    endpoint_id: str,
    request: Request,
    account_set_key: str | None = Query(default=None, max_length=500),
    entity_types: str = Query(default="", max_length=200),
):
    user = await asyncio.to_thread(lambda: require_perm(request, "erp.endpoint.view"))
    return await asyncio.to_thread(
        _read_projection, user, endpoint_id, account_set_key, entity_types, request
    )


@router.post("/api/erp/endpoints/{endpoint_id}/target-projection/refresh")
async def refresh_erp_target_projection(
    endpoint_id: str,
    request: Request,
    account_set_key: str | None = Query(default=None, max_length=500),
):
    user = await asyncio.to_thread(lambda: require_perm(request, "erp.endpoint.view"))
    result = await asyncio.to_thread(
        _refresh_projection, user, endpoint_id, account_set_key, request
    )
    adapter = result.pop("adapter")
    if adapter == "mrerp":
        asyncio.create_task(
            asyncio.to_thread(
                target_refresh.process_mrerp_request,
                result["refresh"]["request_id"],
            )
        )
    return result


@router.get("/api/erp/endpoints/{endpoint_id}/target-projection/refresh/{request_id}")
async def erp_target_projection_refresh_status(
    endpoint_id: str,
    request_id: str,
    request: Request,
):
    user = await asyncio.to_thread(lambda: require_perm(request, "erp.endpoint.view"))
    return await asyncio.to_thread(_refresh_status, user, endpoint_id, request_id, request)


__all__ = [
    "erp_target_projection",
    "erp_target_projection_refresh_status",
    "refresh_erp_target_projection",
    "router",
]
