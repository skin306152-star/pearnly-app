# -*- coding: utf-8 -*-
"""Authenticated browser editor for one pending LINE DMS booking."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core import db
from core.auth import create_access_token
from core.pos_api import PosError, ok
from routes.line_liff_routes import LiffAuthIn, _verify_id_token

router = APIRouter(tags=["line-dms-booking-edit"])
_ROOT = Path(__file__).resolve().parent.parent


class DmsBookingSaveIn(BaseModel):
    nonce: str = ""
    form: Dict[str, Any] = Field(default_factory=dict)


@router.get("/login/dms-booking")
@router.get("/liff/dms-booking")
async def liff_dms_booking_entry():
    """Public shell; draft data still requires a DMS JWT and one-time nonce."""
    return FileResponse(
        _ROOT / "static" / "dist" / "dms-booking-edit.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/api/line/dms-booking/config")
async def dms_booking_liff_config():
    liff_id = os.getenv("LINE_DMS_LIFF_ID", "").strip() or os.getenv("LINE_LIFF_ID", "").strip()
    return ok({"liff_id": liff_id})


@router.post("/api/line/dms-booking/auth")
async def dms_booking_liff_auth(req: LiffAuthIn):
    """Exchange a DMS-channel LIFF identity for a DMS-scoped session."""
    from services.line_dms import store

    claims = await asyncio.to_thread(_verify_id_token, req.id_token, "LINE_DMS_LIFF_ID")
    binding = await asyncio.to_thread(store.get_binding_by_line_user, (claims or {}).get("sub"))
    if not binding:
        raise PosError("dms_booking.not_bound", 403, detail="line_not_bound")
    user = await asyncio.to_thread(db.find_user_by_id, str(binding["user_id"]))
    if not user or not user.get("is_active", True):
        raise PosError("dms_booking.not_bound", 403, detail="line_not_bound")
    token = await asyncio.to_thread(
        create_access_token,
        user_id=str(user["id"]),
        username=user.get("username") or "",
        plan=user.get("plan") or "free",
        tenant_id=str(user.get("tenant_id") or "") or None,
        role=user.get("role") or "owner",
        entry="dms",
    )
    return ok({"token": token})


async def _authorize(request: Request) -> dict:
    from routes.dms_routes import _authorize as authorize_dms

    return await asyncio.to_thread(authorize_dms, request)


def _booking_error(exc):
    from services.line_dms.booking_edit import BookingEditError

    if isinstance(exc, BookingEditError):
        raise PosError(exc.code, exc.status, detail=exc.code) from exc
    raise exc


@router.get("/api/line/dms-booking/draft")
async def dms_booking_draft(request: Request, nonce: str):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        return ok(await asyncio.to_thread(booking_edit.load, user, nonce))
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)


@router.get("/api/line/dms-booking/paints")
async def dms_booking_paints(request: Request, nonce: str, car_id: str):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        return ok(await asyncio.to_thread(booking_edit.paints, user, nonce, car_id))
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)


@router.get("/api/line/dms-booking/geo")
async def dms_booking_geo(request: Request, nonce: str, level: str, parent_id: str = ""):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        return ok(await asyncio.to_thread(booking_edit.geo, user, nonce, level, parent_id))
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)


@router.post("/api/line/dms-booking/draft")
async def dms_booking_save(request: Request, req: DmsBookingSaveIn):
    from services.line_dms import booking_edit

    user = await _authorize(request)
    try:
        next_nonce = await asyncio.to_thread(booking_edit.save, user, req.nonce, req.form)
        return ok({"nonce": next_nonce})
    except booking_edit.BookingEditError as exc:
        _booking_error(exc)
