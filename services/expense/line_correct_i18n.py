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

# 目标值已等于当前值(如日期已是 2026-06-18)→ 不 void/不重建/不写审计,诚实告知(验收 #3)。
CHANGED_NOOP = {
    "zh": "{field}已经是 {value} 了,无需修改。",
    "th": "{field}เป็น {value} อยู่แล้วค่ะ ไม่ต้องแก้ไข",
    "en": "The {field} is already {value} — no change needed.",
    "ja": "{field}はすでに {value} です。変更は不要です。",
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


# confirm 阶段收到既非「是」也非「否」的输入 → 重问(不静默取消、不串到旧动作·验收 #1)。
CONFIRM_REPROMPT = {
    "zh": "这次修改还没确认。回复「是」确认,或「取消」放弃。",
    "th": "การแก้ไขนี้ยังไม่ได้ยืนยันค่ะ ตอบ 'ใช่' เพื่อยืนยัน หรือ 'ยกเลิก' เพื่อยกเลิก",
    "en": "This change isn't confirmed yet. Reply 'yes' to confirm or 'cancel' to discard.",
    "ja": "この変更はまだ確定していません。「はい」で確定、「キャンセル」で取り消し。",
}

# 听不懂改什么 → 列可改字段示例(产品化兜底·非报错·验收 #8)。泰语为主、四语补齐。
EDIT_EXAMPLES = {
    "zh": "你可以回复:改日期为 2026-06-18、改店名为 7-11、总额改为 200、分类改为餐饮、付款方式改为 PromptPay。",
    "th": "พิมพ์บอกได้เลยค่ะ เช่น แก้วันที่เป็น 2026-06-18, แก้ร้านค้าเป็น 7-11, แก้ยอดเป็น 200, แก้หมวดหมู่เป็นค่าอาหาร, แก้วิธีชำระเป็น PromptPay",
    "en": "You can reply: change date to 2026-06-18, change seller to 7-11, change total to 200, change category to dining, change payment to PromptPay.",
    "ja": "例:日付を2026-06-18に、店名を7-11に、合計を200に、分類を飲食に、支払方法をPromptPayに変更、と返信できます。",
}


# 05 Slice 1(账务安全):引用的旧卡片底层单据已死/已变 → 诚实文案,绝不悄悄改别的单。
# 已撤销(void·无活后代)→ 不改死单,给「先恢复 / 重记」出路(恢复动作本身留 Slice 2)。
STALE_VOIDED = {
    "zh": "这笔已经撤销了,不能直接改。要先恢复它再改,还是重新记一笔?",
    "th": "รายการนี้ถูกยกเลิกไปแล้ว แก้โดยตรงไม่ได้ค่ะ ต้องการกู้คืนก่อนแล้วค่อยแก้ หรือบันทึกใหม่คะ?",
    "en": "This entry has been cancelled, so it can't be edited directly. Restore it first, or record a new one?",
    "ja": "この記録は取り消し済みのため、直接編集できません。先に復元してから編集しますか、それとも新しく記録しますか?",
}

# 草稿已删(软删/物理删·查不到)→ 不改死单,给「恢复 / 重记」出路。
STALE_DISCARDED = {
    "zh": "这张草稿已经删除了。要恢复它,还是重新记一笔?",
    "th": "ฉบับร่างนี้ถูกลบไปแล้วค่ะ ต้องการกู้คืน หรือบันทึกใหม่คะ?",
    "en": "This draft has been deleted. Restore it, or record a new one?",
    "ja": "この下書きは削除済みです。復元しますか、それとも新しく記録しますか?",
}

# 被引用单已被更正(SUPERSEDED)→ 落到最新活单前的提示前缀(后随确认/问值文案)。
SUPERSEDED_PREFIX = {
    "zh": "这张已更新为 ฿{amt}(记录 #{ref}),我帮你改当前这张。",
    "th": "รายการนี้ถูกอัปเดตเป็น ฿{amt} (รายการ #{ref}) แล้วค่ะ จะแก้ที่รายการล่าสุดให้นะคะ",
    "en": "This was updated to ฿{amt} (record #{ref}); I'll edit the current one.",
    "ja": "この記録は ฿{amt}(記録 #{ref})に更新されています。最新のものを編集します。",
}


# 05 Slice 2(恢复闭环):引用已撤/已删单说「恢复」→ 已撤=克隆重过账成新活单(原死单不动);
# 草稿软删=原地翻回 draft(同一记录·数据完整)。文案对两路通用(「记录 #ref」不写「新」)。
RESTORE_DONE = {
    "zh": "↩️ 已恢复:฿{amt}(记录 #{ref})。可继续在这里改它。",
    "th": "↩️ กู้คืนแล้วค่ะ: ฿{amt} (รายการ #{ref}) แก้ต่อได้เลยค่ะ",
    "en": "↩️ Restored: ฿{amt} (record #{ref}). You can keep editing it here.",
    "ja": "↩️ 復元しました:฿{amt}(記録 #{ref})。このまま編集できます。",
}

# 引用的是活单 → 没被撤销/删除,无需恢复。
RESTORE_NOT_VOIDED = {
    "zh": "这张还在,没有被撤销或删除,不用恢复。",
    "th": "รายการนี้ยังอยู่ ไม่ได้ถูกยกเลิกหรือลบ ไม่ต้องกู้คืนค่ะ",
    "en": "This entry is still here — not cancelled or deleted, no need to restore.",
    "ja": "この記録はまだあります。取り消しも削除もされていないので復元は不要です。",
}

# 引用的单数据已不在(旧版物理删·恢复前的删除)→ 诚实告知不可恢复,引导重记。
RESTORE_GONE = {
    "zh": "这张的数据已经不在了,没法恢复,直接重新记一笔吧。",
    "th": "ข้อมูลรายการนี้ไม่อยู่แล้วค่ะ กู้คืนไม่ได้ บันทึกใหม่ได้เลยนะคะ",
    "en": "This entry's data is no longer available and can't be restored — just record a new one.",
    "ja": "この記録のデータはもう残っておらず復元できません。新しく記録してください。",
}

# 已更正/已恢复过(链上已有更新活单)→ 给当前最新版本,不重复建。
RESTORE_ALREADY = {
    "zh": "这笔已经有最新版本了:记录 #{ref}(฿{amt})。",
    "th": "รายการนี้มีเวอร์ชันล่าสุดอยู่แล้วค่ะ: รายการ #{ref} (฿{amt})",
    "en": "This already has a current version: record #{ref} (฿{amt}).",
    "ja": "この記録には最新版があります:記録 #{ref}(฿{amt})。",
}

# 裸「恢复」没引用具体卡片 → 请引用要恢复的那张。
RESTORE_NEED_QUOTE = {
    "zh": "请长按要恢复的那张卡片,回复「恢复」。",
    "th": "กรุณากดค้างที่การ์ดที่ต้องการกู้คืน แล้วตอบ「กู้คืน」ค่ะ",
    "en": "Please long-press the card you want to restore and reply 'restore'.",
    "ja": "復元したいカードを長押しして「復元」と返信してください。",
}

# 所属期间已结账 → 不能在 LINE 恢复(重过账会触碰已结期),诚实引导网页。
RESTORE_CLOSED = {
    "zh": "这笔所属的账期已结账,无法在这里恢复,请在 Pearnly 网页处理。",
    "th": "งวดบัญชีของรายการนี้ปิดแล้ว ไม่สามารถกู้คืนที่นี่ได้ กรุณาดำเนินการในเว็บ Pearnly ค่ะ",
    "en": "This entry's accounting period is closed, so it can't be restored here — please use the Pearnly web app.",
    "ja": "この記録の会計期間は締め済みのため、ここでは復元できません。Pearnly のウェブでご対応ください。",
}


# 06 Slice 3 强锚定(Anchored Action):引用了一张卡 → 整句只围绕它,绝不另记一笔。
# 看着像新记账 / 裸数字 → 把解析值当建议,问要不要用它更新这张(永不新建支出·{sug} 含金额)。
ANCHOR_SUGGEST_EDIT = {
    "zh": "你发的内容像是 {sug}。要用它更新这张记录(#{ref})吗?可回复:改金额 / 改分类、删除、查看详情。",
    "th": "ข้อความที่ส่งมาดูเหมือน {sug} ค่ะ ต้องการใช้ค่านี้อัปเดตรายการนี้ (#{ref}) ไหมคะ? พิมพ์ได้เลย: แก้ยอด / แก้หมวดหมู่, ลบ, ดูรายละเอียด",
    "en": "What you sent looks like {sug}. Update this record (#{ref}) with it? You can reply: change amount / category, delete, or view details.",
    "ja": "送られた内容は {sug} のようです。この記録(#{ref})をこれで更新しますか?返信できます:金額・分類の変更、削除、詳細表示。",
}

# 引用了一张卡却发来闲聊 / 问候 / 全局查账 / 不明 → 不闲聊不查账,锚定追问要对这张做什么({who}=฿额·卖家)。
ANCHOR_ASK = {
    "zh": "你正在回复这张记录({who})。要对它做什么?可回复:改金额 / 改分类、删除、查看详情。",
    "th": "คุณกำลังตอบกลับรายการนี้ ({who}) ค่ะ ต้องการทำอะไรกับรายการนี้? พิมพ์ได้เลย: แก้ยอด / แก้หมวดหมู่, ลบ, ดูรายละเอียด",
    "en": "You're replying to this record ({who}). What would you like to do with it? You can reply: change amount / category, delete, or view details.",
    "ja": "この記録({who})に返信しています。どうしますか?返信できます:金額・分類の変更、削除、詳細表示。",
}

# 引用过期 / 查不到 / 回复的不是记录卡 → 锚定失效,诚实请用户引用一张票据 / 费用卡(绝不落新单)。
ANCHOR_EXPIRED = {
    "zh": "这条引用已过期,或回复的不是一张记录卡。请长按一张票据 / 费用卡再回复要做的操作。",
    "th": "การอ้างอิงนี้หมดอายุ หรือสิ่งที่ตอบกลับไม่ใช่การ์ดรายการค่ะ กรุณากดค้างที่การ์ดใบเสร็จ / ค่าใช้จ่าย แล้วตอบกลับสิ่งที่ต้องการทำ",
    "en": "This reference has expired, or you replied to something that isn't a record card. Please long-press a receipt / expense card and reply with what you'd like to do.",
    "ja": "この引用は期限切れか、返信先が記録カードではありません。領収書・経費カードを長押ししてから操作を返信してください。",
}


# 06 Slice 4 无引用智能解析:目标不明(≥2 近单 + 指示代词)→ 列候选追问要操作哪张(破坏性永不猜删)。
PICK_WHICH = {
    "zh": "你要操作哪一张?回复序号(如「第2张」)或卖家名即可:",
    "th": "ต้องการจัดการรายการไหนคะ? ตอบลำดับ (เช่น “อันที่ 2”) หรือชื่อร้านได้เลย:",
    "en": 'Which record do you mean? Reply with the number (e.g. "2") or the seller name:',
    "ja": "どの記録ですか?番号(例:「2」)または販売者名で返信してください:",
}

# 删/撤/改但近期没有可操作的 LINE 记录 → 诚实告知(不猜不误删)。
PICK_NONE = {
    "zh": "目前没有可操作的记录。",
    "th": "ตอนนี้ยังไม่มีรายการให้จัดการค่ะ",
    "en": "There's no record to act on right now.",
    "ja": "現在、操作できる記録はありません。",
}


# 06 Phase B-1 学习按钮:改分类成功后追发一条,问要不要把这次修正沉淀成规则。
LEARN_ASK = {
    "zh": "要我记住这次的分类吗?",
    "th": "ให้จำหมวดหมู่นี้ไว้ไหมคะ?",
    "en": "Want me to remember this category?",
    "ja": "この分類を覚えますか?",
}
LEARN_BTN_ONCE = {"zh": "仅这次", "th": "เฉพาะครั้งนี้", "en": "Just this once", "ja": "今回のみ"}
LEARN_BTN_VENDOR = {
    "zh": "以后「{vendor}」都记{cat}",
    "th": "「{vendor}」ลง{cat}ตลอด",
    "en": '"{vendor}" → {cat} from now',
    "ja": "今後「{vendor}」は{cat}",
}
LEARN_BTN_WS = {
    "zh": "这个套账都这样",
    "th": "ทั้งบัญชีนี้เลย",
    "en": "All in this book",
    "ja": "この帳簿すべて",
}

# 点按钮后的确认回执(诚实告知存了什么规则)。
LEARN_ONCE = {
    "zh": "好的,仅这次。",
    "th": "ได้ค่ะ เฉพาะครั้งนี้",
    "en": "Okay, just this once.",
    "ja": "了解です、今回のみ。",
}
LEARN_VENDOR = {
    "zh": "记住啦,以后「{vendor}」都记「{cat}」。",
    "th": "จำแล้วค่ะ ต่อไป「{vendor}」จะลง「{cat}」ให้",
    "en": 'Got it — "{vendor}" will go to "{cat}" from now on.',
    "ja": "覚えました。今後「{vendor}」は「{cat}」にします。",
}
LEARN_WS = {
    "zh": "记住啦,这个套账以后「{item}」都记「{cat}」。",
    "th": "จำแล้วค่ะ ในบัญชีนี้ต่อไป「{item}」จะลง「{cat}」",
    "en": 'Got it — "{item}" will go to "{cat}" in this book.',
    "ja": "覚えました。この帳簿では今後「{item}」を「{cat}」にします。",
}
# 令牌已消费/失效(重复点同一组按钮)→ 友好幂等提示,不重复写规则。
LEARN_STALE = {
    "zh": "这个选择已经处理过了。",
    "th": "ตัวเลือกนี้ดำเนินการไปแล้วค่ะ",
    "en": "This choice was already handled.",
    "ja": "この選択は処理済みです。",
}


# 用户改/教的分类词对不上科目树任何准确科目 → 诚实告知先记「其他」、可再改(不静默落其他)。
CAT_FALLBACK_OTHER = {
    "zh": "没找到完全对应的科目,先记到「其他」了,你可以随时再改。",
    "th": "ยังไม่พบหมวดหมู่ที่ตรงพอดี จึงบันทึกไว้ที่ “อื่น ๆ” ก่อน แก้ไขภายหลังได้ค่ะ",
    "en": 'No exact category match — recorded under "Other" for now; you can change it anytime.',
    "ja": "ぴったりの科目が見つからず、ひとまず「その他」に記録しました。いつでも変更できます。",
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


def short_ref(doc_id) -> str:
    """单据短记录号(末 6 位·与卡片 _short_id 同口径)。填 {ref} 占位(恢复/被更正提示共用)。"""
    from services.line_binding import line_card

    return line_card._short_id(doc_id)


def money(v) -> str:
    """金额展示文本(千分位 2 位·฿ 前缀由文案模板加)。填 {amt} 占位(恢复/被更正提示共用)。"""
    from decimal import Decimal

    return f"{Decimal(str(v or 0)):,.2f}"


def disp(key: str, value, lang: str) -> str:
    """字段值 → 展示文本(付款方式码本地化成人话·日期转佛历票面口径·其余原样·回执/确认用)。"""
    if key == "payment_method":
        return pay_label(value, lang)
    if key in ("doc_date", "date"):
        from core.thai_date import buddhist_display

        return buddhist_display(value)
    return str(value)


def t(pool: dict, lang: str, **kw) -> str:
    """池 + 语言 → 文案(缺省回退 zh)。kw 供 {field} 等占位。"""
    return (pool.get(lang) or pool["zh"]).format(**kw)
