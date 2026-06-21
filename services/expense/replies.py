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
    # 只发裸数字(「1」「65」)无物品/卖家:不入账,问一句记啥(治「1→记 1 THB 垃圾条目」)。
    "amount_no_item": {
        "th": [
            "ได้รับตัวเลขมาค่ะ😊 ถ้าจะบันทึกค่าใช้จ่าย บอกหน่อยได้ไหมคะว่าซื้ออะไร เช่น 'กาแฟ 65'",
            "เห็นแค่ตัวเลขค่ะ~ อยากบันทึกพิมพ์แบบนี้ได้เลยนะคะ เช่น 'ค่าน้ำ 50'",
        ],
        "zh": [
            "收到一个数字😊 想记一笔的话告诉我买了啥呀,比如「咖啡 65」",
            "只看到数字哦~ 记一笔可以这样发,例如「水费 50」",
        ],
        "en": [
            "Got a number 😊 To log it, tell me what it was for — like 'coffee 65'",
            "I only see a number~ to record, try e.g. 'water bill 50'",
        ],
        "ja": [
            "数字だけ届きました😊 記録するなら何に使ったか教えてください、例:「コーヒー 65」",
            "数字だけですね~ 記録は例えば「水道代 50」と送ってください",
        ],
    },
    # 语气层(P3A)没发挥时的回落话术:轮选治复读,仍带「记一笔/查账」钩子(reply_pool 注入)。
    "out_of_scope": {
        "th": [
            "อยู่เป็นเพื่อนเลยค่ะ😊 ว่างๆ ส่งค่าใช้จ่ายหรือใบเสร็จมาให้ดูแลได้นะคะ",
            "ฟังอยู่ค่ะ~ พร้อมช่วยบันทึกค่าใช้จ่ายหรือดูยอดเดือนนี้ให้เสมอนะคะ",
            "Pearnly อยู่ตรงนี้เสมอค่ะ😊 อยากบันทึกรายการหรือส่งรูปใบเสร็จ บอกได้เลยค่ะ",
        ],
        "zh": [
            "我在呢😊 想记账或发票据照片随时找我~",
            "陪你聊两句~ 要记一笔或看看这月花了多少,我都在",
            "Pearnly 一直在😊 发笔费用或票据给我都行",
        ],
        "en": [
            "I'm right here 😊 send an expense or a receipt whenever you like~",
            "I'm listening~ ready to log an expense or show this month's spending anytime",
            "Pearnly's always here 😊 just send an expense or a receipt photo",
        ],
        "ja": [
            "そばにいますよ😊 経費や領収書、いつでも送ってくださいね",
            "聞いてますよ~ 記録も今月の確認もいつでもどうぞ",
            "Pearnlyはいつでもここに😊 経費や領収書を送ってください",
        ],
    },
    "unknown": {
        "th": [
            "ขอโทษค่ะ ไม่แน่ใจว่าหมายถึงอะไร😅 อยากบันทึกค่าใช้จ่าย ดูบัญชี หรือส่งใบเสร็จดีคะ",
            "ยังไม่ค่อยเข้าใจประโยคนี้ค่ะ~ พิมพ์เช่น 'กาแฟ 65' เพื่อบันทึก หรือถาม 'เดือนนี้ใช้เท่าไหร่' ได้นะคะ",
            "บอกอีกนิดได้ไหมคะ จะได้ช่วยถูก😊 บันทึก/ดูบัญชี/อ่านใบเสร็จ ทำได้หมดค่ะ",
        ],
        "zh": [
            "我好像没太get到😅 你是想记一笔、查账,还是发张票据给我看看?",
            "嗯…这句我没太懂~ 可以直接说『咖啡 65』记一笔,或问『这月花了多少』",
            "再说清楚点我就能帮上啦😊 记账/查账/识别票据都行",
        ],
        "en": [
            "I didn't quite catch that 😅 Record an expense, check your books, or send a receipt?",
            "Hmm, not sure I got that~ type 'coffee 65' to log it, or ask 'how much this month?'",
            "Tell me a little more and I'll help 😊 I can record, look up, or read receipts.",
        ],
        "ja": [
            "うまく聞き取れませんでした😅 経費の記録、帳簿確認、領収書、どれにしますか?",
            "ちょっと分からなかったです~ 「コーヒー 65」で記録、「今月いくら?」で照会できます",
            "もう少し教えてもらえれば対応できます😊 記録・照会・領収書 OKです",
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
    if line_classify.is_time_query(low):
        return "time_query"
    if line_classify.is_date_query(low):
        return "date_query"
    return line_classify.intro_intent(low) or None


def pick(kind: str, text: str, lang: str) -> str:
    """从 kind 池按 hash(text) 轮选一条(确定但不复读)。kind 未知 → support。"""
    pool = _POOLS.get(kind) or _POOLS["support"]
    by_lang = pool.get((lang or "zh").lower()) or pool["zh"]
    idx = sum(ord(c) for c in (text or "x")) % len(by_lang)
    return by_lang[idx]
