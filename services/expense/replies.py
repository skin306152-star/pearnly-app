# -*- coding: utf-8 -*-
"""LINE 智能回复(治复读 · docs/smart-intake/15 §5)。

问候/感谢/跑题各有一池回复,按 hash(text) 轮选 —— 同一句确定、不同句换说法,不再三句一个模子。
greeting/thanks 走 L1 关键词(零成本,无需调 L2)。纯函数,可单测。
"""

from __future__ import annotations

from typing import Optional

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
    "greeting": {
        "zh": [
            "你好👋 想记账就发一句,比如「ค่าน้ำ 50」",
            "嗨~ 把票据拍给我,或发一句「打车 120」,我就记下",
            "在的👋 随时发票据或一句话,我帮你记账查账",
        ],
        "th": [
            "สวัสดีค่ะ👋 พิมพ์บันทึกได้เลย เช่น「ค่าน้ำ 50」",
            "หวัดดีค่ะ~ ส่งรูปใบเสร็จ หรือพิมพ์「ค่าแท็กซี่ 120」ก็บันทึกให้",
            "อยู่ค่ะ👋 ส่งใบเสร็จหรือพิมพ์ข้อความ เดี๋ยวบันทึกและดูยอดให้",
        ],
        "en": [
            "Hi 👋 Just type an expense, e.g. 'Water 50'",
            "Hey~ Send a receipt photo, or type 'Taxi 120' and I'll log it",
            "Here 👋 Send a receipt or a line anytime — I'll record & track it",
        ],
        "ja": [
            "こんにちは👋「水道 50」のように入力すれば記帳します",
            "やあ~ 領収書の写真か「タクシー 120」と送ってください、記録します",
            "います👋 領収書か一言を送れば、記帳と集計をします",
        ],
    },
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
    "scope": {
        "zh": [
            "我专做记账和查账 · 试试发「ค่าน้ำ 50」或问「本月花了多少」",
            "这个我帮不上😅 但记账查账找我 · 发张票或一句话试试",
            "我是你的记账助手 · 发票据或一句话记一笔,也能问本月花销",
        ],
        "th": [
            "ผมช่วยเรื่องบันทึก/ดูค่าใช้จ่าย · ลอง「ค่าน้ำ 50」หรือถาม「เดือนนี้จ่ายเท่าไหร่」",
            "เรื่องนี้ช่วยไม่ได้😅 แต่บันทึก/ดูค่าใช้จ่ายได้ · ส่งใบเสร็จหรือพิมพ์มาเลย",
            "ผมคือผู้ช่วยบันทึกบัญชี · ส่งใบเสร็จหรือพิมพ์ 1 บรรทัด หรือถามยอดเดือนนี้",
        ],
        "en": [
            "I focus on logging & checking expenses · try 'Water 50' or 'how much this month'",
            "Can't help with that 😅 but I do expenses · send a receipt or a line",
            "I'm your bookkeeping helper · send a receipt/line, or ask this month's spend",
        ],
        "ja": [
            "経費の記録と照会が専門です ·「水道 50」や「今月いくら」をどうぞ",
            "それは苦手です😅 でも経費はお任せ · 領収書か一言を送ってください",
            "記帳アシスタントです · 領収書か一言、または今月の支出をどうぞ",
        ],
    },
}


def detect_smalltalk(text: str) -> Optional[str]:
    """L1 关键词判 greeting / thanks(零成本);都不是 → None。"""
    low = (text or "").strip().lower()
    if not low:
        return None
    if any(w in low for w in _THANKS_WORDS):
        return "thanks"
    if any(w in low for w in _GREETING_WORDS):
        return "greeting"
    return None


def pick(kind: str, text: str, lang: str) -> str:
    """从 kind 池按 hash(text) 轮选一条(确定但不复读)。kind 未知 → scope。"""
    pool = _POOLS.get(kind) or _POOLS["scope"]
    by_lang = pool.get((lang or "zh").lower()) or pool["zh"]
    idx = sum(ord(c) for c in (text or "x")) % len(by_lang)
    return by_lang[idx]
