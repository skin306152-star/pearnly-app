"""Universal COWORK entry and authenticated service-to-service handoff."""

from __future__ import annotations

import hmac
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.auth import decode_access_token, get_current_user_from_request
from services.work_bridge import accounts, sessions
from services.work_bridge.config import service
from services.security.headers import _ENFORCE_CSP, _REPORT_CSP

router = APIRouter(tags=["work-collaboration"])


class TicketRequest(BaseModel):
    state: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")


class ConsumeRequest(TicketRequest):
    ticket: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")


class SessionRequest(BaseModel):
    session: str = Field(pattern=r"^[a-f0-9]{64}$")


class MemberRequest(BaseModel):
    actor_id: UUID
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{10,64}$")
    account: str = Field(min_length=3, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, min_length=6, max_length=100)
    display_name: str = Field(default="", max_length=200)


class LookupRequest(BaseModel):
    account: str = Field(min_length=3, max_length=200)


class EnrollmentRequest(BaseModel):
    actor_id: UUID
    user_id: UUID


def require_service(request: Request) -> None:
    supplied = request.headers.get("Authorization", "")
    if not hmac.compare_digest(supplied.encode(), ("Bearer " + service().secret).encode()):
        raise HTTPException(401, "work.service_unauthorized")


def cowork_user(request: Request) -> dict:
    user = get_current_user_from_request(request)
    if user.get("entry", "main") not in ("main", "cowork"):
        raise HTTPException(403, "authz.entrance_scope")
    return user


@router.get("/work", include_in_schema=False)
def work_page():
    try:
        form_action = "form-action 'self' " + service().url
    except HTTPException:
        form_action = "form-action 'self'"
    return FileResponse(
        "static/dist/work.html",
        headers={
            "Cache-Control": "no-store",
            # A no-referrer navigation POST carries Origin: null. Share only
            # the fixed origin so the gateway can check this browser handoff.
            "Referrer-Policy": "strict-origin",
            "Content-Security-Policy": _ENFORCE_CSP + "; " + form_action,
            "Content-Security-Policy-Report-Only": _REPORT_CSP.replace(
                "form-action 'self'", form_action
            ),
        },
    )


@router.get("/api/work/entry")
def work_entry(request: Request):
    cowork_user(request)
    return {"url": service().url + "/_pearnly/start"}


@router.post("/api/work/tickets")
def work_ticket(body: TicketRequest, request: Request):
    user = cowork_user(request)
    claims = decode_access_token(request.headers["Authorization"][7:].strip())
    return sessions.issue(user, claims or {}, body.state)


@router.post("/api/work/service/consume", include_in_schema=False)
def work_consume(body: ConsumeRequest, request: Request):
    require_service(request)
    return sessions.consume(body.ticket, body.state)


@router.post("/api/work/service/session", include_in_schema=False)
def work_session(body: SessionRequest, request: Request):
    require_service(request)
    return sessions.validate(body.session)


@router.post("/api/work/service/revoke", include_in_schema=False)
def work_revoke(body: SessionRequest, request: Request):
    require_service(request)
    sessions.revoke(body.session)
    return {"ok": True}


@router.post("/api/work/service/members", include_in_schema=False)
def work_member(body: MemberRequest, request: Request):
    require_service(request)
    values = body.model_dump()
    values["actor_id"] = str(body.actor_id)
    try:
        return accounts.create_member(**values)
    except ValueError:
        raise HTTPException(422, "work.account_invalid") from None


@router.post("/api/work/service/lookup", include_in_schema=False)
def work_lookup(body: LookupRequest, request: Request):
    require_service(request)
    try:
        return accounts.lookup(body.account)
    except ValueError:
        raise HTTPException(422, "work.account_invalid") from None


@router.post("/api/work/service/enroll", include_in_schema=False)
def work_enroll(body: EnrollmentRequest, request: Request):
    require_service(request)
    return accounts.enroll(str(body.actor_id), str(body.user_id))
