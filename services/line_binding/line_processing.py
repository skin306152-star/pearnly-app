# -*- coding: utf-8 -*-
"""LINE「识别中」提示(docs/smart-intake/15 §2)。

LINE 硬限制:机器人发出的消息不能删/改 → 大处理卡识别完会一直杵着(显得过期)。只有原生
••• 转圈(chat/loading/start)来新消息会自动收起。故"识别中"= 原生 ••• 转圈 + 一句猫咪短句
(短句即便留着也像助手随口说一句,自然);识别完由结果卡接上。
"""

from __future__ import annotations

_PROC = {
    "zh": "🐱 正在认真看票中喵～ 稍等一下",
    "th": "🐱 กำลังตั้งใจอ่านบิลอยู่นะเหมียว~ รอแป๊บนึง",
    "en": "🐱 Reading your receipt, meow~ one moment",
    "ja": "🐱 じっくり領収書を見てるニャ～ 少々お待ちを",
}


def processing_text(lang: str = "zh") -> str:
    """识别中短句(配原生 ••• 转圈;一行,留着也自然)。"""
    return _PROC.get((lang or "zh").lower(), _PROC["zh"])
