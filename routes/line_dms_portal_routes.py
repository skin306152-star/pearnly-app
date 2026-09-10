# -*- coding: utf-8 -*-
"""Short-lived LINE-to-MR.ERP login relay for the DMS channel."""

from __future__ import annotations

import asyncio
import html
import secrets
import urllib.parse

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core import db
from core.pos_api import PosError, ok
from services.line_dms import binding_guard, login_tickets, mrerp_portal

router = APIRouter(tags=["line-dms-portal"])


async def _authorize(request: Request) -> dict:
    from routes.dms_routes import _authorize as authorize_dms

    from services.line_dms import binding_guard

    user = await asyncio.to_thread(authorize_dms, request)
    return await asyncio.to_thread(binding_guard.authorize_browser, request, user)


def _error_page(message: str, status_code: int) -> HTMLResponse:
    nonce = secrets.token_urlsafe(18)
    content = (
        '<!doctype html><html lang="th"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="referrer" content="no-referrer"><title>DMS</title></head>'
        f"<body><main><h1>DMS</h1><p>{html.escape(message)}</p>"
        f'<p><a href="{mrerp_portal.MRERP_ROOT_URL}" rel="noreferrer">เปิด DMS</a></p>'
        "</main></body></html>"
    )
    return HTMLResponse(
        content,
        status_code=status_code,
        headers=mrerp_portal.security_headers(nonce),
    )


@router.post("/api/line/dms-portal/ticket")
async def issue_mrerp_login_ticket(request: Request):
    user = await _authorize(request)
    tenant_id = str(user.get("tenant_id") or "").strip()
    user_id = str(user.get("id") or "").strip()
    if not tenant_id or not user_id:
        raise PosError("dms_portal.identity_missing", 403)
    issued = await asyncio.to_thread(
        binding_guard.browser_call, user, login_tickets.issue_login_ticket, tenant_id, user_id
    )
    if not issued:
        raise PosError("dms_portal.unavailable", 503)
    ticket = urllib.parse.quote(issued["ticket"], safe="")
    return ok(
        {
            "url": f"/home/dms-booking/portal?ticket={ticket}",
            "expires_at": issued["expires_at"],
        }
    )


@router.get("/home/dms-booking/portal")
async def consume_mrerp_login_ticket(ticket: str = ""):
    identity = await asyncio.to_thread(login_tickets.consume_login_ticket, ticket)
    if not identity:
        return _error_page("ลิงก์หมดอายุหรือถูกใช้งานแล้ว กรุณาเปิดเมนูใหม่", 410)

    user = await asyncio.to_thread(db.find_user_by_id, str(identity["user_id"]))
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id") or "") != str(identity["tenant_id"])
    ):
        return _error_page("ไม่สามารถยืนยันผู้ใช้งานได้ กรุณาเปิดเมนูใหม่", 410)

    from services.line_dms import store
    from services.line_platform import channels as line_channels

    binding = await asyncio.to_thread(store.get_binding_by_user, str(identity["user_id"]))
    if binding:
        binding = {**binding, "user_id": str(identity["user_id"])}
    ticket_channel = line_channels.normalize(identity.get("channel_key"))
    ticket_epoch = identity.get("binding_id")
    if (
        not binding
        or not identity.get("created_at")
        or binding["channel_key"] != ticket_channel
        or (ticket_epoch is not None and str(binding["id"]) != str(ticket_epoch))
        # Legacy tickets (issued before the epoch column) are only valid on the legacy OA and
        # fall back to the bound_at timestamp check; they can never authorize an A/B binding.
        or (ticket_epoch is None and binding["channel_key"] != line_channels.DEFAULT_DMS_CHANNEL)
        or binding["bound_at"] > identity["created_at"]
        or not await asyncio.to_thread(binding_guard.current, binding)
    ):
        return _error_page("ลิงก์หมดอายุ กรุณาเปิดเมนูใหม่", 410)

    try:
        username, password = await asyncio.to_thread(
            mrerp_portal.load_credentials, str(identity["user_id"])
        )
    except mrerp_portal.PortalCredentialsMissing:
        return _error_page("ยังไม่ได้ตั้งค่าบัญชี DMS ใน Pearnly", 409)
    except mrerp_portal.PortalUnavailable:
        return _error_page("ไม่สามารถเข้าสู่ DMS ได้ในขณะนี้ กรุณาลองใหม่", 503)

    if not await asyncio.to_thread(binding_guard.current, binding):
        return _error_page("ลิงก์หมดอายุ กรุณาเปิดเมนูใหม่", 410)

    content, nonce = mrerp_portal.render_login_relay(username, password)
    return HTMLResponse(content, headers=mrerp_portal.security_headers(nonce))
