# -*- coding: utf-8 -*-
"""LINE 智能回复(治复读 · docs/smart-intake/15 §5)。

感谢/求助各有一池回复,按 hash(text) 轮选 —— 同一句确定、不同句换说法,不三句一个模子。
greeting/thanks 走 L1 关键词检测(零成本);问候与跑题文案已收口到 line_i18n(line_greeting /
line_unknown_intent · P1E-1),由 reply_pool 直取,不再走本文件的池。纯函数,可单测。
"""

from __future__ import annotations

from typing import Optional

from services.expense import line_classify

_GREETING_WORDS = (
    "你好",
    "您好",
    "在吗",
    "hi",
    "hello",
    "hey",
    "สวัสดี",
    "หวัดดี",
    "こんにちは",
    "もしもし",
)
_THANKS_WORDS = (
    "谢谢",
    "多谢",
    "感谢",
    "thank",
    "thx",
    "ขอบคุณ",
    "ขอบใจ",
    "ありがと",
    "サンキュー",
)

_POOLS = {
    "thanks": {
        "zh": ["不客气😊 还有票就继续发", "应该的~ 随时记账查账", "👍 随时为你记一笔"],
        "th": [
            "ยินดีค่ะ😊 มีใบเสร็จส่งมาได้เรื่อยๆ",
            "ด้วยความยินดีค่ะ~ บันทึกได้ตลอด",
            "👍 พร้อมบันทึกให้เสมอ",
        ],
        "en": [
            "You're welcome 😊 Send more anytime",
            "Anytime~ happy to track it",
            "👍 Always here to log it",
        ],
        "ja": [
            "どういたしまして😊 続けてどうぞ",
            "いつでもどうぞ~ 記帳します",
            "👍 いつでも記録します",
        ],
    },
    "support": {
        "zh": [
            "记账/查账我直接帮你🙌 其他事(开通/计费/对接)请到 pearnly.com 联系我们,会有人跟进",
            "需要人工?记账查账这里就能办;账号/计费类问题到 pearnly.com 留言,团队会回你",
        ],
        "th": [
            "เรื่องบันทึก/ดูค่าใช้จ่ายทำให้ได้เลย🙌 เรื่องบัญชี/ค่าบริการ ทักที่ pearnly.com เดี๋ยวมีทีมดูแล",
            "ต้องการเจ้าหน้าที่? บันทึก/ดูยอดทำที่นี่ได้ ส่วนเรื่องบัญชี/บิล ฝากข้อความที่ pearnly.com",
        ],
        "en": [
            "I handle logging & lookups right here 🙌 For account/billing, reach us at pearnly.com and the team will follow up",
            "Need a human? Expenses I do here; for account/billing leave a note at pearnly.com",
        ],
        "ja": [
            "記帳・照会はここで対応します🙌 アカウント/請求は pearnly.com からご連絡ください、担当が対応します",
            "オペレーター希望ですか?経費はここで、アカウント/請求は pearnly.com へどうぞ",
        ],
    },
}


def detect_smalltalk(text: str) -> Optional[str]:
    """L1 关键词判 thanks / greeting / 引导意图(capability·start·upload·零成本);都不是 → None。

    引导意图复用 line_classify.intro_intent,与问候同走 reply_pool(各取 line_i18n 收口文案 + 引导)。
    """
    low = (text or "").strip().lower()
    if not low:
        return None
    if any(w in low for w in _THANKS_WORDS):
        return "thanks"
    if any(w in low for w in _GREETING_WORDS):
        return "greeting"
    return line_classify.intro_intent(low) or None


def pick(kind: str, text: str, lang: str) -> str:
    """从 kind 池按 hash(text) 轮选一条(确定但不复读)。kind 未知 → support。"""
    pool = _POOLS.get(kind) or _POOLS["support"]
    by_lang = pool.get((lang or "zh").lower()) or pool["zh"]
    idx = sum(ord(c) for c in (text or "x")) % len(by_lang)
    return by_lang[idx]
