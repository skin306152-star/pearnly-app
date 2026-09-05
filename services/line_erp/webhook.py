"""ERP LINE event handling and staged-draft actions."""

from __future__ import annotations

import asyncio
import secrets
from types import SimpleNamespace
from urllib.parse import parse_qs

from core import db  # noqa: F401 - compatibility seam for route tests
from core.feature_flags import erp_line_enabled_for
from services.cloud_tasks import dispatch as cloud_dispatch
from services.erp import team_access
from services.intake_bridge import convert as convert_svc  # noqa: F401 - test seam
from services.line_erp import (
    cards,
    draft_actions,
    draft_view,
    flow,
    intake,
    menu_cards,
    push as line_push,  # noqa: F401 - compatibility seam for route tests
    store,
    target_flow,
    target_preflight,
    target_selection,
    workspace_resolution,
)
from services.line_erp.out import make_spawn
from services.line_platform import client as line_client
from services.ocr.recognize.core import run_recognition_core

CHANNEL = "erp"
_spawn = make_spawn("line_erp.webhook")
_MENU_WORDS = frozenset({"menu", "เมนู"})


_allowed_modes = team_access.binding_line_modes
draft_records = draft_view.records
BatchIncomplete = draft_actions.BatchIncomplete


async def _menu_card(_binding: dict, modes: tuple[str, ...]) -> dict:
    return menu_cards.menu_card(modes)


async def handle_event(ev: dict) -> None:
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    reply_token = ev.get("replyToken")
    if not line_user_id:
        return
    binding = store.get_binding(line_user_id)
    if binding and not erp_line_enabled_for(binding.get("tenant_id"), binding.get("user_id")):
        return
    modes = _allowed_modes(binding) if binding else ()
    if ev.get("type") == "follow":
        if reply_token:
            if binding:
                line_client.reply_messages(
                    reply_token,
                    [await _menu_card(binding, modes)],
                    channel=CHANNEL,
                )
            else:
                line_client.reply_text(
                    reply_token,
                    "ยินดีต้อนรับ กรุณาไปที่หน้า /erp เพื่อสร้างรหัส 6 หลัก แล้วส่งรหัสนี้ที่นี่ก่อนใช้งาน",
                    channel=CHANNEL,
                )
        return
    if not binding:
        await _bind_if_possible(ev, line_user_id, reply_token)
        return
    if ev.get("type") == "postback":
        await _handle_postback(ev, binding, line_user_id, reply_token)
        return
    if ev.get("type") != "message":
        return
    message = ev.get("message") or {}
    if message.get("type") == "text":
        await _handle_text(message, binding, line_user_id, reply_token)
    elif message.get("type") in ("image", "file"):
        await _queue_document(message, binding, line_user_id, reply_token)


async def _bind_if_possible(ev: dict, line_user_id: str, reply_token: str | None) -> None:
    message = ev.get("message") or {}
    if ev.get("type") == "message" and message.get("type") == "text":
        identity = store.consume_code(message.get("text", ""))
        if (
            identity
            and erp_line_enabled_for(identity.get("tenant_id"), identity.get("user_id"))
            and team_access.login_allowed(
                {
                    "id": identity.get("user_id"),
                    "tenant_id": identity.get("tenant_id"),
                    "is_active": True,
                }
            )
        ):
            profile = line_client.get_user_profile(line_user_id, channel=CHANNEL) or {}
            bound = store.bind(identity, line_user_id, profile.get("displayName", ""))
            if reply_token:
                if bound:
                    line_client.reply_messages(
                        reply_token,
                        [
                            {"type": "text", "text": "เชื่อมต่อ ERP สำเร็จ"},
                            await _menu_card(
                                {**identity, "line_user_id": line_user_id},
                                team_access.line_modes(
                                    str(identity["tenant_id"]), str(identity["user_id"])
                                ),
                            ),
                        ],
                        channel=CHANNEL,
                    )
                else:
                    line_client.reply_text(reply_token, "รหัสไม่ถูกต้อง", channel=CHANNEL)
            return
    if reply_token:
        line_client.reply_text(reply_token, "กรุณาผูกบัญชี ERP ก่อนใช้งาน", channel=CHANNEL)


async def _handle_postback(
    ev: dict, binding: dict, line_user_id: str, reply_token: str | None
) -> None:
    params = parse_qs((ev.get("postback") or {}).get("data", ""))
    action = (params.get("a") or [""])[0]
    if action.startswith("mode:"):
        mode = action.split(":", 1)[1]
        if mode not in _allowed_modes(binding):
            if reply_token:
                line_client.reply_text(
                    reply_token,
                    "บัญชีนี้ไม่มีสิทธิ์สำหรับรายการนี้",
                    channel=CHANNEL,
                )
            return
        await target_flow.begin_mode(binding, line_user_id, reply_token, mode)
    elif action == "erp-type":
        session = store.get_session(binding["tenant_id"], line_user_id) or {}
        session_mode = str((session.get("payload") or {}).get("mode") or "")
        mode = str((params.get("mode") or [session_mode])[0])
        adapter = str((params.get("erp") or [""])[0])
        try:
            page = int((params.get("page") or ["0"])[0])
        except ValueError:
            page = 0
        await target_flow.show_account_picker(
            binding,
            line_user_id,
            reply_token,
            mode,
            adapter,
            page=page,
        )
    elif action == "target-page":
        mode = str((params.get("mode") or [""])[0])
        await target_flow.begin_mode(binding, line_user_id, reply_token, mode)
    elif action == "target":
        await target_flow.choose_target(params, binding, line_user_id, reply_token)
    elif action.startswith("posting:"):
        await target_flow.choose_posting_mode(
            action.split(":", 1)[1], binding, line_user_id, reply_token
        )
    elif action == "discard":
        draft_id = (params.get("draft") or [""])[0]
        await act_draft(binding, line_user_id, reply_token, draft_id, action)


async def _handle_text(
    message: dict, binding: dict, line_user_id: str, reply_token: str | None
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing":
        if reply_token:
            line_client.reply_text(
                reply_token, "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่", channel=CHANNEL
            )
        return
    text = (message.get("text") or "").strip()
    if session.get("state") in ("draft", "editing"):
        if reply_token:
            line_client.reply_text(
                reply_token,
                "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อนเริ่มรายการใหม่",
                channel=CHANNEL,
            )
        return
    if text.lower() in _MENU_WORDS:
        store.set_session(binding["tenant_id"], line_user_id, "menu", {})
        if reply_token:
            line_client.reply_messages(
                reply_token,
                [await _menu_card(binding, _allowed_modes(binding))],
                channel=CHANNEL,
            )
        return
    if text not in ("1", "2"):
        return
    mode = "purchase" if text == "1" else "sales"
    if mode not in _allowed_modes(binding):
        if reply_token:
            line_client.reply_text(
                reply_token, "บัญชีนี้ไม่มีสิทธิ์สำหรับรายการนี้", channel=CHANNEL
            )
        return
    await target_flow.begin_mode(binding, line_user_id, reply_token, mode)


def _notify(line_user_id: str, reply_token: str | None, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    else:
        line_client.push_text(line_user_id, text, channel=CHANNEL)


def _restore_receiving(
    binding: dict,
    line_user_id: str,
    payload: dict,
) -> None:
    store.set_session(
        binding["tenant_id"],
        line_user_id,
        "receiving",
        {key: value for key, value in payload.items() if key != "message_id"},
    )


async def _queue_document(
    message: dict, binding: dict, line_user_id: str, reply_token: str | None
) -> None:
    """Reserve one OCR run, then let the webhook return before recognition starts."""
    claimed = await asyncio.to_thread(
        store.claim_processing,
        binding["tenant_id"],
        line_user_id,
        message.get("id"),
    )
    if claimed:
        cloud_dispatch.spawn(
            "line_erp.document",
            _process_document,
            message,
            binding,
            line_user_id,
            _legacy_spawn=_spawn,
        )
        return
    session = await asyncio.to_thread(store.get_session, binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing":
        text = "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่"
    elif session.get("state") in ("draft", "editing"):
        text = "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อนส่งเอกสารใหม่"
    elif session.get("state") in ("target", "posting"):
        text = "กรุณาเลือกบัญชี ERP และรูปแบบการบันทึกก่อนส่งเอกสาร"
    else:
        text = "กรุณาเลือก 1 ซื้อ หรือ 2 ขาย ก่อนส่งเอกสาร"
    _notify(line_user_id, reply_token, text)


async def _process_document(message: dict, binding: dict, line_user_id: str) -> None:
    session = await asyncio.to_thread(store.get_session, binding["tenant_id"], line_user_id) or {}
    processing_payload = session.get("payload") or {}
    mode = processing_payload.get("mode") or ""
    try:
        await asyncio.to_thread(line_client.start_loading, line_user_id, 30, channel=CHANNEL)
        await _handle_document(message, binding, line_user_id, None, queued=True)
    except Exception:
        if mode in flow.MODES:
            _restore_receiving(binding, line_user_id, processing_payload)
        _notify(line_user_id, None, "ดำเนินการไม่สำเร็จ กรุณาส่งเอกสารใหม่")
        raise


async def _handle_document(
    message: dict,
    binding: dict,
    line_user_id: str,
    reply_token: str | None,
    *,
    queued: bool = False,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing" and not queued:
        if reply_token:
            line_client.reply_text(
                reply_token, "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่", channel=CHANNEL
            )
        return
    session_payload = dict(session.get("payload") or {})
    mode = session_payload.get("mode") or ""
    if mode not in flow.MODES or mode not in _allowed_modes(binding):
        if reply_token:
            line_client.reply_text(
                reply_token, "กรุณาเลือก 1 ซื้อ หรือ 2 ขาย ก่อนส่งเอกสาร", channel=CHANNEL
            )
        return
    try:
        readiness, selection = await asyncio.to_thread(
            target_selection.normalize,
            binding,
            target_selection.from_payload(session_payload),
            refresh=True,
        )
    except target_selection.SelectionError as exc:
        if exc.code == "erp_user_inactive":
            store.clear_session(binding["tenant_id"], line_user_id)
        else:
            _restore_receiving(binding, line_user_id, session_payload)
        text = (
            target_preflight.status_text(exc.readiness)
            if exc.readiness
            else "กรุณาเลือกบัญชี ERP และรูปแบบการบันทึกใหม่"
        )
        _notify(line_user_id, reply_token, text)
        return
    message_id = message.get("id")
    content = await asyncio.to_thread(
        line_client.download_message_content, message_id, channel=CHANNEL
    )
    if not content:
        _restore_receiving(binding, line_user_id, selection)
        _notify(line_user_id, reply_token, "อ่านไฟล์ไม่สำเร็จ กรุณาส่งใหม่")
        return
    user = readiness["user"]
    if (
        not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding.get("tenant_id"))
        or not erp_line_enabled_for(binding.get("tenant_id"), binding.get("user_id"))
    ):
        store.clear_session(binding["tenant_id"], line_user_id)
        _notify(line_user_id, reply_token, "ไม่สามารถใช้งาน ERP ได้ในขณะนี้")
        return
    if not queued:
        store.set_session(
            binding["tenant_id"],
            line_user_id,
            "ocr_processing",
            {
                "mode": mode,
                **selection,
                "message_id": str(message_id or ""),
            },
            ttl_minutes=15,
        )
        await asyncio.to_thread(line_client.start_loading, line_user_id, 30, channel=CHANNEL)
    user["entry"] = "erp"
    try:
        result = await asyncio.to_thread(
            run_recognition_core,
            user,
            content,
            SimpleNamespace(filename=message.get("fileName") or f"line_{message_id}.jpg"),
            ws_client_id=selection["workspace_client_id"],
            staged=True,
            direction=mode,
            posting_kind=selection.get("posting_kind"),
            source="line_erp",
        )
    except Exception:
        _restore_receiving(binding, line_user_id, selection)
        _notify(line_user_id, reply_token, "อ่านเอกสารไม่สำเร็จหรือเครดิตไม่พอ กรุณาลองใหม่")
        return
    history_ids = [str(value) for value in result.get("history_ids") or [] if value]
    if not history_ids:
        _restore_receiving(binding, line_user_id, selection)
        _notify(line_user_id, reply_token, "ไม่พบเอกสารที่อ่านได้ กรุณาส่งไฟล์ใหม่")
        return
    await asyncio.to_thread(
        intake.generate_and_save_pdf,
        content,
        result.get("raw_pages") or [],
        history_ids,
        str(user["id"]),
        str(binding["tenant_id"]),
    )
    try:
        target = await asyncio.to_thread(
            workspace_resolution.resolve_history_workspace,
            binding,
            readiness["target"],
            history_ids,
            mode,
            provisional_history_assignment=True,
        )
    except (workspace_resolution.WorkspaceResolutionError, target_preflight.TargetNotReady):
        await draft_actions.discard(binding, history_ids)
        _restore_receiving(binding, line_user_id, selection)
        _notify(
            line_user_id,
            reply_token,
            "ไม่สามารถจับคู่บริษัทในเอกสารกับบัญชี Pearnly ได้ กรุณาตรวจสอบข้อมูลบริษัท",
        )
        return
    selection["connection_workspace_client_id"] = target.get("connection_workspace_client_id")
    selection["workspace_client_id"] = int(target["workspace_client_id"])
    nonce = secrets.token_urlsafe(24)
    store.set_session(
        binding["tenant_id"],
        line_user_id,
        "draft",
        {
            **selection,
            "history_ids": history_ids,
            "nonce": nonce,
        },
    )
    raw_pages = [page for page in result.get("raw_pages") or [] if isinstance(page, dict)]
    primary = raw_pages[0] if raw_pages else {}
    fields = primary.get("fields") if isinstance(primary.get("fields"), dict) else {}
    item_count = sum(
        len((page.get("fields") or {}).get("items") or [])
        for page in raw_pages
        if isinstance(page.get("fields"), dict)
    )
    preview_card = cards.preview_card(
        history_ids[0],
        mode,
        fields,
        target=target,
        posting_mode=str(selection.get("posting_mode") or ""),
        record_count=len(history_ids),
        item_count=item_count,
    )
    if reply_token:
        line_client.reply_messages(reply_token, [preview_card], channel=CHANNEL)
    else:
        line_client.push_messages(line_user_id, [preview_card], channel=CHANNEL)


async def act_draft(
    binding: dict,
    line_user_id: str,
    reply_token: str | None,
    history_id: str,
    action: str,
) -> dict:
    return await draft_actions.act_draft(
        binding,
        line_user_id,
        reply_token,
        history_id,
        action,
        confirm_action=_confirm,
        discard_action=_discard,
        feature_enabled=erp_line_enabled_for,
    )


async def _discard(binding: dict, history_ids: list[str]) -> dict:
    return await draft_actions.discard(binding, history_ids)


async def _confirm(
    binding: dict,
    user: dict,
    draft_id: str,
    history_ids: list[str],
    reply_token: str | None,
    mode: str,
    selection: dict | None = None,
) -> dict:
    return await draft_actions.confirm(
        binding,
        user,
        draft_id,
        history_ids,
        reply_token,
        mode,
        selection or {},
        records_loader=draft_records,
    )
