"""Interactive LINE steps for selecting one exact ERP destination."""

from __future__ import annotations

import asyncio
from typing import Any

from services.erp import team_access
from services.line_erp import cards, flow, store, target_preflight, target_selection
from services.line_platform import client as line_client

CHANNEL = "erp"


def _notify(line_user_id: str, reply_token: str | None, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    else:
        line_client.push_text(line_user_id, text, channel=CHANNEL)


def _locked(session: dict[str, Any]) -> bool:
    return session.get("state") in {"draft", "editing"}


async def show_target_picker(
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
    mode: str,
    *,
    page: int = 0,
) -> None:
    allowed = team_access.binding_line_modes(binding)
    if mode not in flow.MODES or mode not in allowed:
        _notify(line_user_id, reply_token, "บัญชีนี้ไม่มีสิทธิ์สำหรับรายการนี้")
        return
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing" or _locked(session):
        _notify(line_user_id, reply_token, "รายการปัจจุบันยังไม่เสร็จ กรุณาดำเนินการให้เรียบร้อย")
        return
    result = await asyncio.to_thread(target_preflight.inspect_targets, binding, refresh=True)
    store.set_session(binding["tenant_id"], line_user_id, "target", {"mode": mode})
    message = cards.target_picker_card(mode, result.get("targets") or [], page=page)
    if reply_token:
        line_client.reply_messages(reply_token, [message], channel=CHANNEL)
    else:
        line_client.push_messages(line_user_id, [message], channel=CHANNEL)


async def begin_mode(
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
    mode: str,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing":
        _notify(line_user_id, reply_token, "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่")
        return
    if _locked(session):
        _notify(
            line_user_id,
            reply_token,
            "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อนเริ่มรายการใหม่",
        )
        return
    try:
        await show_target_picker(binding, line_user_id, reply_token, mode)
    except target_preflight.TargetNotReady as exc:
        _notify(line_user_id, reply_token, target_preflight.status_text(exc.result))
    except Exception:
        _notify(line_user_id, reply_token, "ไม่สามารถตรวจสอบ ERP ได้ กรุณาลองใหม่")


async def choose_target(
    params: dict[str, list[str]],
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    session_mode = str((session.get("payload") or {}).get("mode") or "")
    mode = str((params.get("mode") or [session_mode])[0])
    if (
        session.get("state") != "target"
        or mode != session_mode
        or mode not in team_access.binding_line_modes(binding)
    ):
        _notify(line_user_id, reply_token, "รายการหมดอายุ กรุณาเลือกประเภทเอกสารใหม่")
        return
    endpoint_id = str((params.get("endpoint") or [""])[0]).strip()
    try:
        workspace_id = int(str((params.get("workspace") or [""])[0]).strip())
    except ValueError:
        _notify(line_user_id, reply_token, "กรุณาเลือกบัญชีและ ERP ใหม่")
        return
    try:
        readiness = await asyncio.to_thread(
            target_preflight.require_ready,
            binding,
            endpoint_id=endpoint_id,
            workspace_client_id=workspace_id,
            refresh=True,
        )
    except target_preflight.TargetNotReady as exc:
        _notify(line_user_id, reply_token, target_preflight.status_text(exc.result))
        return
    target = readiness["target"]
    payload = {
        "mode": mode,
        "direction": mode,
        "endpoint_id": str(target["endpoint_id"]),
        "workspace_client_id": int(target["workspace_client_id"]),
        "adapter": str(target.get("adapter") or "").lower(),
        "target_label": str(target.get("label") or "")[:200],
    }
    store.set_session(binding["tenant_id"], line_user_id, "posting", payload)
    message = cards.posting_mode_card(mode, target)
    if reply_token:
        line_client.reply_messages(reply_token, [message], channel=CHANNEL)
    else:
        line_client.push_messages(line_user_id, [message], channel=CHANNEL)


async def choose_posting_mode(
    value: str,
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") != "posting":
        _notify(line_user_id, reply_token, "รายการหมดอายุ กรุณาเลือกประเภทเอกสารใหม่")
        return
    requested = dict(session.get("payload") or {})
    field = "posting_kind" if requested.get("adapter") == "express" else "payment"
    requested[field] = value
    try:
        _, selection = await asyncio.to_thread(
            target_selection.normalize,
            binding,
            requested,
            refresh=True,
        )
    except target_selection.SelectionError as exc:
        text = (
            target_preflight.status_text(exc.readiness)
            if exc.readiness
            else "รูปแบบการบันทึกไม่ถูกต้อง กรุณาเลือกใหม่"
        )
        _notify(line_user_id, reply_token, text)
        return
    store.set_session(binding["tenant_id"], line_user_id, "receiving", selection)
    _notify(line_user_id, reply_token, "กรุณาส่งรูปภาพหรือ PDF")


__all__ = ["begin_mode", "choose_posting_mode", "choose_target", "show_target_picker"]
