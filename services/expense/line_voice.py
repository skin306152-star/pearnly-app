# -*- coding: utf-8 -*-
"""Pearnly Voice 语气层(P3A-1 · 空接,不接线主路径)。

大脑把意图判成闲聊/越界(chat_kind=out_of_scope|unknown)时,把死模板升级成自然、温暖、泰语
优先的 Pearnly 回复。本层只负责【组织这一句闲聊的措辞】—— 永不执行任何动作、永不写账。

安全边界(铁律):
- 走 P2E AI Gateway(run_task),不直连 provider。
- 只把用户这句闲聊文本喂给模型:不传 history、不传任何票据 OCR 原文/税号/金额上下文。
- 模型输出不可信 → 出口必过确定性 response_guard;不过则返回 None,调用方回落模板。
- 任何异常 → None。绝不崩、绝不阻塞主路径。
"""

from __future__ import annotations

_MAX_REPLY_LEN = 500

_PERSONA = """You are Pearnly, a warm, friendly smart accounting assistant on LINE for Thai SMEs.
The user just sent a small-talk / off-topic message. Reply to THAT message only, in a kind, human
tone.

Rules:
- Keep it short: 1-2 sentences.
- Reply in the user's language. Thai is the primary language; also support Chinese, English and
  Japanese — match whatever the user wrote.
- The user may be tired, joking, venting, complimenting you, or just chatting about daily life.
  Respond warmly and naturally like a friendly coworker, and vary your wording — don't sound
  formulaic or reuse the same closing line.
- You NEVER perform any action. Never claim you have recorded, saved, deleted, cancelled, submitted
  or filed anything — this layer only chats, it does not touch the books.
- Never reveal anything about the underlying technology, model or provider. Never claim to be a human.
- End naturally and gently by hinting that you can help record an expense or look up the books — a
  soft nudge, not a hard sell.

Output ONLY one JSON object, no prose, no markdown:

{"reply": "<your natural reply here>"}
"""


def compose(text, lang, *, api_key, quota_ok=lambda: True) -> str | None:
    """把一句闲聊组织成自然 Pearnly 回复;不安全/失败/超限 → None(调用方回落模板)。

    quota_ok() 为 False(每日上限,真实计数 P3A-2 接,这期注入)→ 直接 None,不调 Gateway。
    """
    try:
        if not api_key or not (text or "").strip():
            return None
        if not quota_ok():
            return None

        from services.ai_gateway import router as ai_gateway
        from services.expense import response_guard

        # 超时用 task 默认(line_chat_reply=8s):大脑已先跑一次 Gemini,语气层留太短常超时退冷兜底。
        res = ai_gateway.run_task("line_chat_reply", prompt=_PERSONA, text=text, api_key=api_key)
        if not res.ok or not isinstance(res.data, dict):
            return None
        reply = res.data.get("reply")
        if not isinstance(reply, str):
            return None
        reply = reply.strip()
        if not reply or len(reply) > _MAX_REPLY_LEN:
            return None
        if not response_guard.is_safe(reply):
            return None
        return reply
    except Exception:  # noqa: BLE001 — 语气层绝不崩,调用方回落确定性模板
        return None


def try_reply(bound_user, line_user_id, text, lang, tenant_id, chat_kind) -> str | None:
    """接线编排:仅 out_of_scope/unknown 用自然语气;其余引导类目仍走调用方固定模板。

    无 key/超额/护栏不过/失败 → None(调用方回落 line_out_of_scope / line_unknown_intent)。
    成功才 bump 每日计数。compose 保持纯逻辑,此处负责 key/配额/计数编排。绝不崩主路径。
    """
    try:
        if chat_kind not in ("out_of_scope", "unknown"):
            return None
        from services.expense import line_l2, line_voice_quota

        api_key = line_l2.resolve_api_key(bound_user)
        if not api_key:
            return None
        reply = compose(
            text,
            lang,
            api_key=api_key,
            quota_ok=lambda: line_voice_quota.within_cap(line_user_id, tenant_id),
        )
        if not reply:
            return None
        line_voice_quota.bump(line_user_id, tenant_id)
        return reply
    except Exception:  # noqa: BLE001
        return None
