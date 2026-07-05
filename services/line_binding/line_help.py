# -*- coding: utf-8 -*-
"""已绑定用户「能干什么/怎么用」的确定性回复(Agent 升级改造 W1-4)。

Agent 全量后 capability/upload 类短问全进大脑,回复质量看模型发挥;能力说明是最不该
赌的一句(往往是新用户第一问)。这里在前门之前确定性接住:泰语用户回 A2 能力图卡,
其他语言回四语能力文案;末尾都挂 拍照/示例记账/问能力 chips,答完直通第一单。

双保险防误伤(intro_intent 是 contains 匹配,「ค่าอาหารตามเมนู 250」含 เมนู 会命中):
只接「无数字 + 短句」的纯问法,其余放行原路,绝不吃掉记账。任何故障 fail-open 回原路。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_MAX_LEN = 30  # 纯问法很短;超过这个长度多半是带上下文的业务句,交大脑


def _is_pure_help_ask(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and len(t) <= _MAX_LEN and not any(ch.isdigit() for ch in t)


def maybe_reply(bound_user, reply_token, line_user_id, text, lang, kind, quote_token=None) -> bool:
    """kind = replies.detect_smalltalk 结果。能力/上传类纯问法 → 确定性能力卡,返 True 消费本轮。"""
    if kind not in ("capability", "upload") or not _is_pure_help_ask(text):
        return False
    try:
        from services.line_binding import line_bind_i18n, line_imagemap, line_reply
        from services.line_binding.line_client import t_line

        if (lang or "th") == "th" and line_imagemap.has_card("capability"):
            msg = line_imagemap.card_message("capability")
        else:
            msg = {"type": "text", "text": t_line(lang, "line_intro_capability")}
        chips = line_bind_i18n.first_doc_nudge_msg(lang).get("quickReply")
        if chips:
            msg["quickReply"] = chips
        return bool(
            line_reply.reply_messages_context(
                reply_token,
                [msg],
                line_user_id=line_user_id,
                tenant_id=bound_user.get("tenant_id"),
                quote_token=quote_token or "",
            )
        )
    except Exception:
        logger.warning("[line_help] capability reply failed; fall through", exc_info=True)
        return False
