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
from services.line_dms import login_tickets, mrerp_portal

router = APIRouter(tags=["line-dms-portal"])


async def _authorize(request: Request) -> dict:
    from routes.dms_routes import _authorize as authorize_dms

    return await asyncio.to_thread(authorize_dms, request)


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
    issued = await asyncio.to_thread(login_tickets.issue_login_ticket, tenant_id, user_id)
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

    try:
        username, password = await asyncio.to_thread(
            mrerp_portal.load_credentials, str(identity["user_id"])
        )
    except mrerp_portal.PortalCredentialsMissing:
        return _error_page("ยังไม่ได้ตั้งค่าบัญชี DMS ใน Pearnly", 409)
    except mrerp_portal.PortalUnavailable:
        return _error_page("ไม่สามารถเข้าสู่ DMS ได้ในขณะนี้ กรุณาลองใหม่", 503)

    content, nonce = mrerp_portal.render_login_relay(username, password)
    return HTMLResponse(content, headers=mrerp_portal.security_headers(nonce))
