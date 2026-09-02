"""Document upload, OCR review, and confirmation handlers for Cowork LINE."""

from __future__ import annotations

import asyncio
import logging

from services.cowork_line import webhook

logger = logging.getLogger(__name__)


async def queue_document(
    message: dict,
    identity: dict,
    reply_token: str | None,
    lang: str,
) -> None:
    claimed = await asyncio.to_thread(
        webhook.session_store.claim_processing,
        tenant_id=identity["tenant_id"],
        line_user_id=identity["line_user_id"],
        message_id=str(message.get("id") or ""),
    )
    if claimed:
        webhook._spawn(process_document(message, identity, lang))
        return
    session = await asyncio.to_thread(webhook._session, identity)
    state = session.get("state")
    if state == "ocr_processing":
        key = "processing"
    elif state in {"draft", "editing"}:
        key = "finish_draft"
    else:
        key = "choose"
    webhook._reply_text(reply_token, webhook._text(lang, key))


async def process_document(message: dict, identity: dict, lang: str) -> None:
    try:
        await asyncio.to_thread(
            webhook.line_client.start_loading,
            identity["line_user_id"],
            30,
            channel=webhook.CHANNEL,
        )
        await recognize_document(message, identity, lang)
    except Exception:
        logger.exception("Cowork LINE OCR failed")
        session = await asyncio.to_thread(webhook._session, identity)
        payload = dict(session.get("payload") or {})
        payload.pop("message_id", None)
        if payload.get("posting_mode"):
            webhook._set(identity, "receiving", payload)
        webhook._notify(identity["line_user_id"], None, webhook._text(lang, "read_failed"))


async def recognize_document(message: dict, identity: dict, lang: str) -> None:
    session = await asyncio.to_thread(webhook._session, identity)
    payload = dict(session.get("payload") or {})
    if session.get("state") != "ocr_processing":
        return
    target = await webhook._require_target(identity, payload, refresh_probe=True)
    if not target:
        webhook.session_store.clear_session(
            tenant_id=identity["tenant_id"], line_user_id=identity["line_user_id"]
        )
        webhook._notify(identity["line_user_id"], None, webhook._text(lang, "target_changed"))
        return
    content = await asyncio.to_thread(
        webhook.line_client.download_message_content,
        message.get("id"),
        channel=webhook.CHANNEL,
    )
    if not content:
        raise RuntimeError("line_content_unavailable")
    user = await asyncio.to_thread(webhook.db.find_user_by_id, identity["user_id"])
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != identity["tenant_id"]
    ):
        raise PermissionError("cowork_identity_inactive")
    user = dict(user)
    user["entry"] = "cowork"
    filename = str(message.get("fileName") or "")
    if not filename:
        filename = f"line_{message.get('id')}.jpg"
    result = await asyncio.to_thread(
        webhook.run_recognition_core,
        user,
        content,
        webhook.SimpleNamespace(filename=filename),
        ws_client_id=target.get("workspace_client_id"),
        staged=True,
        posting_kind=(payload.get("posting_mode") if target["adapter"] == "express" else None),
        direction=payload["direction"],
        source="cowork_line",
    )
    history_ids = [str(value) for value in result.get("history_ids") or [] if value]
    if not history_ids:
        payload.pop("message_id", None)
        webhook._set(identity, "receiving", payload)
        webhook._notify(identity["line_user_id"], None, webhook._text(lang, "no_document"))
        return
    try:
        await asyncio.to_thread(
            webhook.intake.generate_and_save_pdf,
            content,
            result.get("raw_pages") or [],
            history_ids,
            identity["user_id"],
            identity["tenant_id"],
        )
        target = await asyncio.to_thread(
            webhook.erp_targets.resolve_history_workspace,
            identity,
            target,
            history_ids,
            payload["direction"],
            provisional_history_assignment=True,
        )
        nonce = webhook.secrets.token_urlsafe(24)
        payload.update(
            {
                "history_ids": history_ids,
                "nonce": nonce,
                "endpoint_id": target["endpoint_id"],
                "connection_workspace_client_id": target.get("connection_workspace_client_id"),
                "workspace_client_id": target.get("workspace_client_id"),
                "target_label": target.get("label"),
            }
        )
        payload.pop("message_id", None)
        if target["adapter"] == "mrerp":
            await asyncio.to_thread(
                webhook.intake.apply_posting_mode,
                identity,
                history_ids,
                payment=payload["posting_mode"],
            )
        preflights = [
            await asyncio.to_thread(
                webhook.erp_targets.preflight_document,
                identity,
                target,
                history_id,
                payload["direction"],
                posting_kind=(payload["posting_mode"] if target["adapter"] == "express" else None),
                payment=(payload["posting_mode"] if target["adapter"] == "mrerp" else None),
            )
            for history_id in history_ids
        ]
        missing = list(
            dict.fromkeys(code for result in preflights for code in (result.get("missing") or []))
        )
        payload["document_preflight"] = {
            "ok": not missing,
            "missing": missing,
            "block_reason": missing[0] if missing else None,
        }
        webhook._set(identity, "draft", payload)
        await show_preview(
            identity,
            None,
            history_ids[0],
            lang,
        )
    except Exception:
        await asyncio.to_thread(webhook.intake.cleanup_staged, identity, history_ids)
        raise


def _record_fields(record: dict) -> dict:
    pages = record.get("pages") or []
    page = pages[0] if pages and isinstance(pages[0], dict) else {}
    fields = page.get("fields") or {}
    return fields if isinstance(fields, dict) else {}


async def show_preview(
    identity: dict,
    reply_token: str | None,
    draft_id: str,
    lang: str,
) -> None:
    session = await asyncio.to_thread(webhook._session, identity)
    payload = dict(session.get("payload") or {})
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    draft_id = str(draft_id or "")
    if session.get("state") not in {"draft", "editing"} or draft_id not in history_ids:
        webhook._notify(identity["line_user_id"], reply_token, webhook._text(lang, "expired"))
        return
    records = await asyncio.to_thread(
        webhook.intake.draft_records,
        identity,
        draft_id,
        history_ids,
    )
    target = {
        "endpoint_id": payload.get("endpoint_id"),
        "connection_workspace_client_id": payload.get("connection_workspace_client_id"),
        "workspace_client_id": payload.get("workspace_client_id"),
        "adapter": payload.get("adapter"),
        "label": payload.get("target_label"),
    }
    card = webhook.flow_cards.preview_card(
        draft_id=draft_id,
        fields=_record_fields(records[0]),
        target=target,
        direction=payload["direction"],
        mode=payload["posting_mode"],
        lang=lang,
        record_count=len(records),
        item_count=sum(
            len((page.get("fields") or {}).get("items") or [])
            for record in records
            for page in record.get("pages") or []
            if isinstance(page, dict)
        ),
        preflight=payload.get("document_preflight"),
    )
    if reply_token:
        webhook._reply_card(reply_token, card)
    else:
        webhook.line_client.push_messages(identity["line_user_id"], [card], channel=webhook.CHANNEL)


async def discard_draft(
    identity: dict,
    reply_token: str | None,
    draft_id: str,
    lang: str,
) -> None:
    session = await asyncio.to_thread(webhook._session, identity)
    payload = dict(session.get("payload") or {})
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    if session.get("state") not in {"draft", "editing"} or draft_id not in history_ids:
        webhook._reply_text(reply_token, webhook._text(lang, "expired"))
        return
    result = await asyncio.to_thread(webhook.intake.discard, identity, history_ids)
    if result.get("ok"):
        webhook.session_store.clear_session(
            tenant_id=identity["tenant_id"],
            line_user_id=identity["line_user_id"],
        )
        webhook._reply_text(reply_token, webhook._text(lang, "discarded"))


__all__ = [
    "discard_draft",
    "process_document",
    "queue_document",
    "recognize_document",
    "show_preview",
]
