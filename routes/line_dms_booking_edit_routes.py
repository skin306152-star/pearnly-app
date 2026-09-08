# -*- coding: utf-8 -*-
"""Authenticated browser editor for one pending LINE DMS booking."""

from __future__ import annotations

from services.line_dms.binding_guard import browser_call

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core import db
from core.auth import create_access_token
from core.pos_api import PosError, ok
from services.line_platform.liff import verify_id_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["line-dms-booking-edit"])
_ROOT = Path(__file__).resolve().parent.parent


class LiffAuthIn(BaseModel):
    id_token: str = ""
    channel: str = ""


class DmsBookingSaveIn(BaseModel):
    nonce: str = ""
    form: Dict[str, Any] = Field(default_factory=dict)


@router.get("/home/dms-booking")
@router.get("/login/dms-booking")
@router.get("/liff/dms-booking")
async def liff_dms_booking_entry():
    """Public shell; draft data still requires a DMS JWT and one-time nonce."""
    return FileResponse(
        _ROOT / "static" / "dist" / "dms-booking-edit.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/api/line/dms-booking/config")
async def dms_booking_liff_config(channel: str = ""):
    """Resolve the LIFF app of the OA that owns this browser entry.

    Unknown non-empty channel → 404; A/B without its own LIFF id returns an empty id so the page
    degrades honestly instead of silently opening the legacy OA's LIFF.
    """
    from services.line_platform import channels

    raw = (channel or "").strip()
    if raw and not channels.is_valid(raw):
        raise PosError("dms_booking.liff_unavailable", 404, detail="unknown_channel")
    key = raw or channels.DEFAULT_DMS_CHANNEL
    liff_id = channels.liff_id(key)
    return ok({"liff_id": liff_id, "channel_key": key, "available": bool(liff_id)})


@router.post("/api/line/dms-booking/auth")
async def dms_booking_liff_auth(req: LiffAuthIn):
    """Exchange a LIFF identity for a session scoped to the same OA's binding."""
    from services.line_dms import store
    from services.line_platform import channels

    raw = (req.channel or "").strip()
    if raw and not channels.is_valid(raw):
        logger.warning("DMS browser authentication rejected: unknown_channel")
        raise PosError("dms_booking.liff_unavailable", 403, detail="unknown_channel")
    key = raw or channels.DEFAULT_DMS_CHANNEL
    claims = await asyncio.to_thread(verify_id_token, req.id_token, channels.liff_env_name(key))
    if not claims or not claims.get("sub"):
        logger.warning("DMS browser authentication rejected: line_token_invalid")
        raise PosError("dms_booking.line_auth_required", 401, detail="line_token_invalid")
    binding = await asyncio.to_thread(store.get_binding_by_line_user, claims["sub"], key)
    if not binding or str(binding.get("channel_key") or "") != key:
        logger.warning("DMS browser authentication rejected: line_not_bound")
        raise PosError("dms_booking.not_bound", 403, detail="line_not_bound")
    user = await asyncio.to_thread(db.find_user_by_id, str(binding["user_id"]))
    if not user or not user.get("is_active", True):
        raise PosError("dms_booking.not_bound", 403, detail="line_not_bound")
    from services.line_dms import binding_guard

    if not await asyncio.to_thread(binding_guard.current, binding):
        raise PosError("dms_booking.not_bound", 403, detail="line_not_bound")
    token = await asyncio.to_thread(
        create_access_token,
        user_id=str(user["id"]),
        username=user.get("username") or "",
        plan=user.get("plan") or "free",
        tenant_id=str(user.get("tenant_id") or "") or None,
        role=user.get("role") or "owner",
        entry="dms",
        dms_binding=binding,
    )
    return ok({"token": token})


async def _authorize(request: Request) -> dict:
    from routes.dms_routes import _authorize as authorize_dms

    from services.line_dms import binding_guard

    user = await asyncio.to_thread(authorize_dms, request)
    return await asyncio.to_thread(binding_guard.authorize_browser, request, user)


def _booking_error(exc):
    from services.line_dms.booking_edit import BookingEditError

    if isinstance(exc, BookingEditError):
        logger.warning("dms booking edit failed: code=%s status=%s", exc.code, exc.status)
        raise PosError(exc.code, exc.status, detail=exc.code) from exc
    raise exc


@router.get("/api/line/dms-booking/draft")
async def dms_booking_draft(request: Request, nonce: str):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        return ok(await asyncio.to_thread(browser_call, user, booking_edit.load, user, nonce))
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)


@router.get("/api/line/dms-booking/paints")
async def dms_booking_paints(request: Request, nonce: str, car_id: str):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        return ok(
            await asyncio.to_thread(browser_call, user, booking_edit.paints, user, nonce, car_id)
        )
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)


@router.get("/api/line/dms-booking/geo")
async def dms_booking_geo(request: Request, nonce: str, level: str, parent_id: str = ""):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        return ok(
            await asyncio.to_thread(
                browser_call, user, booking_edit.geo, user, nonce, level, parent_id
            )
        )
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)


@router.post("/api/line/dms-booking/draft")
async def dms_booking_save(request: Request, req: DmsBookingSaveIn):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        next_nonce = await asyncio.to_thread(
            browser_call, user, booking_edit.save, user, req.nonce, req.form
        )
        return ok({"nonce": next_nonce})
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)
