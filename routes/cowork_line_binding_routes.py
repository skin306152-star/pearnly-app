"""Authenticated Cowork LINE self-service connection endpoints."""

from __future__ import annotations

import asyncio
import os

from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user_from_request
from core.route_helpers import _log_op
from services.cowork_line.identity_store import (
    CoworkLineIdentityError,
    get_identity_status,
    issue_binding_code,
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
        "code_unavailable": 503,
    }.get(exc.code, 400)
    return HTTPException(status_code=status_code, detail=f"cowork_line.{exc.code}")


@router.get("/api/cowork-line/identity")
async def cowork_line_identity(request: Request):
    user = get_current_user_from_request(request)
    try:
        return await asyncio.to_thread(get_identity_status, **_identity_args(user))
    except CoworkLineIdentityError as exc:
        raise _http_error(exc) from exc


@router.post("/api/cowork-line/binding-code")
async def cowork_line_binding_code(request: Request):
    user = get_current_user_from_request(request)
    try:
        issued = await asyncio.to_thread(issue_binding_code, **_identity_args(user))
    except CoworkLineIdentityError as exc:
        raise _http_error(exc) from exc
    await asyncio.to_thread(
        _log_op,
        request,
        user,
        "cowork.line.binding_code",
        "user",
        str(user["id"]),
        None,
        {"expires_at": issued["expires_at"]},
    )
    return {
        **issued,
        "bot_friend_url": os.environ.get("LINE_BOT_FRIEND_URL")
        or "https://line.me/R/ti/p/@pearnly",
        "bot_basic_id": os.environ.get("LINE_BOT_BASIC_ID") or "@pearnly",
    }


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


from pydantic import BaseModel, Field
from fastapi.responses import FileResponse


class WorkConnectRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=10000)


class WorkInviteRequest(WorkConnectRequest):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{16,64}$")
    account: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(min_length=1, max_length=100)
    board: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")


@router.get("/liff/cowork-connect", include_in_schema=False)
def cowork_connect_page():
    return FileResponse("static/dist/cowork-connect.html", headers={"Cache-Control": "no-store"})


@router.post("/api/cowork-line/connect")
async def cowork_connect(body: WorkConnectRequest, request: Request):
    from services.cowork_line.work_invites import connect

    user = get_current_user_from_request(request)
    try:
        result = await asyncio.to_thread(connect, **_identity_args(user), token=body.id_token)
    except CoworkLineIdentityError as exc:
        raise _http_error(exc) from exc
    await asyncio.to_thread(
        _log_op, request, user, "cowork.line.connect", "user", str(user["id"]), None, {}
    )
    return result


@router.post("/api/cowork-line/work-invite")
async def cowork_work_invite(body: WorkInviteRequest):
    from services.cowork_line.work_invites import invite

    try:
        return await asyncio.to_thread(
            invite,
            body.id_token,
            body.request_id,
            body.account,
            body.password,
            body.display_name,
            body.board,
        )
    except ValueError as exc:
        raise HTTPException(422, "work.account_invalid") from exc


class WorkLiveRead(BaseModel):
    token: str = Field(min_length=1, max_length=10000)
    board: str = Field(default="", pattern=r"^[A-Za-z0-9_-]{0,100}$")


@router.post("/api/cowork-line/work-live/auth")
async def cowork_live_auth(body: WorkConnectRequest):
    from services.cowork_line import work_live
    from fastapi.responses import JSONResponse

    return JSONResponse(
        await asyncio.to_thread(work_live.authenticate, body.id_token),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/api/cowork-line/work-live/read")
async def cowork_live_read(body: WorkLiveRead):
    from services.cowork_line import work_live
    from fastapi.responses import JSONResponse

    return JSONResponse(
        await asyncio.to_thread(work_live.read, body.token, body.board),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/liff/cowork-live", include_in_schema=False)
def cowork_live_page():
    return FileResponse("static/dist/cowork-live.html", headers={"Cache-Control": "no-store"})
