# -*- coding: utf-8 -*-
"""LINE 语音消息 → 逐字转写 → 走与打字完全相同的文本路(VOICE-STT-DESIGN)。

转写复用网关 multimodal_to_json(Gemini 原生收音频·零新供应商·成本进 ai_usage 可归属),
先 push 回显「🎤 原文」让用户看到机器听到了什么(钱路诚实),再把转写文本喂入口注入的
text_handler —— 金额接地/confirm-first/撤销改错等既有钱闸对语音天然全部生效。
闸 agent_voice_stt 默认关:关/未绑定返回 False,入口落 unsupported 现状逐字节不变;
转写失败/听不清/超长一律诚实回复,绝不静默吞。
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

MAX_DURATION_MS = 120_000  # 超长语音诚实拒(控成本/超时;LINE 语音本身上限也在分钟级)
_MAX_TRANSCRIPT_CHARS = 500

_PROMPT = (
    "Transcribe this voice message verbatim in its original language "
    "(likely Thai, Chinese, English or Japanese). Keep numbers exactly as spoken. "
    'Reply with ONE line of JSON only: {"text": "<transcript>"} — '
    'use {"text": ""} if the audio is unintelligible or contains no speech.'
)

# LINE 专用过程文案(inline · 同 line_agent_bridge._PLAN_ACK 先例)。
_TOO_LONG = {
    "th": "ข้อความเสียงยาวเกินไปค่ะ (เกิน 2 นาที) รบกวนพูดสั้นลงหรือพิมพ์มาแทนนะคะ",
    "zh": "这条语音太长了(超过 2 分钟),请说短一点或改用文字。",
    "en": "That voice message is too long (over 2 minutes) — please keep it shorter or type instead.",
    "ja": "音声メッセージが長すぎます(2分超)。短くするか、テキストでお送りください。",
}
_UNCLEAR = {
    "th": "ฟังไม่ชัดค่ะ รบกวนพูดอีกครั้งหรือพิมพ์มาแทนนะคะ",
    "zh": "没听清,请再说一次或改用文字。",
    "en": "I couldn't catch that — please try again or type it instead.",
    "ja": "聞き取れませんでした。もう一度話すか、テキストでお送りください。",
}


def _say(reply_token, table, lang, line_user_id, tenant_id) -> bool:
    from services.line_binding import line_reply

    line_reply.reply_text_context(
        reply_token,
        table.get(lang, table["en"]),
        line_user_id=line_user_id,
        tenant_id=tenant_id,
    )
    return True


def _transcribe(audio: bytes, *, tenant_id, user_id) -> str:
    """网关转写。失败/不合形 → ""(调用方诚实拒)。LINE 语音为 AAC(m4a 容器)。"""
    from services.ai_gateway import transport

    outcome = transport.multimodal_to_json(
        _PROMPT,
        [(audio, "audio/aac")],
        max_tokens=512,
        timeout_s=20,
        task="line_voice_stt",
        tenant_id=tenant_id,
        user_id=user_id,
    )
    if not getattr(outcome, "ok", False) or not isinstance(getattr(outcome, "data", None), dict):
        return ""
    return str(outcome.data.get("text") or "").strip()[:_MAX_TRANSCRIPT_CHARS]


async def try_handle_audio(msg, line_user_id, reply_token, ev, ev_lang, *, text_handler) -> bool:
    """audio 事件入口。True=本层已回话;False=闸关/未绑定 → 入口落 unsupported 现状。"""
    from core import db, feature_flags
    from services.expense import line_lang
    from services.line_binding import line_reply

    if not (line_user_id and reply_token):
        return False
    bound = db.get_user_by_line_user_id(line_user_id)
    if not bound or not feature_flags.agent_voice_enabled_for(str(bound.get("id") or "") or None):
        return False
    tid = bound.get("tenant_id")
    lang = line_lang.card_lang(line_user_id, tid, ev_lang)
    try:
        if int(msg.get("duration") or 0) > MAX_DURATION_MS:
            return _say(reply_token, _TOO_LONG, lang, line_user_id, tid)
        from services.line_binding import line_client

        line_reply.begin_loading(line_user_id)
        # 下载/转写是阻塞网络调用 → to_thread(事件循环全站阻塞的既有教训,同文本路 PR#55)。
        audio = await asyncio.to_thread(line_client.download_message_content, msg.get("id"))
        if not audio:
            return _say(reply_token, _UNCLEAR, lang, line_user_id, tid)
        transcript = await asyncio.to_thread(
            _transcribe, audio, tenant_id=tid, user_id=str(bound.get("id"))
        )
        if not transcript:
            return _say(reply_token, _UNCLEAR, lang, line_user_id, tid)
        # 回显在前:记账卡出现前用户先核对机器听到了什么(听错金额与打错字同风险面,卡可撤可改)。
        line_reply.push_text_context(line_user_id, f"🎤 {transcript}", tenant_id=tid)
        await text_handler(
            line_user_id, reply_token, transcript, ev, quote_token=msg.get("quoteToken")
        )
        return True
    except Exception:
        logger.warning(
            "[line_stt] failed; honest fallback (uid=%s)", bound.get("id"), exc_info=True
        )
        try:
            return _say(reply_token, _UNCLEAR, lang, line_user_id, tid)
        except Exception:
            return True  # 回复也失败:已尽力,别把异常抛回 webhook
