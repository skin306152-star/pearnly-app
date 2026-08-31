"""Minimal Messaging API webhook for Cowork LINE account binding."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request

from services.cowork_line import identity_store
from services.line_binding import line_client, line_webhook_dedup

router = APIRouter()
logger = logging.getLogger(__name__)

_COPY = {
    "follow": {
        "th": "เพิ่มเพื่อนสำเร็จแล้ว กรุณาส่งรหัสเชื่อมต่อ 6 หลักจากหน้า Pearnly Cowork",
        "en": "Friend added. Send the 6-digit connection code shown in Pearnly Cowork.",
        "zh": "已添加好友，请发送 Pearnly Cowork 网页显示的 6 位绑定码。",
        "ja": "友だち追加が完了しました。Pearnly Cowork に表示された6桁の連携コードを送信してください。",
    },
    "success": {
        "th": "เชื่อมต่อ Pearnly Cowork สำเร็จแล้ว",
        "en": "Pearnly Cowork connected successfully.",
        "zh": "Pearnly Cowork 绑定成功。",
        "ja": "Pearnly Cowork の連携が完了しました。",
    },
    "invalid": {
        "th": "รหัสไม่ถูกต้องหรือหมดอายุแล้ว กรุณาขอรหัสใหม่จากหน้า Pearnly Cowork",
        "en": "This code is invalid or expired. Get a new code from Pearnly Cowork.",
        "zh": "绑定码无效或已过期，请在 Pearnly Cowork 网页重新获取。",
        "ja": "コードが無効または期限切れです。Pearnly Cowork で新しいコードを取得してください。",
    },
    "conflict": {
        "th": "LINE นี้เชื่อมต่อกับสมาชิก Pearnly คนอื่นแล้ว กรุณายกเลิกการเชื่อมต่อเดิมก่อน",
        "en": "This LINE is connected to another Pearnly member. Disconnect it there first.",
        "zh": "该 LINE 已绑定其他 Pearnly 成员，请先在原账号解除绑定。",
        "ja": "このLINEは別の Pearnly メンバーに連携されています。先に元の連携を解除してください。",
    },
}


def _language(event: dict) -> str:
    lang = line_client.pick_lang_from_line_event(event)
    return lang if lang in {"th", "en", "zh", "ja"} else "th"


async def _reply(reply_token: str, key: str, lang: str) -> None:
    if reply_token:
        await asyncio.to_thread(
            line_client.reply_text,
            reply_token,
            _COPY[key][lang],
            channel="default",
        )


async def _handle_event(event: dict) -> None:
    event_type = event.get("type")
    source = event.get("source") or {}
    line_user_id = str(source.get("userId") or "")
    reply_token = str(event.get("replyToken") or "")
    lang = _language(event)
    if event_type == "follow" and source.get("type") == "user":
        await _reply(reply_token, "follow", lang)
        return
    message = event.get("message") or {}
    if (
        event_type != "message"
        or source.get("type") != "user"
        or message.get("type") != "text"
        or not line_user_id
    ):
        return
    code = str(message.get("text") or "").strip()
    if len(code) != 6 or not code.isdigit():
        return
    profile = await asyncio.to_thread(line_client.get_user_profile, line_user_id)
    try:
        membership = await asyncio.to_thread(
            identity_store.bind_identity_with_code,
            code=code,
            line_user_id=line_user_id,
            display_name=(profile or {}).get("displayName"),
            picture_url=(profile or {}).get("pictureUrl"),
        )
    except identity_store.CoworkLineIdentityError as exc:
        await _reply(reply_token, "conflict" if exc.code == "line_conflict" else "invalid", lang)
        return
    if not membership:
        await _reply(reply_token, "invalid", lang)
        return
    await _reply(reply_token, "success", lang)


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
            line_webhook_dedup.claim(event_id, source="cowork_binding")
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
