# -*- coding: utf-8 -*-
"""Read-only web contract for the current ERP target projection."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, Request

from core.feature_flags import erp_target_projection_enabled_for
from services.auth.entrance import require_erp_portal
from services.authz.deps import require_perm
from services.erp import team_access
from services.erp.target_projection_contract import ProjectionContractError
from services.erp.target_projection_store import load_state
from services.erp.mrerp_target_projection import (
    MRErpProjectionError,
    refresh_mrerp_projection,
)

router = APIRouter()


def _parse_entities(raw: str) -> tuple[str, ...]:
    return tuple(value.strip().lower() for value in raw.split(",") if value.strip())


def _resolve_endpoint(user: dict, endpoint_id: str) -> dict | None:
    assigned = team_access.assigned_endpoint_for_request(user, endpoint_id)
    if assigned is not None:
        return assigned
    from core import db

    endpoint = db.get_erp_endpoint(str(user.get("id") or ""), endpoint_id)
    return endpoint if endpoint and endpoint.get("enabled") else None


def _endpoint_visible(user: dict, endpoint_id: str) -> bool:
    return _resolve_endpoint(user, endpoint_id) is not None


def _read_projection(
    user: dict, endpoint_id: str, account_set_key: str | None, entity_types: str
) -> dict:
    require_erp_portal(user)
    if not erp_target_projection_enabled_for(user.get("tenant_id"), user.get("id")):
        raise HTTPException(404, detail="erp.target_projection_unavailable")
    if not _endpoint_visible(user, endpoint_id):
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


def _refresh_projection(user: dict, endpoint_id: str, account_set_key: str | None) -> dict:
    require_erp_portal(user)
    if not erp_target_projection_enabled_for(user.get("tenant_id"), user.get("id")):
        raise HTTPException(404, detail="erp.target_projection_unavailable")
    endpoint = _resolve_endpoint(user, endpoint_id)
    if endpoint is None:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    try:
        return refresh_mrerp_projection(
            tenant_id=str(user["tenant_id"]),
            user_id=str(user["id"]),
            endpoint=endpoint,
            account_set_key=account_set_key,
        )
    except MRErpProjectionError as exc:
        status = 404 if exc.code == "erp.endpoint_not_found" else 400
        raise HTTPException(status, detail=exc.code) from exc


@router.get("/api/erp/endpoints/{endpoint_id}/target-projection")
async def erp_target_projection(
    endpoint_id: str,
    request: Request,
    account_set_key: str | None = Query(default=None, max_length=500),
    entity_types: str = Query(default="", max_length=200),
):
    user = await asyncio.to_thread(lambda: require_perm(request, "erp.endpoint.view"))
    return await asyncio.to_thread(
        _read_projection, user, endpoint_id, account_set_key, entity_types
    )


@router.post("/api/erp/endpoints/{endpoint_id}/target-projection/refresh")
async def refresh_erp_target_projection(
    endpoint_id: str,
    request: Request,
    account_set_key: str | None = Query(default=None, max_length=500),
):
    user = await asyncio.to_thread(lambda: require_perm(request, "erp.endpoint.view"))
    return await asyncio.to_thread(_refresh_projection, user, endpoint_id, account_set_key)


__all__ = ["erp_target_projection", "refresh_erp_target_projection", "router"]
