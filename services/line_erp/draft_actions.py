"""ERP LINE staged-draft confirmation and discard actions."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from core import db
from services.erp import team_access
from services.line_erp import cards, draft_view, store
from services.line_platform import client as line_client

CHANNEL = "erp"


class BatchIncomplete(Exception):
    def __init__(self, result):
        self.result = result


def _saved_without_profile(result: dict[str, Any]) -> bool:
    rows = list(result.get("push_results") or [])
    return (
        str(result.get("status") or "") == "manual"
        and bool(rows)
        and all(
            row.get("status") == "manual"
            and row.get("error_msg") == "erp.workspace_endpoint_required"
            for row in rows
        )
    )


async def act_draft(
    binding: dict,
    line_user_id: str,
    reply_token: str | None,
    history_id: str,
    action: str,
    *,
    confirm_action: Callable[..., Awaitable[dict[str, Any]]],
    discard_action: Callable[..., Awaitable[dict[str, Any]]],
    feature_enabled: Callable[[Any, Any], bool],
) -> dict[str, Any]:
    if not history_id:
        return {"ok": False, "status": 409, "detail": "line_erp.draft_empty"}
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    payload = session.get("payload") or {}
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    if not history_ids and payload.get("history_id"):
        history_ids = [str(payload["history_id"])]
    if not history_ids:
        return {"ok": False, "status": 409, "detail": "line_erp.draft_empty"}
    if session.get("state") not in ("draft", "editing") or history_id not in history_ids:
        if reply_token:
            line_client.reply_text(reply_token, "รายการหมดอายุ กรุณาเปิดรายการใหม่", channel=CHANNEL)
        return {"ok": False, "status": 409, "detail": "line_erp.draft_expired"}
    mode = str(payload.get("mode") or "")
    if not team_access.mode_allowed(str(binding["tenant_id"]), str(binding["user_id"]), mode):
        return {"ok": False, "status": 403, "detail": "line_erp.draft_forbidden"}
    user = db.find_user_by_id(binding["user_id"])
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding["tenant_id"])
        or not feature_enabled(binding.get("tenant_id"), binding.get("user_id"))
    ):
        return {"ok": False, "status": 403, "detail": "line_erp.draft_forbidden"}
    user = dict(user)
    user["entry"] = "erp"
    if action == "discard":
        result = await discard_action(binding, history_ids)
        if not result["ok"]:
            if reply_token:
                line_client.reply_text(
                    reply_token,
                    "ทิ้งเอกสารไม่สำเร็จ กรุณาลองใหม่",
                    channel=CHANNEL,
                )
            return result
        text = "ทิ้งเอกสารเรียบร้อยแล้ว"
    else:
        result = await confirm_action(
            binding,
            user,
            history_id,
            history_ids,
            reply_token,
            mode,
            payload,
        )
        if not result["ok"]:
            if reply_token:
                detail = result.get("detail") or {}
                duplicate = isinstance(detail, dict) and any(
                    row.get("reason") == "duplicate" for row in detail.get("histories", [])
                )
                line_client.reply_text(
                    reply_token,
                    "เอกสารนี้บันทึกแล้ว กรุณาทิ้งรายการซ้ำครับ"
                    if duplicate
                    else "บันทึกไม่สำเร็จ กรุณาเปิดแก้ไขรายการแล้วลองใหม่",
                    channel=CHANNEL,
                )
            return result
        text = "บันทึกแล้ว"
    store.clear_session(binding["tenant_id"], line_user_id)
    if action == "discard":
        if reply_token:
            line_client.reply_text(reply_token, text, channel=CHANNEL)
    else:
        # Receipt errors must not turn an already committed save into a failed save.
        try:
            records = await asyncio.to_thread(
                draft_view.records,
                str(binding["user_id"]),
                str(binding["tenant_id"]),
                history_id,
                history_ids,
            )
            messages = [
                cards.saved_card(
                    cards.preview_card(
                        str(record.get("id") or history_id),
                        mode,
                        (record.get("pages") or [{}])[0].get("fields") or {},
                        target={"label": payload.get("target_label")},
                        posting_mode="",
                    )
                )
                for record in records
            ]
            if reply_token:
                line_client.reply_messages(reply_token, messages[:5], channel=CHANNEL)
                messages = messages[5:]
            for offset in range(0, len(messages), 5):
                line_client.push_messages(
                    line_user_id, messages[offset : offset + 5], channel=CHANNEL
                )
        except Exception:
            import logging

            logging.getLogger(__name__).exception("ERP saved receipt delivery failed")
    response = {"ok": True, "action": action, "history_ids": history_ids}
    if action != "discard":
        response.update({"status": "saved", "converted": result.get("converted", [])})
    return response


async def discard(binding: dict, history_ids: list[str]) -> dict[str, Any]:
    from core.db import get_cursor_rls
    from services.ocr import pdf_storage
    from services.ocr_history.staged import discard_staged_ocr_history_with_pdf_paths

    deleted, pdf_paths = await asyncio.to_thread(
        discard_staged_ocr_history_with_pdf_paths,
        str(binding["user_id"]),
        history_ids,
        tenant_id=binding["tenant_id"],
    )
    if deleted != len(history_ids):
        return {"ok": False, "status": 409, "detail": "line_erp.discard_incomplete"}
    for path in set(pdf_paths or []):
        with get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (path,))
            still_used = cur.fetchone() is not None
        if not still_used:
            pdf_storage.delete_pdf(path)
    return {"ok": True}


async def confirm(
    binding: dict,
    user: dict,
    draft_id: str,
    history_ids: list[str],
    reply_token: str | None,
    mode: str,
    selection_values: dict[str, Any],
    *,
    records_loader: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    from fastapi import HTTPException
    from services.erp import internal_records
    from services.line_erp import internal_flow

    try:
        selection = await asyncio.to_thread(
            internal_flow.recognized_selection,
            binding,
            {**selection_values, "mode": mode},
            history_ids,
        )
        return await asyncio.to_thread(
            internal_records.confirm,
            user,
            history_ids=history_ids,
            workspace_id=selection["workspace_client_id"],
            direction=mode,
        )
    except HTTPException as exc:
        return {"ok": False, "status": exc.status_code, "detail": exc.detail}


__all__ = ["BatchIncomplete", "act_draft", "confirm", "discard"]
