# -*- coding: utf-8 -*-
"""LINE 图片意图接线层的四语过程文案(从 line_image_route 拆出 · 2026-07-02)。

只放确定性文案表 + 取词函数,零逻辑。与 push_confirm._ACK 同先例:LINE 专用
过程文案留代码侧(不进 i18n-data.js——那是网页词表)。
"""

_SKIP_ACK = {
    "th": "รับทราบค่ะ ใบนี้ไม่บันทึกและไม่ส่งเข้า ERP ให้นะคะ",
    "zh": "好的,这张不记账、也不推送。",
    "en": "Okay — this one won't be recorded or pushed to ERP.",
    "ja": "了解です。この伝票は記帳も ERP 送信もしません。",
}
_NO_ENDPOINT = {
    "th": "ยังไม่ได้เชื่อมต่อ ERP ค่ะ ไปที่เว็บ Pearnly > การเชื่อมต่อ เพื่อเพิ่มปลายทางก่อนนะคะ",
    "zh": "还没有可用的 ERP 端点,请先到网页「集成」里连接一个。",
    "en": "No ERP endpoint connected yet — add one under Integrations on the web first.",
    "ja": "ERP がまだ接続されていません。ウェブの「連携」から先に追加してください。",
}
_CANT_PUSH = {
    "th": "⚠️ ใบนี้ยังส่งเข้า ERP ไม่ได้ค่ะ: {reason} · เก็บเอกสารไว้ให้แล้ว แก้บนเว็บแล้วส่งได้เลย",
    "zh": "⚠️ 这张票暂不能推送:{reason}·单据已留存,到网页修正后可再推。",
    "en": "⚠️ This document can't be pushed yet: {reason} · it's saved — fix it on the web, then push.",
    "ja": "⚠️ この伝票はまだ送信できません:{reason} · 保存済みです。ウェブで修正後に送信できます。",
}
_BANK_STMT_GUIDE = {
    "th": (
        "ใบนี้เป็นรายการเดินบัญชีธนาคารค่ะ ไม่ใช่ใบเสร็จค่าใช้จ่าย · ไปที่เว็บ Pearnly > "
        "กระทบยอดธนาคาร เพื่ออัปโหลดทำกระทบยอดได้เลย หรือถามผลกระทบยอดล่าสุดกับฉันก็ได้ค่ะ"
    ),
    "zh": "这是银行对账单,不是费用票据·请到网页「银行对账」上传做对账;也可以直接问我最近的对账结果。",
    "en": (
        "This is a bank statement, not an expense receipt. Upload it under Bank Reconciliation "
        "on the web — or just ask me for the latest reconciliation results."
    ),
    "ja": (
        "これは銀行取引明細で、経費の伝票ではありません。ウェブの「銀行照合」から"
        "アップロードしてください。最新の照合結果は私に聞いても大丈夫です。"
    ),
}
_PUSH_DROPPED = {
    "th": "ส่วนการส่งเข้า ERP ยังไม่เปิดใช้งานค่ะ เก็บใบไว้ให้แล้ว เปิดใช้เมื่อไหร่ส่งได้เลย",
    "zh": "推送功能暂未开通,单据已留存,开通后可直接推。",
    "en": "ERP push isn't enabled yet — the document is saved and can be pushed once enabled.",
    "ja": "ERP 送信はまだ有効化されていません。伝票は保存済みで、有効化後に送信できます。",
}
_ID_CARD_GUIDE = {
    "th": (
        "ใบนี้ดูเหมือนบัตรประชาชนค่ะ ไม่ใช่ใบเสร็จ · ถ้าจะสร้างลูกค้า DMS "
        "พิมพ์บอกก่อน (เช่น 'บัตรใบต่อไปสร้างลูกค้า DMS') แล้วส่งรูปอีกครั้งนะคะ"
    ),
    "zh": "这像是身份证,不是费用票据·要建 DMS 客户的话,先说一声(比如「下一张身份证建 DMS 客户」)再重发这张图。",
    "en": (
        "This looks like an ID card, not an expense receipt. To create a DMS customer, "
        "tell me first (e.g. 'next ID card → DMS customer'), then resend the photo."
    ),
    "ja": (
        "これは身分証のようで、経費の伝票ではありません。DMS 顧客を作成するには、"
        "先に一言(例:「次の身分証は DMS 顧客に」)伝えてから写真を再送してください。"
    ),
}
_ASK_GOAL = {
    "th": (
        "ใบนี้อ่านได้ไม่มั่นใจค่ะ เก็บไว้ในประวัติสแกนให้แล้ว (ยังไม่ลงบัญชี) · "
        "จะให้ทำอะไรดีคะ ตอบมาสั้น ๆ (เช่น 'บันทึก' / 'ไม่ต้องทำอะไร') แล้วส่งรูปนี้อีกครั้งนะคะ"
    ),
    "zh": "这张读得不太确定,先存进识别记录了(没有入账)·要怎么处理?回我一句(比如「记账」「不用管」),再把这张图重发一次就按你说的办。",
    "en": (
        "I couldn't read this one confidently — it's saved to scan history (not booked). "
        "Tell me what to do (e.g. 'record it' / 'leave it') and resend the photo."
    ),
    "ja": (
        "この画像は自信を持って読み取れませんでした。スキャン履歴に保存済み(未記帳)です。"
        "どうするか一言(例:「記帳して」)返信し、写真をもう一度送ってください。"
    ),
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])
