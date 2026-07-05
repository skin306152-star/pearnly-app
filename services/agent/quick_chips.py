# -*- coding: utf-8 -*-
"""回复底部 quick-reply chips(P2)——教用户能问什么,点一下即问。

只挂在 Agent 文本回复与安全兜底上(数据卡/旧确定性路不动)。label 走 LINE 20 字硬限;
点击即以该语言发出对应查询句,走正常对话轮(零新入口)。语言与 loop._reply_lang 同源
(看用户本条消息的文字系统,不读账号偏好),chips 永远和正文一个语言。
闸 agent_quick_chips 默认关;闸关/异常一律降级纯文本,绝不挡回复。
"""

from __future__ import annotations

# (label ≤20 字, 点击发出的查询句)——三个高价值动作,四语同构。
_CHIPS = {
    "th": (
        ("ดูประวัติ", "ดูประวัติเอกสารล่าสุด"),
        ("เครดิตคงเหลือ", "เครดิตเหลือเท่าไหร่"),
        ("ผลกระทบยอด", "ผลกระทบยอดล่าสุดเป็นยังไง"),
    ),
    "zh": (
        ("查看历史", "看一下最近的识别历史"),
        ("查余额", "余额还有多少"),
        ("对账结果", "最近对账结果怎么样"),
    ),
    "en": (
        ("History", "Show my recent scan history"),
        ("Balance", "How much credit is left?"),
        ("Reconciliation", "How did the latest reconciliation go?"),
    ),
    "ja": (
        ("履歴を見る", "最近のスキャン履歴を見せて"),
        ("残高を確認", "残高はいくらですか"),
        ("照合結果", "最新の照合結果はどうですか"),
    ),
}


def enabled_for(user_id) -> bool:
    """闸 agent_quick_chips(默认关·fail-closed)。"""
    from core import feature_flags

    return feature_flags.agent_quick_chips_enabled_for(str(user_id) if user_id else None)


# 大脑故障兜底的「再问一次」chip:一点即把原话重发(用户不用重打)。
_RETRY_LABEL = {"th": "ถามอีกครั้ง", "zh": "再问一次", "en": "Ask again", "ja": "もう一度きく"}


def quick_reply(user_text: str, lang: str, retry_text: str | None = None) -> dict:
    """LINE quickReply payload。语言=用户本条消息文字系统(与回复正文同源),回落入口 lang。
    retry_text 给了 → 首位插「再问一次」chip 重发原话(crash 兜底专用)。"""
    from services.expense.line_classify import detect_text_lang

    lg = detect_text_lang(user_text or "") or (lang if lang in _CHIPS else "en")
    items = [
        {
            "type": "action",
            "action": {"type": "message", "label": label[:20], "text": text},
        }
        for label, text in _CHIPS.get(lg, _CHIPS["en"])
    ]
    if retry_text:
        items.insert(
            0,
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": _RETRY_LABEL.get(lg, _RETRY_LABEL["en"]),
                    "text": retry_text[:300],
                },
            },
        )
    return {"items": items}
