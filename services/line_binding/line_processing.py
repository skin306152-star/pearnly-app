# -*- coding: utf-8 -*-
"""LINE「识别中」处理卡(Flex · docs/smart-intake/15 §2)。

从 line_card 拆出(控行数)。收图即回:猫咪 + 「正在认真看票中喵」陪伴 + 引用「你发的收据」
+ 进度条快照 + 时间预期。真 LINE 限制:Flex 静态——进度条不逐格走、气泡不呼吸;猫咪眨眼需
APNG(_CAT_ANIMATED)。动感靠 猫咪(APNG)+ 可叠原生 ••• 转圈。识别完由结果卡接上。
"""

from __future__ import annotations

_BRAND = "#2563EB"
_AMOUNT = "#111827"
_LABEL = "#98A2B3"
_VALUE = "#344054"

# 猫咪资产(APNG 到位后把 _CAT_ANIMATED 置 True 即眨眼)。
_CAT_URL = "https://pearnly.com/static/brand/kb-cat.png"
_CAT_ANIMATED = False

_PROC = {
    "zh": {
        "companion": "正在认真看票中喵～",
        "quote": "你发的收据",
        "title": "正在帮你看票",
        "step": "读取金额与卖家…",
        "hint": "💡 清晰票几秒,复杂热敏票最多约 30 秒",
    },
    "th": {
        "companion": "กำลังตั้งใจอ่านบิลอยู่นะเหมียว~",
        "quote": "ใบเสร็จที่คุณส่ง",
        "title": "กำลังอ่านบิลให้",
        "step": "อ่านยอดเงินและผู้ขาย…",
        "hint": "💡 บิลชัดไม่กี่วินาที · บิลความร้อนซับซ้อนสูงสุด ~30 วิ",
    },
    "en": {
        "companion": "Reading your receipt, meow~",
        "quote": "Your receipt",
        "title": "Reading your receipt",
        "step": "Extracting amount & vendor…",
        "hint": "💡 A few seconds for clear ones · up to ~30s for tricky thermal",
    },
    "ja": {
        "companion": "じっくり見てるニャ～",
        "quote": "送ってくれた領収書",
        "title": "領収書を読んでます",
        "step": "金額と取引先を読取中…",
        "hint": "💡 鮮明なら数秒 · 複雑な感熱紙は最大約30秒",
    },
}


def _txt(text, *, size, color, **kw) -> dict:
    return {"type": "text", "text": str(text), "size": size, "color": color, **kw}


def processing_card(lang: str = "zh") -> dict:
    """「识别中」处理卡(静态 Flex)。"""
    p = _PROC.get((lang or "zh").lower(), _PROC["zh"])
    return {
        "type": "flex",
        "altText": p["title"],
        "contents": {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    {  # 猫 + 陪伴气泡
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "md",
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "image",
                                "url": _CAT_URL,
                                "size": "xs",
                                "aspectMode": "fit",
                                "flex": 0,
                                "animated": _CAT_ANIMATED,
                            },
                            _txt(p["companion"], size="sm", color=_VALUE, flex=1, wrap=True),
                        ],
                    },
                    {  # 引用「你发的收据」
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "paddingAll": "8px",
                        "backgroundColor": "#F6F8FA",
                        "cornerRadius": "md",
                        "contents": [_txt("📄 " + p["quote"], size="xxs", color=_LABEL)],
                    },
                    {
                        "type": "text",
                        "text": f"{p['title']} •••",
                        "size": "lg",
                        "weight": "bold",
                        "color": _AMOUNT,
                        "margin": "lg",
                    },
                    _txt(p["step"], size="xs", color=_LABEL, margin="sm"),
                    {  # 进度条快照(静态 · 约 40%)
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "md",
                        "height": "5px",
                        "backgroundColor": "#EEF1F4",
                        "cornerRadius": "xl",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 2,
                                "backgroundColor": _BRAND,
                                "cornerRadius": "xl",
                                "contents": [],
                            },
                            {"type": "box", "layout": "vertical", "flex": 3, "contents": []},
                        ],
                    },
                    _txt(p["hint"], size="xxs", color="#AAB1BD", margin="md", wrap=True),
                ],
            },
        },
    }
