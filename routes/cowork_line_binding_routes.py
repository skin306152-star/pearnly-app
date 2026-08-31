"""Authenticated Cowork LINE self-service connection endpoints."""

from __future__ import annotations

import asyncio
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user_from_request
from core.route_helpers import _log_op
from services.cowork_line.identity_store import (
    CoworkLineIdentityError,
    get_identity_status,
    issue_connect_token,
    unbind_identity,
)

router = APIRouter()


def _identity_args(user: dict) -> dict[str, str]:
    if user.get("entry") == "erp" or user.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="cowork_line.membership_inactive")
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="cowork_line.membership_inactive")
    return {"user_id": str(user["id"]), "tenant_id": str(tenant_id)}


def _http_error(exc: CoworkLineIdentityError) -> HTTPException:
    status_code = {
        "membership_inactive": 403,
        "already_connected": 409,
        "line_conflict": 409,
        "token_expired": 410,
        "invalid_line_user": 422,
    }.get(exc.code, 400)
    return HTTPException(status_code=status_code, detail=f"cowork_line.{exc.code}")


@router.get("/api/cowork-line/identity")
async def cowork_line_identity(request: Request):
    user = get_current_user_from_request(request)
    try:
        return await asyncio.to_thread(get_identity_status, **_identity_args(user))
    except CoworkLineIdentityError as exc:
        raise _http_error(exc) from exc


@router.post("/api/cowork-line/connect/start")
async def cowork_line_connect_start(request: Request):
    user = get_current_user_from_request(request)
    try:
        issued = await asyncio.to_thread(issue_connect_token, **_identity_args(user))
    except CoworkLineIdentityError as exc:
        raise _http_error(exc) from exc
    url = "/api/auth/line/start?entry=cowork&connect_token=" + quote(issued["token"], safe="")
    await asyncio.to_thread(
        _log_op,
        request,
        user,
        "cowork.line.connect_start",
        "user",
        str(user["id"]),
        None,
        {"expires_at": issued["expires_at"]},
    )
    return {"url": url}


@router.delete("/api/cowork-line/identity")
async def cowork_line_unbind(request: Request):
    user = get_current_user_from_request(request)
    try:
        disconnected = await asyncio.to_thread(unbind_identity, **_identity_args(user))
    except CoworkLineIdentityError as exc:
        raise _http_error(exc) from exc
    if disconnected:
        await asyncio.to_thread(
            _log_op,
            request,
            user,
            "cowork.line.unbind",
            "user",
            str(user["id"]),
            None,
            {},
        )
    return {"connected": False}
