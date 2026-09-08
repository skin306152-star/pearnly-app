# -*- coding: utf-8 -*-
"""Pearnly DMS LINE OA webhook(DL-1 + 多 OA)· POST /api/line/dms/webhook[/a|/b]。

每个 OA 一个独立入口:入口决定用哪把 secret 验签,再把 stable channel key 传进业务查找与
回复。与 Cowork、ERP webhook 完全隔离:独立 channel profile、独立绑定表(services/line_dms)、
独立闸(dms_line)。

闸 dms_line 关 → 收到事件一律 200 静默零回复(fail-closed);闸开才走绑定/会话逻辑。
事件处理拆成可直接单测的 async 函数。

兼容:旧 `/api/line/dms/webhook` 继续服务现有 ลั่วหยง DMS(默认 OA),行为不变。
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Request

from core.feature_flags import dms_line_enabled_for
from services.line_dms import cards, flow, menu_cards, query_access, store
from services.line_platform import channels as line_channels
from services.line_platform import client as line_client
from services.line_platform import webhook_runner as line_webhook_runner

logger = logging.getLogger(__name__)

router = APIRouter()

_LEGACY_CHANNEL = "dms"
_UNBIND_CMD = "ยกเลิกการเชื่อมต่อ"

# 泰语文案(经销商销售员受众 · 简洁不堆 emoji)。
_MSG_WELCOME = "ยินดีต้อนรับสู่ Pearnly DMS\n\nพิมพ์รหัสเชื่อมต่อ 6 หลักที่ได้จากระบบ เพื่อเริ่มใช้งานผ่าน LINE"
_MSG_BIND_OK = "เชื่อมต่อสำเร็จแล้ว ตอนนี้ใช้งาน Pearnly DMS ผ่าน LINE ได้เลย"
_MSG_BIND_BAD = "รหัสไม่ถูกต้องหรือหมดอายุ กรุณาขอรหัสใหม่จากระบบแล้วส่งอีกครั้ง"
_MSG_UNBOUND = "ยกเลิกการเชื่อมต่อเรียบร้อยแล้ว"
_MSG_GUIDE = (
    "พิมพ์รหัสเชื่อมต่อ 6 หลักเพื่อเริ่มใช้งาน หรือพิมพ์ ยกเลิกการเชื่อมต่อ เพื่อออกจากระบบ"
)
# 处理失败的回执:失败事件不自动重放,只能请用户重发(重发 = 新 event_id,不会重复建单)。
_MSG_FAILED = "ข้อความล่าสุดประมวลผลไม่สำเร็จค่ะ กรุณาส่งใหม่อีกครั้งนะคะ"


def _reply(reply_token: str, text: str, channel: str) -> None:
    """经指定 OA 回复(webhook 唯一出口)。无 reply_token 静默跳过。"""
    if reply_token:
        line_client.reply_text(reply_token, text, channel=channel)


async def _handle_dms_event(ev: dict, channel_key: str = _LEGACY_CHANNEL) -> None:
    from services.line_dms import binding_guard

    channel = line_channels.normalize(channel_key)
    line_id = (ev.get("source") or {}).get("userId")
    binding = (
        await asyncio.to_thread(store.get_binding_by_line_user, line_id, channel)
        if line_id
        else None
    )
    if binding and ev.get("type") != "unfollow":
        if not await asyncio.to_thread(binding_guard.current, binding):
            return
    with binding_guard.scope(binding):
        try:
            await _handle_dms_event_bound(ev, binding, channel)
        except binding_guard.BindingChanged:
            logger.warning("DMS event stopped after binding changed")


async def _handle_dms_event_bound(ev: dict, binding, channel: str) -> None:
    """单个 DMS LINE 事件处理:闸 → follow/text/unfollow 分发。

    闸判定域必须在「能知道租户是谁」之后:
      · 已绑用户 → 按其绑定租户判(E4)。
      · 未绑用户提交 6 位绑定码 → 先窥码定租户按该租户判闸(不能拿 None 判,否则 allowlist
        灰度下有效码被静默吞掉)——见 _handle_dms_bind_code。
      · 其余未绑事件(follow/解绑/引导)无从得知租户,按 None 判(fail-closed,现状保留)。
    """
    ev_type = ev.get("type")
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    reply_token = ev.get("replyToken")

    # 未绑用户的绑定码:闸判定域是「码所属租户」,须在核销前按码判闸。
    if not binding and ev_type == "message":
        msg = ev.get("message") or {}
        if msg.get("type") == "text":
            text = (msg.get("text") or "").strip()
            if len(text) == 6 and text.isdigit():
                await _handle_dms_bind_code(line_user_id, reply_token, text, channel)
                return

    tenant_id = binding.get("tenant_id") if binding else None
    user_id = binding.get("user_id") if binding else None
    if not dms_line_enabled_for(tenant_id, user_id):
        return

    if ev_type == "follow":
        # 已绑用户加好友 = 回访,直接给功能菜单(波2);未绑仍给绑定码指引。
        if binding:
            allowed = await asyncio.to_thread(query_access.can_query, binding)
            line_client.reply_messages(
                reply_token,
                [
                    {"type": "text", "text": cards.TXT_MENU_GREETING},
                    menu_cards.menu_card(can_query=bool(allowed)),
                ],
                channel=channel,
            )
        else:
            _reply(reply_token, _MSG_WELCOME, channel)
        return

    if ev_type == "unfollow":
        if line_user_id:
            store.unbind_by_line_user(line_user_id, channel)  # 静默,LINE 不许回复 unfollow
        return

    if ev_type == "postback":
        # 确认按钮只对已绑用户有意义(会话态挂在绑定租户下);未绑的 postback 忽略。
        if binding:
            await flow.handle_postback(binding, line_user_id, reply_token, ev.get("postback") or {})
        return

    if ev_type == "message":
        msg = ev.get("message") or {}
        if binding:
            await _handle_bound_message(binding, line_user_id, reply_token, msg, channel)
        elif msg.get("type") == "text":
            await _handle_dms_text(
                line_user_id, reply_token, (msg.get("text") or "").strip(), channel
            )


async def _handle_bound_message(
    binding: dict, line_user_id: str, reply_token: str, msg: dict, channel: str
) -> None:
    """已绑用户的消息 → 身份证对话流(DL-3)。解绑命令仍就地处理(不进流程)。"""
    mtype = msg.get("type")
    if mtype == "image":
        flow.handle_image(binding, line_user_id, msg.get("id"))
        return
    if mtype == "text":
        text = (msg.get("text") or "").strip()
        if text == _UNBIND_CMD:
            store.unbind_by_line_user(line_user_id, channel)
            _reply(reply_token, _MSG_UNBOUND, channel)
            return
        await flow.handle_text(binding, line_user_id, reply_token, text)


async def _handle_dms_bind_code(
    line_user_id: str, reply_token: str, code: str, channel: str = _LEGACY_CHANNEL
) -> None:
    """未绑用户提交 6 位码:先窥码定租户按其判闸(闸序缺陷根治),闸开才核销 + 绑定。

    闸对码所属租户关(或判不出租户归属的垃圾码)→ 零回复零核销:不泄漏功能存在,也不烧掉
    名单外租户的码(其码在 TTL 内待该租户进名单后仍可用)。闸开且码过期/已用 → 回 BIND_BAD。

    码只认本入口 OA:码在别的 OA 签发时 peek 判不出归属 → 零回复零核销,绝不串 OA。
    """
    if not line_user_id:
        return

    tenant_id = store.peek_bind_code_tenant(code, channel)
    if not tenant_id:
        return  # 判不出租户归属(垃圾码/别的 OA 的码)→ fail-closed 零回复
    if not dms_line_enabled_for(tenant_id, None):
        return  # 闸对该租户关 → 零回复、不核销(不泄漏、不烧他人码)

    ident = store.consume_bind_code(code, channel)
    if not ident:
        _reply(reply_token, _MSG_BIND_BAD, channel)  # 过期/已用(闸开着才回)
        return
    if line_channels.normalize(ident.get("channel_key")) != channel:
        logger.warning("[line_dms_webhook] bind code channel mismatch rejected")
        return
    profile = line_client.get_user_profile(line_user_id, channel=channel) or {}
    ok = store.create_or_update_binding(
        ident["tenant_id"],
        ident["user_id"],
        line_user_id,
        display_name=profile.get("displayName"),
        channel_key=channel,
    )
    _reply(reply_token, _MSG_BIND_OK if ok else _MSG_BIND_BAD, channel)


async def _handle_dms_text(
    line_user_id: str, reply_token: str, text: str, channel: str = _LEGACY_CHANNEL
) -> None:
    """未绑用户文字:解绑命令 / 其余引导一句。

    6 位绑定码在闸前已被 _handle_dms_event 窥码路由进 _handle_dms_bind_code(按码所属租户
    判闸再核销),不会走到这里 —— 故本函数只处理解绑与引导。
    """
    if not line_user_id:
        return

    if text == _UNBIND_CMD:
        store.unbind_by_line_user(line_user_id, channel)
        _reply(reply_token, _MSG_UNBOUND, channel)
        return

    _reply(reply_token, _MSG_GUIDE, channel)


async def _handle_webhook(request: Request, channel_key: str):
    """共用入口:按 channel key 验签(失败 400)→ 逐事件分发 → 恒回 {"ok":true}。"""
    channel = line_channels.normalize(channel_key)
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")
    if not line_client.verify_signature(body, signature, channel=channel):
        logger.warning("[line_dms_webhook] 签名校验失败 channel=%s", channel)
        raise HTTPException(status_code=400, detail="line_dms.bad_signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"[line_dms_webhook] JSON 解析失败: {e}")
        raise HTTPException(status_code=400, detail="line_dms.bad_json")

    # DMS 事件驱动 OCR/建单(烧钱且不可逆)→ 重跑比丢一条伤害大,故沿用 at-most-once:
    # 幂等占坑 + 成败收尾 + 失败回执统一在 runner,失败不自动重放而是请用户重发。
    for ev in payload.get("events") or []:
        await line_webhook_runner.run_event(
            ev,
            lambda event: _handle_dms_event(event, channel),
            source="line_dms_webhook",
            channel=channel,
            failed_text=_MSG_FAILED,
        )

    # 恒 200:LINE 平台重投是控制台开关(不归我们控),回非 200 只会让 LINE 判定 webhook
    # 挂掉并降级投递,救不回这一条 —— 补救靠 runner 的「请重发」回执。
    return {"ok": True}


@router.post("/api/line/dms/webhook")
async def line_dms_webhook(request: Request):
    """现有 ลั่วหยง DMS OA 入口(channel='dms')· 行为与旧版一致。"""
    return await _handle_webhook(request, "dms")


@router.post("/api/line/dms/webhook/a")
async def line_dms_webhook_a(request: Request):
    """A DMS OA 入口(channel='dms_a')· 用 A 的 secret 验签、A 的 token 回复。"""
    return await _handle_webhook(request, "dms_a")


@router.post("/api/line/dms/webhook/b")
async def line_dms_webhook_b(request: Request):
    """B DMS OA 入口(channel='dms_b')· 用 B 的 secret 验签、B 的 token 回复。"""
    return await _handle_webhook(request, "dms_b")
