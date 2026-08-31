# -*- coding: utf-8 -*-
"""Shared LINE webhook execution and deduplication lifecycle.

两条 LINE webhook(老会计 OA / DMS OA)共用这一份策略。这段逻辑原本在两个路由里各写一遍,
于是「先标记后处理」的缺陷也一模一样地存在两份:处理前就把 event_id 落表,handler 抛异常后
行仍在表里 → LINE 重投永远被拦 → 消息永久丢失且查无痕迹。收成一处之后,「claim 必须配一个
ack」这件事只需要守一个地方。

失败不自动重放:handler 可能已经部分写库(建单/扣费/入账),机器重放 = 重复入账。改成落证据
(last_error + 原始事件,48h)再回一句「请重发」—— 用户重发带的是新 webhookEventId,天然是
干净的一次。回执尽力而为:replyToken 可能已被 handler 消费或过期(异常往往发生在回复之后),
故先 reply 后回落 push;两条路都吞异常,回执失败不该掀翻同一批里其余事件的处理。
"""

from __future__ import annotations

import logging

from services.line_platform import client, webhook_dedup

logger = logging.getLogger(__name__)

_FAILED_TEXT = {
    "th": "เกิดข้อผิดพลาด กรุณาส่งรายการนี้อีกครั้ง",
    "zh": "本条处理失败，请重新发送。",
    "en": "This item could not be processed. Please send it again.",
    "ja": "処理に失敗しました。もう一度送信してください。",
}


async def run_event(
    ev: dict,
    handler,
    *,
    source: str,
    channel: str = "cowork",
    failed_text: str = "",
) -> bool:
    """跑一个事件并落终态。返回是否真的跑了 handler(重投/处理中 → False)。"""
    eid = ev.get("webhookEventId")
    if webhook_dedup.claim(eid, source=source) == webhook_dedup.CLAIM_SKIP:
        logger.info("[%s] duplicate event skipped id=%s", source, str(eid)[:24])
        return False
    try:
        await handler(ev)
        webhook_dedup.mark_done(eid)
    except Exception as e:
        logger.error("[%s] 事件处理异常: %s", source, e, exc_info=True)
        webhook_dedup.mark_failed(eid, f"{type(e).__name__}: {e}", ev)
        notify_failed(ev, channel=channel, text=failed_text)
    return True


def notify_failed(ev: dict, *, channel: str = "cowork", text: str = "") -> None:
    """告知发件人本条没处理成功、请重发。text 留空则按事件语言取通用文案。"""
    try:
        if (ev.get("type") or "") == "unfollow":
            return  # LINE 明令不可回复 unfollow,且用户已删好友,push 必被拒
        src = ev.get("source") or {}
        line_user_id = src.get("userId") or ""
        reply_token = ev.get("replyToken") or ""

        lang = client.pick_lang_from_line_event(ev)
        msg = text or _FAILED_TEXT.get(lang, _FAILED_TEXT["th"])
        if not msg:
            return
        if reply_token and _reply(reply_token, msg, channel):
            return
        if line_user_id:
            _push(line_user_id, msg, channel)
    except Exception:
        logger.warning("[%s] 失败回执未送达", channel, exc_info=True)


def _reply(reply_token: str, text: str, channel: str) -> bool:
    try:
        return bool(client.reply_text(reply_token, text, channel=channel))
    except Exception:
        logger.warning("[%s] 失败回执 reply 失败,转 push", channel, exc_info=True)
        return False


def _push(line_user_id: str, text: str, channel: str) -> None:
    client.push_text(line_user_id, text, channel=channel)
