"""Messaging API webhook for Cowork LINE binding and ERP intake."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request

from services.cowork_line import webhook as cowork_flow
from services.line_binding import line_webhook_dedup

router = APIRouter()
logger = logging.getLogger(__name__)

# Stable aliases keep the existing binding contract tests and monkeypatches valid.
identity_store = cowork_flow.identity_store
line_client = cowork_flow.line_client
_handle_event = cowork_flow.handle_event


@router.post("/api/line/webhook")
async def cowork_line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")
    if not line_client.verify_signature(body, signature, channel="default"):
        return {"status": "ignored"}
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "bad_json"}
    for event in payload.get("events") or []:
        event_id = event.get("webhookEventId")
        if (
            line_webhook_dedup.claim(event_id, source="cowork_line")
            == line_webhook_dedup.CLAIM_SKIP
        ):
            continue
        try:
            await _handle_event(event)
            line_webhook_dedup.mark_done(event_id)
        except Exception as exc:
            line_webhook_dedup.mark_failed(
                event_id,
                f"{type(exc).__name__}: {exc}",
                event,
            )
            logger.exception("[cowork_line_webhook] event failed")
    return {"status": "ok"}
