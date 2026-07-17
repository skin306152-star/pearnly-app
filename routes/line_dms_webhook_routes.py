# -*- coding: utf-8 -*-
"""Pearnly DMS 独立 LINE OA 的 webhook(DL-1)· POST /api/line/dms/webhook。

与老会计站 webhook(routes/line_webhook_routes)完全隔离:独立 channel profile('dms')、
独立绑定表(services/line_dms)、独立闸(dms_line)。老 OA 逐字节不受影响。

闸 dms_line 关 → 收到事件一律 200 静默零回复(fail-closed);闸开才走绑定/会话逻辑。
事件处理拆成可直接单测的 async 函数(照 line_webhook_routes._handle_line_event 风格)。
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request

from core.feature_flags import dms_line_enabled_for
from services.line_binding import line_client
from services.line_dms import store

logger = logging.getLogger(__name__)

router = APIRouter()

_CHANNEL = "dms"
_UNBIND_CMD = "ยกเลิกการเชื่อมต่อ"

# 泰语文案(经销商销售员受众 · 简洁不堆 emoji)。
_MSG_WELCOME = (
    "ยินดีต้อนรับสู่ Pearnly DMS\n\n"
    "พิมพ์รหัสเชื่อมต่อ 6 หลักที่ได้จากระบบ เพื่อเริ่มใช้งานผ่าน LINE"
)
_MSG_BIND_OK = "เชื่อมต่อสำเร็จแล้ว ตอนนี้ใช้งาน Pearnly DMS ผ่าน LINE ได้เลย"
_MSG_BIND_BAD = "รหัสไม่ถูกต้องหรือหมดอายุ กรุณาขอรหัสใหม่จากระบบแล้วส่งอีกครั้ง"
_MSG_UNBOUND = "ยกเลิกการเชื่อมต่อเรียบร้อยแล้ว"
_MSG_GUIDE = (
    "พิมพ์รหัสเชื่อมต่อ 6 หลักเพื่อเริ่มใช้งาน " "หรือพิมพ์ ยกเลิกการเชื่อมต่อ เพื่อออกจากระบบ"
)


def _reply(reply_token: str, text: str) -> None:
    """经 DMS channel 回复(webhook 唯一出口)。无 reply_token 静默跳过。"""
    if reply_token:
        line_client.reply_text(reply_token, text, channel=_CHANNEL)


async def _handle_dms_event(ev: dict) -> None:
    """单个 DMS LINE 事件处理:闸 → follow/text/unfollow 分发。

    闸判定域按事件所属租户(已绑用户从绑定拿 tenant/user;follow/未绑用户无租户 →
    全局 user_id=None 判)。闸关 → 直接 return(零回复,fail-closed)。
    """
    ev_type = ev.get("type")
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    reply_token = ev.get("replyToken")

    binding = store.get_binding_by_line_user(line_user_id) if line_user_id else None
    tenant_id = binding.get("tenant_id") if binding else None
    user_id = binding.get("user_id") if binding else None
    if not dms_line_enabled_for(tenant_id, user_id):
        return

    if ev_type == "follow":
        _reply(reply_token, _MSG_WELCOME)
        return

    if ev_type == "unfollow":
        if line_user_id:
            store.unbind_by_line_user(line_user_id)  # 静默,LINE 不许回复 unfollow
        return

    if ev_type == "message":
        msg = ev.get("message") or {}
        if msg.get("type") != "text":
            return
        await _handle_dms_text(line_user_id, reply_token, (msg.get("text") or "").strip())


async def _handle_dms_text(line_user_id: str, reply_token: str, text: str) -> None:
    """DMS 文字消息:6 位码核销绑定 / 解绑命令 / 其余引导一句。"""
    if not line_user_id:
        return

    if len(text) == 6 and text.isdigit():
        ident = store.consume_bind_code(text)
        if not ident:
            _reply(reply_token, _MSG_BIND_BAD)
            return
        profile = line_client.get_user_profile(line_user_id, channel=_CHANNEL) or {}
        ok = store.create_or_update_binding(
            ident["tenant_id"],
            ident["user_id"],
            line_user_id,
            display_name=profile.get("displayName"),
        )
        _reply(reply_token, _MSG_BIND_OK if ok else _MSG_BIND_BAD)
        return

    if text == _UNBIND_CMD:
        store.unbind_by_line_user(line_user_id)
        _reply(reply_token, _MSG_UNBOUND)
        return

    _reply(reply_token, _MSG_GUIDE)


@router.post("/api/line/dms/webhook")
async def line_dms_webhook(request: Request):
    """DMS LINE OA webhook 入口:验签(channel='dms',失败 400)→ 逐事件分发 → 恒回 {"ok":true}。"""
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")
    if not line_client.verify_signature(body, signature, channel=_CHANNEL):
        logger.warning("[line_dms_webhook] 签名校验失败")
        raise HTTPException(status_code=400, detail="line_dms.bad_signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"[line_dms_webhook] JSON 解析失败: {e}")
        raise HTTPException(status_code=400, detail="line_dms.bad_json")

    for ev in payload.get("events") or []:
        try:
            await _handle_dms_event(ev)
        except Exception as e:
            logger.error(f"[line_dms_webhook] 事件处理异常: {e}")

    return {"ok": True}
