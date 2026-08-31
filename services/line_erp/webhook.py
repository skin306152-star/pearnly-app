"""ERP LINE event handling and staged-draft actions."""

from __future__ import annotations

import asyncio
import secrets
from types import SimpleNamespace
from urllib.parse import parse_qs

from fastapi import HTTPException

from core import db
from core.feature_flags import erp_line_enabled_for
from services.intake_bridge import convert as convert_svc
from services.line_binding import line_client
from services.line_erp import cards, flow, intake, preview, store
from services.line_erp.out import make_spawn
from services.ocr.recognize.core import run_recognition_core
from services.erp import team_access

CHANNEL = "erp"
_spawn = make_spawn("line_erp.webhook")
_MENU_WORDS = frozenset({"menu", "เมนู"})


class BatchIncomplete(Exception):
    def __init__(self, result):
        self.result = result


_allowed_modes = team_access.binding_line_modes


def draft_records(user_id: str, tenant_id: str, draft_id: str, ids: list[str]) -> list[dict]:
    from services.ocr_history.queries import get_ocr_history_detail

    records = []
    for history_id in ids:
        detail = get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id)
        if detail is None:
            raise HTTPException(403, detail="line_erp.draft_forbidden")
        page_numbers = []
        for index, page in enumerate(detail.get("pages") or []):
            raw_number = page.get("page_number") if isinstance(page, dict) else None
            try:
                page_number = max(0, int(raw_number or index + 1) - 1)
            except (TypeError, ValueError):
                page_number = index
            if page_number not in page_numbers:
                page_numbers.append(page_number)
        page_numbers = page_numbers or [0]
        detail["preview_urls"] = [
            f"/api/line/erp/draft/{draft_id}/records/{history_id}/page/{page}.png"
            for page in page_numbers
        ]
        detail["preview_url"] = detail["preview_urls"][0]
        records.append(detail)
    return records


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
                line_client.reply_messages(reply_token, [cards.menu_card(modes)], channel=CHANNEL)
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
                            cards.menu_card(
                                team_access.line_modes(
                                    str(identity["tenant_id"]), str(identity["user_id"])
                                )
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
        if mode in flow.MODES and mode in _allowed_modes(binding):
            session = store.get_session(binding["tenant_id"], line_user_id) or {}
            if session.get("state") == "ocr_processing":
                _notify(
                    line_user_id,
                    reply_token,
                    "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่",
                )
                return
            if session.get("state") in ("draft", "editing"):
                _notify(
                    line_user_id,
                    reply_token,
                    "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อนเริ่มรายการใหม่",
                )
                return
            store.set_session(binding["tenant_id"], line_user_id, "receiving", {"mode": mode})
            if reply_token:
                line_client.reply_text(reply_token, "กรุณาส่งรูปภาพหรือ PDF", channel=CHANNEL)
    elif action in ("confirm", "discard"):
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
                reply_token, [cards.menu_card(_allowed_modes(binding))], channel=CHANNEL
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
    store.set_session(binding["tenant_id"], line_user_id, "receiving", {"mode": mode})
    if reply_token:
        line_client.reply_text(reply_token, "กรุณาส่งรูปภาพหรือ PDF", channel=CHANNEL)


def _notify(line_user_id: str, reply_token: str | None, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    else:
        line_client.push_text(line_user_id, text, channel=CHANNEL)


def _restore_receiving(binding: dict, line_user_id: str, mode: str) -> None:
    store.set_session(binding["tenant_id"], line_user_id, "receiving", {"mode": mode})


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
        _spawn(_process_document(message, binding, line_user_id))
        return
    session = await asyncio.to_thread(store.get_session, binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing":
        text = "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่"
    elif session.get("state") in ("draft", "editing"):
        text = "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อนส่งเอกสารใหม่"
    else:
        text = "กรุณาเลือก 1 ซื้อ หรือ 2 ขาย ก่อนส่งเอกสาร"
    _notify(line_user_id, reply_token, text)


async def _process_document(message: dict, binding: dict, line_user_id: str) -> None:
    session = await asyncio.to_thread(store.get_session, binding["tenant_id"], line_user_id) or {}
    mode = (session.get("payload") or {}).get("mode") or ""
    try:
        await asyncio.to_thread(line_client.start_loading, line_user_id, 30, channel=CHANNEL)
        await _handle_document(message, binding, line_user_id, None, queued=True)
    except Exception:
        if mode in flow.MODES:
            _restore_receiving(binding, line_user_id, mode)
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
    mode = (session.get("payload") or {}).get("mode") or ""
    if mode not in flow.MODES or mode not in _allowed_modes(binding):
        if reply_token:
            line_client.reply_text(
                reply_token, "กรุณาเลือก 1 ซื้อ หรือ 2 ขาย ก่อนส่งเอกสาร", channel=CHANNEL
            )
        return
    message_id = message.get("id")
    content = await asyncio.to_thread(
        line_client.download_message_content, message_id, channel=CHANNEL
    )
    if not content:
        _restore_receiving(binding, line_user_id, mode)
        _notify(line_user_id, reply_token, "อ่านไฟล์ไม่สำเร็จ กรุณาส่งใหม่")
        return
    user = db.find_user_by_id(binding["user_id"])
    if not user:
        store.clear_session(binding["tenant_id"], line_user_id)
        _notify(line_user_id, reply_token, "ไม่พบผู้ใช้ ERP กรุณาติดต่อผู้ดูแล")
        return
    user = dict(user)
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
            {"mode": mode, "message_id": str(message_id or "")},
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
            ws_client_id=binding.get("workspace_client_id"),
            staged=True,
            direction=mode,
            posting_kind=None,
            source="line_erp",
        )
    except Exception:
        _restore_receiving(binding, line_user_id, mode)
        _notify(line_user_id, reply_token, "อ่านเอกสารไม่สำเร็จหรือเครดิตไม่พอ กรุณาลองใหม่")
        return
    history_ids = [str(value) for value in result.get("history_ids") or [] if value]
    if not history_ids:
        _restore_receiving(binding, line_user_id, mode)
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
    nonce = secrets.token_urlsafe(24)
    store.set_session(
        binding["tenant_id"],
        line_user_id,
        "draft",
        {"mode": mode, "history_ids": history_ids, "nonce": nonce},
    )
    preview_card = cards.preview_card(history_ids[0], mode, preview.from_result(result, mode))
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
            line_client.reply_text(
                reply_token, "รายการหมดอายุ กรุณาเปิดรายการใหม่", channel=CHANNEL
            )
        return {"ok": False, "status": 409, "detail": "line_erp.draft_expired"}
    mode = str(payload.get("mode") or "")
    if not team_access.mode_allowed(str(binding["tenant_id"]), str(binding["user_id"]), mode):
        return {"ok": False, "status": 403, "detail": "line_erp.draft_forbidden"}
    user = db.find_user_by_id(binding["user_id"])
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding["tenant_id"])
        or not erp_line_enabled_for(binding.get("tenant_id"), binding.get("user_id"))
    ):
        return {"ok": False, "status": 403, "detail": "line_erp.draft_forbidden"}
    user = dict(user)
    user["entry"] = "erp"
    if action == "discard":
        result = await _discard(binding, history_ids)
        if not result["ok"]:
            if reply_token:
                line_client.reply_text(
                    reply_token, "ทิ้งเอกสารไม่สำเร็จ กรุณาลองใหม่", channel=CHANNEL
                )
            return result
        text = "ทิ้งเอกสารเรียบร้อยแล้ว"
    else:
        result = await _confirm(binding, user, history_id, history_ids, reply_token)
        if not result["ok"]:
            return result
        text = "ยืนยันเอกสารเรียบร้อยแล้ว"
    store.clear_session(binding["tenant_id"], line_user_id)
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    return {"ok": True, "action": action, "history_ids": history_ids}


async def _discard(binding: dict, history_ids: list[str]) -> dict:
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


async def _confirm(
    binding: dict,
    user: dict,
    draft_id: str,
    history_ids: list[str],
    reply_token: str | None,
) -> dict:
    records = draft_records(
        str(binding["user_id"]), str(binding["tenant_id"]), draft_id, history_ids
    )
    missing = []
    for record in records:
        pages = record.get("pages") or []
        fields = (pages[0].get("fields") or {}) if pages and isinstance(pages[0], dict) else {}
        error = convert_svc.erp_declaration_error(fields)
        if error:
            missing.append(error)
        if not str(fields.get("date") or fields.get("invoice_date") or "").strip():
            missing.append("no_date")
        if (
            fields.get("direction") == "sales"
            and not str(fields.get("invoice_no") or fields.get("invoice_number") or "").strip()
        ):
            missing.append("no_doc_no")
    if missing:
        text = "กรุณาแก้ไขและเลือกประเภทสินค้า stock หรือบริการ service ให้ครบก่อนยืนยัน"
        if reply_token:
            line_client.reply_text(reply_token, text, channel=CHANNEL)
        return {"ok": False, "status": 409, "detail": "line_erp.posting_kind_required"}
    try:
        with db.get_cursor_rls(
            binding["tenant_id"], user_id=str(binding["user_id"]), commit=True
        ) as cur:
            result = convert_svc.convert_histories(
                cur,
                tenant_id=binding["tenant_id"],
                user_id=str(binding["user_id"]),
                history_ids=history_ids,
            )
            converted_ids = {str(row.get("history_id")) for row in result.get("converted") or []}
            already_ids = {
                str(row.get("history_id"))
                for row in result.get("skipped") or []
                if row.get("reason") == "already_converted"
            }
            if set(history_ids) - (converted_ids | already_ids):
                raise BatchIncomplete(result)
            cur.execute(
                "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
                "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
                "AND user_id = %s::uuid AND staged = TRUE",
                (history_ids, str(binding["tenant_id"]), str(binding["user_id"])),
            )
            cur.execute(
                "SELECT count(*) AS n FROM ocr_history WHERE id = ANY(%s::uuid[]) "
                "AND tenant_id = %s::uuid AND user_id = %s::uuid AND staged = FALSE",
                (history_ids, str(binding["tenant_id"]), str(binding["user_id"])),
            )
            if int((cur.fetchone() or {}).get("n") or 0) != len(set(history_ids)):
                raise BatchIncomplete(result)
    except BatchIncomplete as exc:
        if reply_token:
            line_client.reply_text(
                reply_token,
                "ยืนยันไม่สำเร็จ เอกสารยังไม่ถูกบันทึก กรุณาตรวจสอบรายการ",
                channel=CHANNEL,
            )
        return {
            "ok": False,
            "status": 409,
            "detail": "line_erp.confirm_incomplete",
            "result": exc.result,
        }
    return {"ok": True}
