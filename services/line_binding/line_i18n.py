# -*- coding: utf-8 -*-
"""LINE Bot 多语言文案字典 + 取词器(zh/en/th/ja · 纯数据叶子)。

语气标准(P1E-1·主路径文案系统):专业会计助理,温和不冷、克制不啰嗦;每条回复有明确任务、
先回应意图再给下一步、适当带上下文、失败给恢复路径、高风险动作要求明确对象、不承诺聊天里做不到
的事。泰语优先(先写泰语再 zh/en/ja,不中文直译),泰语统一用偏温和专业的 ค่ะ/นะคะ,不混 ครับ。
OCR 场景文案在 line_ocr_i18n(此处 re-export 保 line_client 契约)。
"""

from typing import Optional

# OCR 场景文案抽到 line_ocr_i18n(保本文件 <500)· re-export 保 line_client.t_ocr/OCR_RESULT_I18N 契约。
from services.line_binding.line_ocr_i18n import OCR_RESULT_I18N, t_ocr  # noqa: F401

DEFAULT_LANG = "th"  # 主市场泰国 · 未知语言兜底(单一来源 · 改市场只动这里)

LINE_I18N = {
    "zh": {
        "bind_invalid": "❌ 绑定码无效或已过期\n请回 pearnly.com 重新获取",
        "bind_conflict": (
            "❌ 绑定失败 · 此 LINE 账号可能已绑到其他 Pearnly 用户\n请先在原账号解绑再试"
        ),
        "bind_success": (
            "✅ 绑定成功\n\n"
            "Pearnly 账号:{username}\n"
            "LINE:{display_name}\n\n"
            "现在可以发送收据或税票照片让我读取,"
            "也可以直接输入一笔费用,例如日期、商家、金额和用途。"
        ),
        "need_bind": (
            "你好,我是 Pearnly 采购与费用助理。先绑定账号即可开始:\n"
            "1. 登录 https://pearnly.com\n"
            "2. 打开「集成 → LINE Bot」获取 6 位绑定码\n"
            "3. 把绑定码发给我\n"
            "绑定后,你可以发送票据让我读取,或直接输入费用记录。"
        ),
        "image_not_bound": (
            "你还没有绑定 Pearnly 账号。\n"
            "请到 pearnly.com「集成 → LINE Bot」获取 6 位绑定码并发给我,绑定后即可开始读取票据。"
        ),
        "unsupported": (
            "我可以读取票据文件:图片、PDF、Excel、CSV、Word 或 TXT。\n"
            "你也可以直接输入一笔费用,例如日期、商家、金额和用途。"
        ),
        "exp_need_amount": "这笔金额是多少?直接回复一个数字即可,例如「50」。",
        "exp_income_guide": (
            "这看起来是一笔收入(收款或卖出)。LINE 目前只处理支出和采购,收入请在 Pearnly 网页记账。\n"
            "如果这其实是一笔支出,请补充「买」或「付」等说明后再发一次。"
        ),
        "exp_sum_head": "📊 本月已入账 ฿{amount} · 共 {n} 笔",
        "exp_sum_empty": "本月还没有已入账的支出。你可以发送一张票据,或输入一笔费用开始记录。",
        "exp_undo_done": "↩️ 已撤销上一笔 · ฿{amount}",
        "exp_undo_none": "没有找到可撤销的记录(只能撤销已入账的上一笔)。",
        "exp_correct_confirm": "把上一笔 ฿{old} 改成 ฿{new} 吗?回复「是」确认(会冲销原单并按新值重记)。",
        "exp_correct_none": "没有可更正的已入账记录(只能更正最近一笔)。",
        "exp_correct_cancel": "已取消更正,原记录保持不变。",
        "exp_correct_posted": "已更正:原单已冲销,新单 ฿{new} 已入账(可撤销)。",
        "exp_correct_draft": "已更正:原单已冲销,新草稿 ฿{new} 待你确认入账。",
        "exp_correct_confirm2": "把这笔改成 {changes} 吗?回复「是」确认(会冲销原单并重记)。",
        "guide_detail_list": "你可以输入「查明细」查看最近记录,然后按序号操作,例如「第 [序号] 笔金额改为 [金额]」。",
        "exp_correct_closed": "这笔所在账期已结账或已申报,无法在这里修改。请到 pearnly.com 采购里处理(已结期会自动红冲,账目不受影响)。",
        "exp_uncat": "未分类",
        "exp_q_not_found": "这个我暂时没有现成答案。你可以换个问法,或直接发送一张票据让我记录。",
        "exp_q_source": "来源:{src}",
        "exp_ack_posted": "✅ 费用已入账 · {amount} THB",
        "exp_ack_confirm": "✅ 已保存费用草稿 · {amount} THB",
        "exp_ack_dup": "⚠️ 可能重复 · {amount} THB · 请核对",
        "card_confirmed": "✅ 费用已入账 · {amount} THB",
        "card_state_void_desc": "这笔记录已撤销,操作记录仍会保留。",
        "card_state_discarded_desc": "这笔草稿已丢弃。",
        "card_action_stale": "这张已处理过或已变更 · 到 pearnly.com 查看",
        "card_action_expired": "这张卡片已过期 · 请重发或到 pearnly.com 操作",
        "qr_record": "记一笔",
        "qr_query": "本月花多少",
        "qr_query_text": "本月花了多少",
        "line_intro_capability": (
            "我可以帮你处理这个账套的采购和费用。\n\n"
            "在 LINE 里,我可以:\n"
            "- 读取收据、税票和费用文件\n"
            "- 整理成采购或费用记录,供你核对\n"
            "- 对指定记录进行确认、修改、丢弃或撤销\n"
            "- 查看费用汇总和最近明细\n\n"
            "如果涉及多行明细、税务、公司资料或重要单据,我会带你打开 Pearnly 的对应页面继续处理。"
        ),
        "line_greeting": (
            "你好,我可以帮你处理采购和费用。\n" "你可以发送票据、费用文件,或告诉我想查看什么。"
        ),
        "line_start_hint": (
            "可以这样开始:\n"
            "你可以直接发送收据或费用文件,我会读取并整理。\n"
            "如果想用文字记录,请告诉我日期、商家、金额和用途。"
        ),
        "line_upload_hint": (
            "你可以发送收据、税票或费用文件,图片、PDF 都可以。\n"
            "拍摄时请尽量完整、清晰,看清金额和日期,识别会更准。"
        ),
        "line_processing_receipt": "已收到文件,我正在读取金额、日期、卖方、VAT 和明细,稍后给你核对。",
        "line_ocr_failed_recovery": (
            "这张单据我还没有读完整。\n"
            "你可以重新发送一张完整、清晰、无遮挡的照片,尤其要看清金额和日期。\n\n"
            "如果想先记录,也可以直接输入日期、商家、金额和用途。"
        ),
        "line_not_receipt_recovery": (
            "这条内容看起来还不像票据或费用记录。\n"
            "你可以发送费用文件,或直接输入要记录的费用信息。"
        ),
        "line_need_reply_record": (
            "为避免操作错记录,请先长按要处理的那条 Pearnly 记录,选择「回复」,\n"
            "再输入要执行的操作,例如「删除」或「修改金额为 …」。"
        ),
        "line_web_handoff": (
            "这一步需要在 Pearnly 页面里完整核对。\n" "我会带你打开正确页面继续处理。"
        ),
        "line_unknown_intent": (
            "我还不确定你想处理什么。\n" "你可以发送票据、查看最近记录,或查询费用汇总。"
        ),
        "line_out_of_scope": "我主要负责记账和费用。你可以发送票据,或查询本月费用情况。",
        "line_date_answer": "今天是 {date}。需要的话把票据发我,或直接打字记一笔费用就行。",
        "line_query_summary_intro": (
            "这是根据已记录数据整理的费用汇总。\n"
            "我会显示总额、记录数和主要分类;如果想看每一笔,可以继续查看明细。"
        ),
        "line_query_detail_intro": (
            "这是我找到的最近记录。\n"
            "如果要修改、丢弃或撤销其中某一笔,请先回复对应记录,避免操作错单。"
        ),
    },
    "en": {
        "bind_invalid": "❌ Invalid or expired code\nGet a new one at pearnly.com",
        "bind_conflict": (
            "❌ Binding failed · this LINE account may already be bound to another Pearnly user\n"
            "Please unbind from the original account first"
        ),
        "bind_success": (
            "✅ Linked successfully\n\n"
            "Pearnly account: {username}\n"
            "LINE: {display_name}\n\n"
            "You can now send a receipt or tax invoice photo for me to read, "
            "or type an expense with the date, vendor, amount, and purpose."
        ),
        "need_bind": (
            "Hello, I'm Pearnly, your purchasing and expense assistant. Link your account to start:\n"
            "1. Log in at https://pearnly.com\n"
            "2. Open 'Integrations → LINE Bot' for your 6-digit code\n"
            "3. Send the code to me\n"
            "Once linked, you can send documents for me to read, or type an expense entry."
        ),
        "image_not_bound": (
            "Your Pearnly account isn't linked yet.\n"
            "Get a 6-digit code at pearnly.com 'Integrations → LINE Bot' and send it to me to start reading documents."
        ),
        "unsupported": (
            "I can read expense documents: images, PDF, Excel, CSV, Word, or TXT.\n"
            "You can also type an expense with the date, vendor, amount, and purpose."
        ),
        "exp_need_amount": "How much was it? Just reply with a number, e.g. '50'.",
        "exp_income_guide": (
            "This looks like income (a sale or money received). LINE currently handles expenses "
            "and purchases only — please record income in Pearnly on the web.\n"
            "If it's actually a purchase, resend it with a word like 'bought' or 'paid'."
        ),
        "exp_sum_head": "📊 Recorded this month: ฿{amount} · {n} entries",
        "exp_sum_empty": "No recorded spending this month yet. Send a document, or type an expense to start.",
        "exp_undo_done": "↩️ Undid your last entry · ฿{amount}",
        "exp_undo_none": "No entry to undo (only the last recorded one can be undone).",
        "exp_correct_confirm": "Change the last entry from ฿{old} to ฿{new}? Reply 'yes' to confirm (the original is voided and re-recorded at the new value).",
        "exp_correct_none": "No recorded entry to correct (only the most recent one can be changed).",
        "exp_correct_cancel": "Correction cancelled — the original entry is unchanged.",
        "exp_correct_posted": "Corrected: original voided, new entry ฿{new} recorded (undoable).",
        "exp_correct_draft": "Corrected: original voided, new draft ฿{new} awaiting your confirmation.",
        "exp_correct_confirm2": "Change this entry to {changes}? Reply 'yes' to confirm (the original is voided and re-recorded).",
        "guide_detail_list": "You can type 'show details' to see recent entries, then refer to one by number, such as 'change item [number] to [amount]'.",
        "exp_correct_closed": "This entry's period is already closed or filed, so it can't be changed here. Please handle it at pearnly.com under Purchases (closed periods are reversed cleanly, books stay intact).",
        "exp_uncat": "Uncategorized",
        "exp_q_not_found": "I don't have a ready answer for that. Try rephrasing, or send a document and I'll record it.",
        "exp_q_source": "Source: {src}",
        "exp_ack_posted": "✅ Expense recorded · {amount} THB",
        "exp_ack_confirm": "✅ Expense draft saved · {amount} THB",
        "exp_ack_dup": "⚠️ Possible duplicate · {amount} THB · please check",
        "card_confirmed": "✅ Expense recorded · {amount} THB",
        "card_state_void_desc": "This entry has been voided. The audit trail is kept.",
        "card_state_discarded_desc": "This draft has been discarded.",
        "card_action_stale": "Already handled or changed · view at pearnly.com",
        "card_action_expired": "This card has expired · resend it or use pearnly.com",
        "qr_record": "Record",
        "qr_query": "This month",
        "qr_query_text": "how much this month",
        "line_intro_capability": (
            "I can help manage purchases and expenses for this workspace.\n\n"
            "In LINE, I can:\n"
            "- Read receipts, tax invoices, and expense documents\n"
            "- Prepare purchase or expense entries for review\n"
            "- Confirm, edit, discard, or void a specific entry\n"
            "- Show expense summaries and recent records\n\n"
            "For details that need careful review, such as multiple line items, tax fields, "
            "company information, or important documents, I'll take you to the right page in Pearnly."
        ),
        "line_greeting": (
            "Hello. I can help with purchases and expenses.\n"
            "You can send a document, an expense, or tell me what you want to check."
        ),
        "line_start_hint": (
            "You can start in two ways:\n"
            "Send a receipt or expense document for me to read, "
            "or type the date, vendor, amount, and purpose of the expense."
        ),
        "line_upload_hint": (
            "You can send receipts, tax invoices, or expense files — images or PDF.\n"
            "Capture the full document clearly, with the amount and date visible, for the best accuracy."
        ),
        "line_processing_receipt": (
            "Document received. I'm reading the amount, date, vendor, VAT, and line items for your review."
        ),
        "line_ocr_failed_recovery": (
            "I couldn't read this document completely.\n"
            "Please try another photo with the full document visible, good lighting, no blur, "
            "and no shadow over the amount or date.\n\n"
            "If you want to record it first, you can type the date, vendor, amount, and purpose."
        ),
        "line_not_receipt_recovery": (
            "This doesn't look like a receipt or expense entry yet.\n"
            "You can send an expense document, or type the expense details you want to record."
        ),
        "line_need_reply_record": (
            "To avoid changing the wrong entry, long-press the Pearnly record, tap “Reply”,\n"
            "then type the action — for example “delete” or “change amount to …”."
        ),
        "line_web_handoff": (
            "This step should be reviewed in Pearnly so you can see all details clearly.\n"
            "I'll take you to the right page to continue."
        ),
        "line_unknown_intent": (
            "I'm not sure what you'd like to do yet.\n"
            "You can send a document, ask for recent records, or check an expense summary."
        ),
        "line_out_of_scope": "I focus on bookkeeping and expenses. You can send a document or ask about your spending.",
        "line_date_answer": "Today is {date}. Send me a receipt, or just type an expense to record it.",
        "line_query_summary_intro": (
            "Here is the expense summary based on recorded entries.\n"
            "I'll show the total, number of records, and main categories. "
            "You can ask for details to see each entry."
        ),
        "line_query_detail_intro": (
            "Here are the recent records I found.\n"
            "To edit, discard, or void one of them, please reply to the exact record first "
            "so I don't act on the wrong entry."
        ),
    },
    "th": {
        "bind_invalid": "❌ รหัสไม่ถูกต้องหรือหมดอายุ\nกรุณารับรหัสใหม่ที่ pearnly.com",
        "bind_conflict": (
            "❌ ผูกบัญชีไม่สำเร็จ · LINE นี้อาจถูกผูกกับ Pearnly บัญชีอื่นแล้ว\n"
            "กรุณายกเลิกที่บัญชีเดิมก่อน"
        ),
        "bind_success": (
            "✅ ผูกบัญชีสำเร็จค่ะ\n\n"
            "บัญชี Pearnly: {username}\n"
            "LINE: {display_name}\n\n"
            "ตอนนี้ส่งรูปใบเสร็จหรือใบกำกับภาษีมาให้ฉันอ่านได้เลยค่ะ "
            "หรือพิมพ์รายการค่าใช้จ่าย พร้อมวันที่ ร้านค้า ยอดเงิน และรายละเอียดก็ได้"
        ),
        "need_bind": (
            "สวัสดีค่ะ ฉันคือ Pearnly ผู้ช่วยงานจัดซื้อและค่าใช้จ่าย ผูกบัญชีก่อนเริ่มใช้งานได้เลยค่ะ\n"
            "1. เข้าสู่ระบบที่ https://pearnly.com\n"
            "2. เปิด 'การเชื่อมต่อ → LINE Bot' รับรหัส 6 หลัก\n"
            "3. ส่งรหัสมาให้ฉัน\n"
            "หลังผูกบัญชีแล้ว ส่งเอกสารมาให้อ่าน หรือพิมพ์บันทึกค่าใช้จ่ายได้เลยค่ะ"
        ),
        "image_not_bound": (
            "ยังไม่ได้ผูกบัญชี Pearnly ค่ะ\n"
            "ไปที่ pearnly.com 'การเชื่อมต่อ → LINE Bot' รับรหัส 6 หลักแล้วส่งมา เพื่อเริ่มอ่านเอกสารได้เลยค่ะ"
        ),
        "unsupported": (
            "ฉันอ่านเอกสารค่าใช้จ่ายได้ค่ะ: รูปภาพ, PDF, Excel, CSV, Word หรือ TXT\n"
            "หรือจะพิมพ์รายการค่าใช้จ่าย พร้อมวันที่ ร้านค้า ยอดเงิน และรายละเอียดก็ได้ค่ะ"
        ),
        "exp_need_amount": "รายการนี้กี่บาทคะ? พิมพ์ตัวเลขกลับมาได้เลยค่ะ เช่น '50'",
        "exp_income_guide": (
            "ดูเหมือนจะเป็นรายรับ (ขายได้หรือรับเงิน) ค่ะ ตอนนี้ LINE ดูแลเฉพาะรายจ่ายและการซื้อ "
            "กรุณาบันทึกรายรับที่หน้าเว็บ Pearnly นะคะ\n"
            "หากนี่คือรายจ่ายจริง พิมพ์ใหม่พร้อมคำว่า 'ซื้อ' หรือ 'จ่าย' ได้เลยค่ะ"
        ),
        "exp_sum_head": "📊 บันทึกเดือนนี้ ฿{amount} · {n} รายการ",
        "exp_sum_empty": "เดือนนี้ยังไม่มีรายการที่บันทึกค่ะ ส่งเอกสารหรือพิมพ์รายการค่าใช้จ่ายเพื่อเริ่มได้เลย",
        "exp_undo_done": "↩️ ยกเลิกรายการล่าสุดแล้วค่ะ · ฿{amount}",
        "exp_undo_none": "ไม่พบรายการให้ยกเลิกค่ะ (ยกเลิกได้เฉพาะรายการล่าสุดที่บันทึกแล้ว)",
        "exp_correct_confirm": "แก้รายการล่าสุดจาก ฿{old} เป็น ฿{new} ไหมคะ? ตอบ 'ใช่' เพื่อยืนยัน (จะยกเลิกใบเดิมและบันทึกใหม่ตามยอดใหม่)",
        "exp_correct_none": "ไม่มีรายการที่บันทึกแล้วให้แก้ค่ะ (แก้ได้เฉพาะรายการล่าสุด)",
        "exp_correct_cancel": "ยกเลิกการแก้ไขแล้วค่ะ รายการเดิมไม่เปลี่ยนแปลง",
        "exp_correct_posted": "แก้ไขแล้วค่ะ: ยกเลิกใบเดิม บันทึกใหม่ ฿{new} แล้ว (ยกเลิกได้)",
        "exp_correct_draft": "แก้ไขแล้วค่ะ: ยกเลิกใบเดิม สร้างฉบับร่าง ฿{new} รอคุณยืนยันบันทึก",
        "exp_correct_confirm2": "แก้รายการนี้เป็น {changes} ไหมคะ? ตอบ 'ใช่' เพื่อยืนยัน (จะยกเลิกใบเดิมและบันทึกใหม่)",
        "guide_detail_list": "พิมพ์ 'ดูรายการ' เพื่อดูรายการล่าสุด แล้วเลือกแก้ไขตามลำดับได้ค่ะ เช่น 'รายการที่ [ลำดับ] แก้ยอดเป็น [จำนวนเงิน]'",
        "exp_correct_closed": "รายการนี้อยู่ในงวดที่ปิดหรือยื่นแล้ว แก้ที่นี่ไม่ได้ค่ะ กรุณาจัดการที่ pearnly.com เมนูจัดซื้อ (งวดที่ปิดจะกลับรายการให้ บัญชีไม่กระทบ)",
        "exp_uncat": "ยังไม่จัดหมวด",
        "exp_q_not_found": "เรื่องนี้ฉันยังไม่มีคำตอบสำเร็จค่ะ ลองถามใหม่ หรือส่งเอกสารมาให้ฉันบันทึกได้เลยค่ะ",
        "exp_q_source": "ที่มา: {src}",
        "exp_ack_posted": "✅ บันทึกค่าใช้จ่ายแล้ว · {amount} THB",
        "exp_ack_confirm": "✅ บันทึกฉบับร่างแล้ว · {amount} THB",
        "exp_ack_dup": "⚠️ อาจซ้ำ · {amount} THB · โปรดตรวจสอบ",
        "card_confirmed": "✅ บันทึกค่าใช้จ่ายแล้ว · {amount} THB",
        "card_state_void_desc": "รายการนี้ถูกยกเลิกแล้ว และยังเก็บประวัติไว้ตรวจสอบได้ค่ะ",
        "card_state_discarded_desc": "ร่างรายการนี้ถูกลบแล้วค่ะ",
        "card_action_stale": "รายการนี้จัดการแล้วหรือมีการเปลี่ยนแปลง · ดูที่ pearnly.com",
        "card_action_expired": "การ์ดนี้หมดอายุแล้ว · กรุณาส่งใหม่หรือใช้งานที่ pearnly.com",
        "qr_record": "บันทึกค่าใช้จ่าย",
        "qr_query": "เดือนนี้เท่าไหร่",
        "qr_query_text": "เดือนนี้จ่ายไปเท่าไหร่",
        "line_intro_capability": (
            "ฉันช่วยดูแลงานซื้อและค่าใช้จ่ายของธุรกิจนี้ได้ค่ะ\n\n"
            "สิ่งที่ทำใน LINE ได้:\n"
            "- อ่านใบเสร็จ ใบกำกับภาษี และเอกสารค่าใช้จ่าย\n"
            "- สร้างรายการซื้อหรือค่าใช้จ่ายให้ตรวจสอบ\n"
            "- ยืนยัน แก้ไข ทิ้ง หรือยกเลิกรายการที่เกี่ยวข้อง\n"
            "- ดูสรุปค่าใช้จ่ายและรายการล่าสุด\n\n"
            "ถ้างานนั้นต้องตรวจรายละเอียด เช่น หลายรายการย่อย ภาษี ข้อมูลบริษัท หรือเอกสารสำคัญ "
            "ฉันจะพาไปที่หน้า Pearnly ที่ถูกต้องค่ะ"
        ),
        "line_greeting": (
            "สวัสดีค่ะ ฉันพร้อมช่วยดูแลรายการซื้อและค่าใช้จ่ายค่ะ\n"
            "ส่งใบเสร็จ เอกสารค่าใช้จ่าย หรือบอกสิ่งที่ต้องการตรวจสอบได้เลยค่ะ"
        ),
        "line_start_hint": (
            "เริ่มได้ง่าย ๆ ค่ะ\n"
            "คุณสามารถส่งรูปใบเสร็จหรือเอกสารค่าใช้จ่ายมาให้ฉันอ่านได้เลย\n"
            "ถ้าต้องการบันทึกจากข้อความ กรุณาบอกวันที่ ร้านค้า ยอดเงิน และรายละเอียดค่าใช้จ่ายค่ะ"
        ),
        "line_upload_hint": (
            "ส่งใบเสร็จ ใบกำกับภาษี หรือไฟล์ค่าใช้จ่ายมาได้เลยค่ะ จะเป็นรูปภาพหรือ PDF ก็ได้\n"
            "ถ่ายให้เห็นเต็มใบ ชัดเจน เห็นยอดเงินและวันที่ จะอ่านได้แม่นยำขึ้นค่ะ"
        ),
        "line_processing_receipt": "ได้รับเอกสารแล้วค่ะ กำลังอ่านยอด วันที่ ผู้ขาย VAT และรายการย่อยให้คุณตรวจสอบ",
        "line_ocr_failed_recovery": (
            "ฉันยังอ่านข้อมูลจากเอกสารนี้ได้ไม่ครบค่ะ\n"
            "กรุณาลองส่งรูปที่เห็นทั้งใบ แสงชัด ไม่เบลอ และไม่มีเงาบังยอดเงินหรือวันที่\n\n"
            "ถ้าต้องการบันทึกไว้ก่อน คุณสามารถพิมพ์วันที่ ร้านค้า ยอดเงิน และรายละเอียดค่าใช้จ่ายได้ค่ะ"
        ),
        "line_not_receipt_recovery": (
            "ข้อความนี้ยังดูไม่เหมือนใบเสร็จหรือรายการค่าใช้จ่ายค่ะ\n"
            "คุณสามารถส่งรูปเอกสารค่าใช้จ่าย หรือพิมพ์รายละเอียดรายการที่ต้องการบันทึกได้ค่ะ"
        ),
        "line_need_reply_record": (
            "เพื่อป้องกันการแก้ผิดรายการ กรุณากดค้างที่ข้อความรายการของ Pearnly เลือก “ตอบกลับ”\n"
            "แล้วพิมพ์สิ่งที่ต้องการ เช่น “ลบ” หรือ “แก้ไข …” ค่ะ"
        ),
        "line_web_handoff": (
            "ขั้นตอนนี้ควรตรวจในหน้า Pearnly เพื่อให้เห็นรายละเอียดครบถ้วนค่ะ\n"
            "ฉันจะพาไปยังหน้าที่ถูกต้องเพื่อดำเนินการต่อ"
        ),
        "line_unknown_intent": (
            "ฉันยังไม่แน่ใจว่าคุณต้องการทำอะไรค่ะ\n"
            "คุณสามารถส่งใบเสร็จให้ฉันอ่าน ขอรายละเอียดรายการล่าสุด หรือถามสรุปค่าใช้จ่ายได้ค่ะ"
        ),
        "line_out_of_scope": "ฉันดูแลเรื่องบันทึกบัญชีและค่าใช้จ่ายเป็นหลักค่ะ ส่งใบเสร็จหรือถามยอดค่าใช้จ่ายได้เลยนะคะ",
        "line_date_answer": "วันนี้คือ {date} ค่ะ ส่งใบเสร็จหรือพิมพ์รายการค่าใช้จ่ายมาบันทึกต่อได้เลยนะคะ",
        "line_query_summary_intro": (
            "นี่คือสรุปค่าใช้จ่ายตามข้อมูลที่บันทึกไว้ค่ะ\n"
            "แสดงยอดรวม จำนวนรายการ และหมวดหมู่หลัก หากต้องการดูทีละรายการ ให้พิมพ์ขอดูรายละเอียดได้เลยค่ะ"
        ),
        "line_query_detail_intro": (
            "นี่คือรายการล่าสุดที่พบค่ะ\n"
            "หากต้องการแก้ไข ทิ้ง หรือยกเลิกรายการใด กรุณาตอบกลับข้อความของรายการนั้นก่อน "
            "เพื่อให้ฉันไม่ดำเนินการผิดรายการค่ะ"
        ),
    },
    "ja": {
        "bind_invalid": "❌ コードが無効または期限切れです\npearnly.com で新しいコードを取得してください",
        "bind_conflict": (
            "❌ 紐付け失敗 · この LINE は別の Pearnly アカウントに紐付け済みの可能性があります\n"
            "元のアカウントで先に解除してください"
        ),
        "bind_success": (
            "✅ 連携完了\n\n"
            "Pearnly アカウント: {username}\n"
            "LINE: {display_name}\n\n"
            "領収書や税金請求書の写真を送って読み取らせるか、"
            "日付、店舗、金額、用途を入力して経費を記録できます。"
        ),
        "need_bind": (
            "こんにちは。仕入れと経費のアシスタント Pearnly です。まずアカウント連携をしてください。\n"
            "1. https://pearnly.com にログイン\n"
            "2. 「連携 → LINE Bot」で 6 桁コードを取得\n"
            "3. コードを送信\n"
            "連携後は、書類を送って読み取らせるか、経費を入力して記録できます。"
        ),
        "image_not_bound": (
            "Pearnly アカウントが未連携です。\n"
            "pearnly.com「連携 → LINE Bot」で 6 桁コードを取得して送信すると、書類の読み取りを開始できます。"
        ),
        "unsupported": (
            "経費書類を読み取れます: 画像、PDF、Excel、CSV、Word、TXT。\n"
            "日付、店舗、金額、用途を入力して経費を記録することもできます。"
        ),
        "exp_need_amount": "いくらでしたか?数字だけ返信してください(例:50)。",
        "exp_income_guide": (
            "これは収入(売上または入金)のようです。LINE は現在、支出と仕入れのみを扱います。"
            "収入は Pearnly の Web で記録してください。\n"
            "もし支出であれば、「購入」や「支払」を付けて再送してください。"
        ),
        "exp_sum_head": "📊 今月の記帳 ฿{amount} · {n} 件",
        "exp_sum_empty": "今月まだ記帳がありません。書類を送るか、経費を入力して記録を始めてください。",
        "exp_undo_done": "↩️ 直近の記帳を取り消しました · ฿{amount}",
        "exp_undo_none": "取り消せる記帳が見つかりません(直近の記帳のみ取消可)。",
        "exp_correct_confirm": "直近の記帳を ฿{old} から ฿{new} に変更しますか?「はい」で確定(元の伝票を無効化し新しい金額で再記帳します)。",
        "exp_correct_none": "修正できる記帳がありません(直近の1件のみ変更可)。",
        "exp_correct_cancel": "修正をキャンセルしました。元の記帳は変わりません。",
        "exp_correct_posted": "修正完了:元伝票を無効化、新規 ฿{new} を記帳(取消可)。",
        "exp_correct_draft": "修正完了:元伝票を無効化、下書き ฿{new} を確認待ち。",
        "exp_correct_confirm2": "この記録を {changes} に変更しますか?「はい」で確定(元伝票を無効化し記帳し直します)。",
        "guide_detail_list": "「明細を表示」と入力すると最近の記録を確認できます。その後「[番号] 番の金額を [金額] に変更」のように指定できます。",
        "exp_correct_closed": "この記録の会計期間は締めまたは申告済みのため、ここでは変更できません。pearnly.com の仕入で処理してください(締め期間は自動で赤伝、帳簿は影響を受けません)。",
        "exp_uncat": "未分類",
        "exp_q_not_found": "その件はまだ用意できた答えがありません。言い換えるか、書類を送っていただければ記帳します。",
        "exp_q_source": "出典:{src}",
        "exp_ack_posted": "✅ 費用を記帳しました · {amount} THB",
        "exp_ack_confirm": "✅ 費用の下書きを保存しました · {amount} THB",
        "exp_ack_dup": "⚠️ 重複の可能性 · {amount} THB · ご確認ください",
        "card_confirmed": "✅ 費用を記帳しました · {amount} THB",
        "card_state_void_desc": "この記録は取消済みです。操作履歴は保持されます。",
        "card_state_discarded_desc": "この下書きは破棄されました。",
        "card_action_stale": "処理済みまたは変更されています · pearnly.com でご確認ください",
        "card_action_expired": "このカードは期限切れです · 再送するか pearnly.com で操作してください",
        "qr_record": "記録する",
        "qr_query": "今月いくら",
        "qr_query_text": "今月いくら使った",
        "line_intro_capability": (
            "このワークスペースの仕入れと経費処理をお手伝いできます。\n\n"
            "LINE では次のことができます。\n"
            "- レシート、税金請求書、経費書類の読み取り\n"
            "- 仕入れ・経費記録の作成と確認\n"
            "- 指定した記録の確認、修正、破棄、取消\n"
            "- 経費サマリーや最近の明細の確認\n\n"
            "明細が多い場合、税務項目、会社情報、重要書類の確認が必要な場合は、"
            "Pearnly の該当ページへ案内します。"
        ),
        "line_greeting": (
            "こんにちは。仕入れや経費処理をお手伝いできます。\n"
            "書類や経費内容を送るか、確認したいことを入力してください。"
        ),
        "line_start_hint": (
            "次のどちらかで始められます。\n"
            "レシートや経費書類を送るか、日付、店舗、金額、用途を入力してください。"
        ),
        "line_upload_hint": (
            "レシート、税金請求書、経費ファイルを送ってください。画像でも PDF でも大丈夫です。\n"
            "書類全体が写り、金額と日付が見えるよう鮮明に撮ると、より正確に読み取れます。"
        ),
        "line_processing_receipt": "書類を受け取りました。金額、日付、取引先、VAT、明細を読み取っています。",
        "line_ocr_failed_recovery": (
            "この書類を完全には読み取れませんでした。\n"
            "全体が写り、明るく、ぼやけや影で金額や日付が隠れていない写真をもう一度送ってください。\n\n"
            "先に記録する場合は、日付、店舗、金額、用途を入力してください。"
        ),
        "line_not_receipt_recovery": (
            "これはレシートや経費記録としてはまだ判断できません。\n"
            "経費書類を送るか、記録したい経費内容を入力してください。"
        ),
        "line_need_reply_record": (
            "誤って別の記録を変更しないよう、対象の Pearnly 記録を長押しして「返信」を選び、\n"
            "「削除」や「金額を…に変更」のように入力してください。"
        ),
        "line_web_handoff": (
            "この操作は Pearnly の画面で詳細を確認する必要があります。\n"
            "該当ページを開いて続行できるようにします。"
        ),
        "line_unknown_intent": (
            "何をしたいのかまだ判断できません。\n"
            "書類を送る、最近の記録を見る、経費サマリーを確認する、のいずれかを入力してください。"
        ),
        "line_out_of_scope": "経理と経費を専門にしています。書類を送るか、支出について尋ねてください。",
        "line_date_answer": "本日は {date} です。レシートを送るか、経費を入力して記録できます。",
        "line_query_summary_intro": (
            "記録済みデータに基づく経費サマリーです。\n"
            "合計、記録数、主な分類を表示します。各明細を見たい場合は、詳細表示を依頼してください。"
        ),
        "line_query_detail_intro": (
            "見つかった最近の記録です。\n"
            "修正、破棄、取消を行う場合は、誤操作を防ぐため対象の記録に返信してください。"
        ),
    },
}


def t_line(lang: Optional[str], key: str, **kwargs) -> str:
    """
    取 LINE 场景文案。
    lang:zh/en/th/ja · 其他/None 默认用 th(主市场泰国)
    key:文案 key
    kwargs:格式化变量(如 username / display_name)
    """
    if lang not in LINE_I18N:
        lang = DEFAULT_LANG
    tmpl = LINE_I18N[lang].get(key) or LINE_I18N[DEFAULT_LANG].get(key) or key
    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl
