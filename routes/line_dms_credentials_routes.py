# -*- coding: utf-8 -*-
"""Self-service DMS credential API for a LINE-bound operator."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.feature_flags import dms_line_enabled_for
from core.pos_api import PosError, ok
from services.dms_roster import self_credentials

router = APIRouter(tags=["line-dms-credentials"])

_STATUS = {
    "dms_credentials.operator_only": 403,
    "dms_credentials.operator_inactive": 403,
    "dms_credentials.endpoint_missing": 409,
    "dms_credentials.unavailable": 409,
    "dms_credentials.required": 422,
    "dms_credentials.too_long": 422,
    "dms_credentials.update_failed": 500,
}


class DmsCredentialsIn(BaseModel):
    username: str = ""
    password: str = ""


async def _authorize(request: Request) -> dict:
    from routes.dms_routes import _authorize as authorize_dms

    user = await asyncio.to_thread(authorize_dms, request)
    if not dms_line_enabled_for(user.get("tenant_id"), user.get("id")):
        raise PosError("dms_credentials.unavailable", 403)
    return user


def _raise(exc: self_credentials.SelfCredentialError):
    raise PosError(exc.code, _STATUS.get(exc.code, 400), detail=exc.code) from exc


@router.get("/api/line/dms-credentials")
async def get_dms_credentials(request: Request):
    user = await _authorize(request)
    try:
        return ok(await asyncio.to_thread(self_credentials.load, user))
    except self_credentials.SelfCredentialError as exc:
        _raise(exc)


@router.put("/api/line/dms-credentials")
async def update_dms_credentials(request: Request, body: DmsCredentialsIn):
    user = await _authorize(request)
    try:
        return ok(
            await asyncio.to_thread(
                self_credentials.update,
                user,
                username=body.username,
                password=body.password,
            )
        )
    except self_credentials.SelfCredentialError as exc:
        _raise(exc)
