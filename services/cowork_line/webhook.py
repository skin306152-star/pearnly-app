"""Event-driven Cowork LINE menu, OCR draft and ERP posting workflow."""

from __future__ import annotations

import asyncio
import logging
import secrets  # noqa: F401
from types import SimpleNamespace  # noqa: F401
from urllib.parse import parse_qs

from core import db  # noqa: F401
from services.cowork_line import (
    erp_targets,
    flow_cards,
    friendship,
    identity_store,
    intake,  # noqa: F401
    menu_cards,
    session_store,
)
from services.erp.line_target_choice import find_account_choice, target_label_for_account
from services.line_platform import client as line_client
from services.ocr.recognize.core import run_recognition_core  # noqa: F401

logger = logging.getLogger(__name__)
CHANNEL = "cowork"
_MENU_WORDS = frozenset({"menu", "菜单", "菜單", "เมนู", "メニュー"})
_BUSY_STATES = frozenset({"ocr_processing", "draft", "editing"})

_COPY = {
    "th": {
        "follow": "กรุณาส่งรหัสเชื่อมต่อ 6 หลักจากหน้า Pearnly Cowork",
        "bind_ok": "เชื่อมต่อ Pearnly Cowork สำเร็จแล้ว",
        "bind_bad": "รหัสไม่ถูกต้องหรือหมดอายุ กรุณาขอรหัสใหม่จากหน้า Cowork",
        "bind_conflict": "LINE นี้เชื่อมต่อกับสมาชิกคนอื่นแล้ว",
        "not_bound": "กรุณาเชื่อมต่อ LINE ที่หน้า Pearnly Cowork ก่อน",
        "configure": "ยังไม่มี ERP ที่พร้อมใช้งาน กรุณาให้เจ้าของตั้งค่าที่หน้า Cowork > การเชื่อมต่อ",
        "upload": "ตรวจสอบการเชื่อมต่อแล้ว กรุณาส่งรูปภาพหรือ PDF",
        "processing": "กำลังอ่านเอกสาร กรุณารอสักครู่",
        "finish_draft": "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อน",
        "choose": "กรุณาเริ่มจากเมนูและเลือก ERP ก่อนส่งเอกสาร",
        "target_changed": "การเชื่อมต่อ ERP เปลี่ยนไป กรุณาเลือกใหม่จากเมนู",
        "read_failed": "อ่านเอกสารไม่สำเร็จ กรุณาส่งใหม่",
        "no_document": "ไม่พบเอกสารที่อ่านได้ กรุณาส่งใหม่",
        "discarded": "ทิ้งเอกสารแล้ว",
        "expired": "รายการหมดอายุ กรุณาเริ่มใหม่จากเมนู",
    },
    "zh": {
        "follow": "请发送 Pearnly Cowork 网页显示的 6 位绑定码。",
        "bind_ok": "Pearnly Cowork 绑定成功。",
        "bind_bad": "绑定码无效或已过期，请在 Cowork 网页重新获取。",
        "bind_conflict": "该 LINE 已绑定其他 Pearnly 成员。",
        "not_bound": "请先在 Pearnly Cowork 网页绑定 LINE。",
        "configure": "没有可用的 ERP 连接，请让老板到 Cowork「集成」完成配置。",
        "upload": "连接预检通过，请上传图片或 PDF。",
        "processing": "正在识别单据，请稍候。",
        "finish_draft": "请先确定入账、编辑或丢弃当前单据。",
        "choose": "请从菜单开始，选择 ERP 后再上传单据。",
        "target_changed": "ERP 连接状态已变化，请从菜单重新选择。",
        "read_failed": "单据识别失败，请重新上传。",
        "no_document": "没有识别到可用单据，请重新上传。",
        "discarded": "单据已丢弃。",
        "expired": "操作已过期，请从菜单重新开始。",
    },
    "en": {
        "follow": "Send the 6-digit connection code shown in Pearnly Cowork.",
        "bind_ok": "Pearnly Cowork connected.",
        "bind_bad": "The code is invalid or expired. Get a new code in Cowork.",
        "bind_conflict": "This LINE is connected to another Pearnly member.",
        "not_bound": "Connect LINE from Pearnly Cowork first.",
        "configure": "No ERP connection is ready. Ask the owner to configure Cowork integrations.",
        "upload": "Connection checks passed. Send an image or PDF.",
        "processing": "Reading the document. Please wait.",
        "finish_draft": "Confirm, edit, or discard the current document first.",
        "choose": "Start from the menu and choose an ERP before uploading.",
        "target_changed": "The ERP connection changed. Choose it again from the menu.",
        "read_failed": "The document could not be read. Send it again.",
        "no_document": "No usable document was found. Send it again.",
        "discarded": "Document discarded.",
        "expired": "This action expired. Start again from the menu.",
    },
    "ja": {
        "follow": "Pearnly Cowork に表示された6桁の連携コードを送信してください。",
        "bind_ok": "Pearnly Cowork と連携しました。",
        "bind_bad": "コードが無効または期限切れです。Cowork で再発行してください。",
        "bind_conflict": "この LINE は別のメンバーに連携されています。",
        "not_bound": "先に Pearnly Cowork で LINE を連携してください。",
        "configure": "利用可能な ERP 接続がありません。オーナーに設定を依頼してください。",
        "upload": "接続確認が完了しました。画像または PDF を送信してください。",
        "processing": "書類を読み取り中です。お待ちください。",
        "finish_draft": "現在の書類を確認、編集、または破棄してください。",
        "choose": "メニューから ERP を選択してからアップロードしてください。",
        "target_changed": "ERP 接続が変更されました。メニューから選び直してください。",
        "read_failed": "書類を読み取れませんでした。再送してください。",
        "no_document": "有効な書類が見つかりませんでした。再送してください。",
        "discarded": "書類を破棄しました。",
        "expired": "操作の有効期限が切れました。メニューから再開してください。",
    },
}


def _lang(event: dict, payload: dict | None = None) -> str:
    stored = str((payload or {}).get("lang") or "")
    if stored in _COPY:
        return stored
    value = line_client.pick_lang_from_line_event(event)
    return value if value in _COPY else "th"


def _text(lang: str, key: str) -> str:
    return _COPY.get(lang, _COPY["th"])[key]


def _spawn(coro) -> None:
    async def runner() -> None:
        try:
            await coro
        except Exception:
            logger.exception("Cowork LINE background task failed")

    asyncio.get_running_loop().create_task(runner())


def _reply_text(reply_token: str | None, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)


def _reply_card(reply_token: str | None, card: dict) -> None:
    if reply_token:
        line_client.reply_messages(reply_token, [card], channel=CHANNEL)


def _notify(line_user_id: str, reply_token: str | None, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    else:
        line_client.push_text(line_user_id, text, channel=CHANNEL)


def _session(identity: dict) -> dict:
    return (
        session_store.get_session(
            tenant_id=identity["tenant_id"], line_user_id=identity["line_user_id"]
        )
        or {}
    )


_set = friendship.set_session


def _params(event: dict) -> dict[str, str]:
    parsed = parse_qs(str((event.get("postback") or {}).get("data") or ""))
    return {key: values[0] for key, values in parsed.items() if values}


def _action(params: dict[str, str]) -> str:
    return params.get("a") or params.get("action") or ""


async def handle_event(event: dict) -> None:
    source = event.get("source") or {}
    line_user_id = str(source.get("userId") or "")
    reply_token = str(event.get("replyToken") or "") or None
    if source.get("type") != "user" or not line_user_id:
        return
    if await friendship.disconnect_if_unfollow(str(event.get("type") or ""), line_user_id):
        return
    identity = await asyncio.to_thread(identity_store.resolve_active_identity, line_user_id)
    if event.get("type") == "follow":
        lang = _lang(event)
        if identity:
            session = await asyncio.to_thread(_session, identity)
            state = session.get("state")
            if state in _BUSY_STATES:
                key = "processing" if state == "ocr_processing" else "finish_draft"
                _reply_text(reply_token, _text(lang, key))
                return
            _set(identity, "menu", {"lang": lang})
            _reply_card(reply_token, menu_cards.menu_card(lang))
        else:
            _reply_text(reply_token, _text(lang, "follow"))
        return
    if not identity:
        await _bind_if_possible(event, line_user_id, reply_token)
        return
    session = await asyncio.to_thread(_session, identity)
    lang = _lang(event, session.get("payload") or {})
    if event.get("type") == "postback":
        await _handle_postback(event, identity, reply_token, lang)
        return
    if event.get("type") != "message":
        return
    message = event.get("message") or {}
    if message.get("type") == "text":
        await _handle_text(message, identity, reply_token, lang)
    elif message.get("type") in {"image", "file"}:
        await _queue_document(message, identity, reply_token, lang)


async def _bind_if_possible(event: dict, line_user_id: str, reply_token: str | None) -> None:
    lang = _lang(event)
    message = event.get("message") or {}
    if event.get("type") != "message" or message.get("type") != "text":
        _reply_text(reply_token, _text(lang, "not_bound"))
        return
    code = str(message.get("text") or "").strip()
    if len(code) != 6 or not code.isdigit():
        _reply_text(reply_token, _text(lang, "not_bound"))
        return
    profile = await asyncio.to_thread(line_client.get_user_profile, line_user_id)
    try:
        identity = await asyncio.to_thread(
            identity_store.bind_identity_with_code,
            code=code,
            line_user_id=line_user_id,
            display_name=(profile or {}).get("displayName"),
            picture_url=(profile or {}).get("pictureUrl"),
        )
    except identity_store.CoworkLineIdentityError as exc:
        key = "bind_conflict" if exc.code == "line_conflict" else "bind_bad"
        _reply_text(reply_token, _text(lang, key))
        return
    if not identity:
        _reply_text(reply_token, _text(lang, "bind_bad"))
        return
    identity = {**identity, "line_user_id": line_user_id}
    _set(identity, "menu", {"lang": lang})
    if reply_token:
        line_client.reply_messages(
            reply_token,
            [{"type": "text", "text": _text(lang, "bind_ok")}, menu_cards.menu_card(lang)],
            channel=CHANNEL,
        )


async def _handle_text(message: dict, identity: dict, reply_token: str | None, lang: str) -> None:
    session = await asyncio.to_thread(_session, identity)
    state = session.get("state")
    text = str(message.get("text") or "").strip()
    if text.lower() in _MENU_WORDS or text in _MENU_WORDS:
        if state in {"ocr_processing", "draft", "editing"}:
            _reply_text(
                reply_token,
                _text(lang, "processing" if state == "ocr_processing" else "finish_draft"),
            )
            return
        _set(identity, "menu", {"lang": lang})
        _reply_card(reply_token, menu_cards.menu_card(lang))
        return
    if state == "ocr_processing":
        _reply_text(reply_token, _text(lang, "processing"))
    elif state in {"draft", "editing"}:
        _reply_text(reply_token, _text(lang, "finish_draft"))


async def _handle_postback(event: dict, identity: dict, reply_token: str | None, lang: str) -> None:
    params = _params(event)
    action = _action(params)
    session = await asyncio.to_thread(_session, identity)
    payload = dict(session.get("payload") or {})
    payload["lang"] = lang
    if action == menu_cards.ACTION_ERP_START:
        if session.get("state") in _BUSY_STATES:
            key = "processing" if session.get("state") == "ocr_processing" else "finish_draft"
            _reply_text(reply_token, _text(lang, key))
            return
        targets = await asyncio.to_thread(
            erp_targets.list_targets,
            identity,
            include_account_catalog=False,
        )
        if not targets:
            _set(identity, "select_erp", payload)
            _reply_text(reply_token, _text(lang, "configure"))
            return
        _set(identity, "select_erp", payload)
        _reply_card(reply_token, flow_cards.erp_picker_card(targets, lang))
        return
    expected_states = {
        "cowork_erp_type": {"select_erp", "select_account"},
        "cowork_erp_target": {"select_erp", "select_account"},
        "cowork_direction": {"select_direction"},
        "cowork_posting_mode": {"select_mode"},
        "cowork_discard": {"draft", "editing"},
    }
    if action not in expected_states or session.get("state") not in expected_states[action]:
        _reply_text(reply_token, _text(lang, "expired"))
        return
    if action == "cowork_erp_type":
        adapter = params.get("erp", "")
        try:
            page = max(0, int(params.get("page") or 0))
        except (TypeError, ValueError):
            page = 0
        targets = await asyncio.to_thread(
            erp_targets.list_targets,
            identity,
            include_account_catalog=False,
        )
        matches = [
            item
            for item in targets
            if item.get("selectable") and str(item.get("adapter") or "").lower() == adapter.lower()
        ]
        if adapter and len(matches) == 1:
            target = matches[0]
            params = {
                "endpoint": str(target.get("endpoint_id") or ""),
                "workspace": str(target.get("workspace_client_id") or ""),
            }
            selected = await _default_target_selection(identity, params, lang)
            if not selected:
                _reply_text(reply_token, _text(lang, "target_changed"))
                return
            _set(identity, "select_direction", selected)
            _reply_card(reply_token, flow_cards.direction_card(lang))
            return
        if not targets:
            _reply_text(reply_token, _text(lang, "configure"))
            return
        _set(identity, "select_erp", {"lang": lang})
        _reply_card(reply_token, flow_cards.erp_picker_card(targets, lang, page=page))
        return
    if action == "cowork_erp_target":
        selected = await _default_target_selection(identity, params, lang)
        if not selected:
            _reply_text(reply_token, _text(lang, "target_changed"))
            return
        _set(identity, "select_direction", selected)
        _reply_card(reply_token, flow_cards.direction_card(lang))
        return
    if action == "cowork_direction":
        direction = params.get("direction", "")
        if direction not in {"purchase", "sales"} or not payload.get("endpoint_id"):
            _reply_text(reply_token, _text(lang, "expired"))
            return
        payload["direction"] = direction
        _set(identity, "select_mode", payload)
        _reply_card(reply_token, flow_cards.mode_card(payload["adapter"], direction, lang))
        return
    if action == "cowork_posting_mode":
        mode = params.get("mode", "")
        if payload.get("adapter") == "express":
            allowed = {"stock", "service"}
        else:
            allowed = {"credit"} if payload.get("direction") == "purchase" else {"cash", "credit"}
        if mode not in allowed or not payload.get("direction"):
            _reply_text(reply_token, _text(lang, "expired"))
            return
        target = await _require_target(identity, payload)
        if not target:
            _reply_text(reply_token, _text(lang, "target_changed"))
            return
        payload["posting_mode"] = mode
        _set(identity, "receiving", payload)
        _reply_text(reply_token, _text(lang, "upload"))
        return
    if action == "cowork_discard":
        await _discard_draft(identity, reply_token, params.get("draft", ""), lang)


async def _require_target(
    identity: dict,
    selection: dict,
    *,
    refresh_probe: bool = False,
) -> dict | None:
    try:
        return await asyncio.to_thread(
            erp_targets.require_target,
            identity,
            str(selection.get("endpoint") or selection.get("endpoint_id") or ""),
            selection.get("workspace") or selection.get("workspace_client_id"),
            refresh_probe=refresh_probe,
            include_account_catalog=False,
        )
    except Exception:
        logger.info("Cowork LINE target no longer selectable", exc_info=True)
        return None


async def _default_target_selection(identity: dict, params: dict, lang: str) -> dict | None:
    target = await _require_target(identity, params)
    if not target:
        return None
    account = find_account_choice(target, account_key=target.get("selected_account_key"))
    if target.get("account_choices") and not account:
        return None
    selected = {
        "lang": lang,
        "endpoint_id": target["endpoint_id"],
        "workspace_client_id": target.get("workspace_client_id"),
        "adapter": target["adapter"],
        "target_label": (
            target_label_for_account(target, account) if account else target.get("label")
        ),
    }
    if account:
        selected.update(
            {
                "account_root": str(account.get("root_key") or "").strip() or None,
                "account_set": str(account.get("key") or account.get("account_set") or ""),
            }
        )
    return selected


async def _queue_document(
    message: dict, identity: dict, reply_token: str | None, lang: str
) -> None:
    from services.cowork_line.webhook_documents import queue_document

    await queue_document(message, identity, reply_token, lang)


async def _process_document(message: dict, identity: dict, lang: str) -> None:
    from services.cowork_line.webhook_documents import process_document

    await process_document(message, identity, lang)


async def _recognize_document(message: dict, identity: dict, lang: str) -> None:
    from services.cowork_line.webhook_documents import recognize_document

    await recognize_document(message, identity, lang)


async def _discard_draft(
    identity: dict,
    reply_token: str | None,
    draft_id: str,
    lang: str,
) -> None:
    from services.cowork_line.webhook_documents import discard_draft

    await discard_draft(identity, reply_token, draft_id, lang)


__all__ = ["handle_event"]
