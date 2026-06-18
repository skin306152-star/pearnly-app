# -*- coding: utf-8 -*-
"""LINE 采购改错澄清文案(P1E-2 · 本地 4 语池)。

从 line_i18n 拆出(避免其破 500·同 replies._POOLS / line_correct 旧 _CLARIFY 范式)。泰语优先、
自然准确。不把用户随口示例(咖啡 65 等)硬编进文案。语言由调用方按 detect_text_lang 选,缺省回退 zh。
"""

from __future__ import annotations

# 可在 LINE 内直接改的字段标签(填进「问新值」模板)。明细/付款方式不在此(改在详情页)。
FIELD_LABELS = {
    "amount": {"zh": "金额", "th": "ยอดเงิน", "en": "amount", "ja": "金額"},
    "date": {"zh": "日期", "th": "วันที่", "en": "date", "ja": "日付"},
    "seller": {"zh": "卖家", "th": "ร้านค้า", "en": "seller", "ja": "販売者"},
    "category": {"zh": "分类", "th": "หมวดหมู่", "en": "category", "ja": "分類"},
}

# 验收 #1:笼统说「识别错了/不对」→ 列可改字段,问改哪里(不重拍·不当 OCR 失败)。
CLARIFY_FIELDS = {
    "zh": "我知道你想修改这张记录。你想改金额、日期、卖家、分类,还是明细?",
    "th": "ฉันเห็นว่าคุณต้องการแก้รายการนี้ค่ะ ต้องการแก้ส่วนไหน: ยอดเงิน, วันที่, ร้านค้า, หมวดหมู่ หรือรายการย่อย?",
    "en": "I see you want to correct this record. Which part should I change: amount, date, seller, category, or line items?",
    "ja": "この記録を修正したいのですね。どの項目を変更しますか:金額、日付、販売者、分類、明細?",
}

# 验收 #3:指出了具体字段但没给新值 → 问新值,并引导用「改成」语法(下一句走既有 edit 流确认)。
ASK_VALUE = {
    "zh": "好的,新的{field}是什么?直接回复即可,例如「{field}改成 ...」。",
    "th": "ได้ค่ะ {field}ใหม่คืออะไรคะ? พิมพ์บอกได้เลย เช่น “แก้{field}เป็น ...”",
    "en": 'Sure — what is the new {field}? Just reply, e.g. "change {field} to ...".',
    "ja": "承知しました。新しい{field}は何ですか?例:「{field}を…に変更」と返信してください。",
}

# 验收 #4:明细可能不全(复杂餐饮小票)→ 引导详情页核对;核心字段没问题可点卡片「บันทึกต่อ」继续。
DETAIL_INCOMPLETE = {
    "zh": "这张票的明细可能不完整,建议先打开详情页核对后再保存。如果核心字段没问题,也可以点卡片上的「บันทึกต่อ / 继续保存」。",
    "th": "รายการย่อยของใบเสร็จนี้อาจไม่ครบ กรุณาเปิดหน้ารายละเอียดเพื่อตรวจสอบก่อนบันทึกค่ะ หากข้อมูลหลักถูกต้องแล้ว สามารถกดปุ่ม “บันทึกต่อ” บนการ์ดได้ค่ะ",
    "en": 'The line items on this receipt may be incomplete — please open the detail page to check before saving. If the core fields are correct, you can tap "บันทึกต่อ / Save anyway" on the card.',
    "ja": "この領収書の明細が不完全な可能性があります。保存前に詳細ページでご確認ください。主要項目が正しければ、カードの「บันทึกต่อ / そのまま保存」を押せます。",
}


def field_label(field: str, lang: str) -> str:
    return FIELD_LABELS.get(field, {}).get(lang) or FIELD_LABELS.get(field, {}).get("zh", field)


def t(pool: dict, lang: str, **kw) -> str:
    """池 + 语言 → 文案(缺省回退 zh)。kw 供 {field} 等占位。"""
    return (pool.get(lang) or pool["zh"]).format(**kw)
