# -*- coding: utf-8 -*-
"""LINE 采购改错澄清文案(P1E-2 · 本地 4 语池)。

从 line_i18n 拆出(避免其破 500·同 replies._POOLS / line_correct 旧 _CLARIFY 范式)。泰语优先、
自然准确。不把用户随口示例(咖啡 65 等)硬编进文案。语言由调用方按 detect_text_lang 选,缺省回退 zh。
"""

from __future__ import annotations

# 可在 LINE 内直接改的字段标签(填进「问新值」模板)。明细仍在详情页(行级);付款方式可直接改。
FIELD_LABELS = {
    "amount": {"zh": "金额", "th": "ยอดเงิน", "en": "amount", "ja": "金額"},
    "date": {"zh": "日期", "th": "วันที่", "en": "date", "ja": "日付"},
    "seller": {"zh": "卖家", "th": "ร้านค้า", "en": "seller", "ja": "販売者"},
    "category": {"zh": "分类", "th": "หมวดหมู่", "en": "category", "ja": "分類"},
    "payment": {"zh": "付款方式", "th": "วิธีชำระเงิน", "en": "payment method", "ja": "支払方法"},
}

# 验收 #1:笼统说「识别错了/不对」→ 列可改字段,问改哪里(不重拍·不当 OCR 失败)。
CLARIFY_FIELDS = {
    "zh": "我知道你想修改这张记录。你想改金额、日期、卖家、分类、付款方式,还是明细?",
    "th": "ฉันเห็นว่าคุณต้องการแก้รายการนี้ค่ะ ต้องการแก้ส่วนไหน: ยอดเงิน, วันที่, ร้านค้า, หมวดหมู่, วิธีชำระเงิน หรือรายการย่อย?",
    "en": "I see you want to correct this record. Which part should I change: amount, date, seller, category, payment method, or line items?",
    "ja": "この記録を修正したいのですね。どの項目を変更しますか:金額、日付、販売者、分類、支払方法、明細?",
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


DRAFT_EDITED = {
    "zh": "已更新草稿:฿{new},待你确认入账。",
    "th": "อัปเดตฉบับร่างแล้วค่ะ: ฿{new} รอคุณยืนยันบันทึก",
    "en": "Draft updated: ฿{new}, awaiting your confirmation to record.",
    "ja": "下書きを更新しました:฿{new}、記帳の確認待ちです。",
}

# 低风险直接执行后的完成回执(草稿改 date/seller/category):保留卡片查看/撤销入口。
CHANGED_DONE = {
    "zh": "已将{field}改为 {new}。可在上方卡片查看或撤销。",
    "th": "เปลี่ยน{field}เป็น {new} เรียบร้อยแล้วค่ะ ดูหรือยกเลิกได้ที่การ์ดด้านบน",
    "en": "{field} changed to {new}. You can view or undo on the card above.",
    "ja": "{field}を {new} に変更しました。上のカードで確認・取り消しできます。",
}

# 多字段一并改的确认(高风险走确认时·罕见):「把这笔改成 {changes} 吗?」。
CONFIRM_MULTI = {
    "zh": "把这笔改成 {changes} 吗?回复「是」确认。",
    "th": "แก้รายการนี้เป็น {changes} ใช่ไหมคะ? ตอบ 'ใช่' เพื่อยืนยันค่ะ",
    "en": "Change this entry to {changes}? Reply 'yes' to confirm.",
    "ja": "この記録を {changes} に変更しますか?「はい」で確定。",
}


# 多行/明细行级改(总额或某行金额)→ 不在 LINE 猜行,引导详情页。说明原因(多个明细),非泛泛。
MULTILINE_EDIT = {
    "zh": "这张有多条明细。要改总额或某一行的金额,需要先在 Pearnly 详情页核对明细,我带你打开。",
    "th": "รายการนี้มีหลายรายการย่อยค่ะ หากต้องการแก้ยอดรวมหรือยอดของรายการใดรายการหนึ่ง ต้องตรวจรายการย่อยในหน้า Pearnly ก่อน ฉันจะพาไปเปิดให้ค่ะ",
    "en": "This entry has multiple line items. To change the total or a line's amount, please check the line items on the Pearnly detail page first — I'll open it for you.",
    "ja": "この記録には複数の明細があります。合計または特定の明細の金額を変更するには、まず Pearnly の詳細ページで明細をご確認ください。ページを開きます。",
}

# 字段值确认(收到新值后):「把{field}从{old}改成{new}吗?」——不提冲销(草稿/已入账通用)。
CONFIRM_FIELD_CHANGE = {
    "zh": "把{field}从 {old} 改成 {new} 吗?回复「是」确认。",
    "th": "เปลี่ยน{field}จาก {old} เป็น {new} ใช่ไหมคะ? ตอบ 'ใช่' เพื่อยืนยันค่ะ",
    "en": "Change {field} from {old} to {new}? Reply 'yes' to confirm.",
    "ja": "{field}を {old} から {new} に変更しますか?「はい」で確定。",
}


def field_label(field: str, lang: str) -> str:
    return FIELD_LABELS.get(field, {}).get(lang) or FIELD_LABELS.get(field, {}).get("zh", field)


# 字段名(detect_correction_field 的 amount/date/seller/category/payment)→ 规范键(_apply_changes /
# changes dict)。唯一源,反向由它派生(防两份手维护漂移)。
FIELD_TO_KEY = {
    "amount": "amount",
    "date": "doc_date",
    "seller": "vendor_name",
    "category": "category",
    "payment": "payment_method",
}
_KEY_TO_FIELD = {v: k for k, v in FIELD_TO_KEY.items()}


def key_label(key: str, lang: str) -> str:
    return field_label(_KEY_TO_FIELD.get(key, key), lang)


def pay_label(code: str, lang: str) -> str:
    """付款方式码 → 本地化标签(复用卡片同口径 line_card._method_label · 单一源)。"""
    from services.line_binding import line_card, line_card_i18n

    return line_card._method_label(code, line_card_i18n.chrome(lang))


def disp(key: str, value, lang: str) -> str:
    """字段值 → 展示文本(付款方式码本地化成人话·其余原样·回执/确认用)。"""
    if key == "payment_method":
        return pay_label(value, lang)
    return str(value)


def t(pool: dict, lang: str, **kw) -> str:
    """池 + 语言 → 文案(缺省回退 zh)。kw 供 {field} 等占位。"""
    return (pool.get(lang) or pool["zh"]).format(**kw)
