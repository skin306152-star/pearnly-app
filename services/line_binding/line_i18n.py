# -*- coding: utf-8 -*-
"""LINE Bot 多语言文案字典 + 取词器(zh/en/th/ja · 纯数据叶子)。"""

from typing import Optional

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
            "现在可以:\n"
            "📸 发发票/收据照片或 PDF → 自动识别入账\n"
            "🧾 发一句「ค่าน้ำ 50」→ 自动记一笔并分类"
        ),
        "already_bound_hint": (
            "Hi {username} 👋 我能帮你:\n"
            "📸 发发票/收据照片或 PDF → 自动识别、查重、入账\n"
            "💡 拍全张、光线清晰,识别最准\n"
            "🧾 发一句「ค่าน้ำ 50」→ 自动记一笔并归类到凭证中心\n"
            "🔗 完整功能在 pearnly.com"
        ),
        "need_bind": (
            "👋 我是 Pearnly 财务自动化助手 · 先绑定账号即可开始:\n"
            "1. 登录 https://pearnly.com\n"
            "2.「集成 → LINE Bot」拿 6 位码\n"
            "3. 发给我\n\n"
            "绑定后能做:\n"
            "📸 发发票照片/PDF 自动识别入账\n"
            "🧾 发一句「ค่าน้ำ 50」自动记账分类"
        ),
        "image_not_bound": (
            "⚠️ 你还没绑定 Pearnly 账号\n"
            "到 pearnly.com「集成 → LINE Bot」拿 6 位绑定码发给我,即可开始自动识别入账 📸"
        ),
        "unsupported": (
            "我能识别发票/收据:图片 / PDF / Excel / CSV / Word / TXT\n"
            "也可发一句文字记账,如「ค่าน้ำ 50」"
        ),
        "exp_need_amount": "这笔多少钱?直接回一个数字就行,例如「50」",
        "exp_sum_head": "📊 本月已入账 ฿{amount} · 共 {n} 笔",
        "exp_sum_empty": "本月还没有已入账的支出哦,发张票或一句「ค่าน้ำ 50」记一笔吧",
        "exp_detail_head": "📋 本月明细(最近 {n} 笔):",
        "exp_undo_done": "↩️ 已撤销上一笔 · ฿{amount}",
        "exp_undo_none": "没找到可撤销的记录(只能撤已入账的上一笔)",
        "exp_edit_web": "改某笔金额/字段,到 pearnly.com 采购里改最准、也留痕 🧾",
        "exp_uncat": "未分类",
        "exp_q_not_found": "知识库里没找到相关内容 · 完整问答见 pearnly.com 知识中心",
        "exp_q_source": "来源:{src}",
        "exp_ack_posted": "✅ 已入账 · ฿{amount}",
        "exp_ack_confirm": "⏳ 已识别 · 请在卡片确认 · ฿{amount}",
        "exp_ack_dup": "⚠️ 可能重复 · ฿{amount} · 请核对",
        "exp_ack_inbox": "📥 已收到 · 需补全后入账",
        "card_confirmed": "✅ 已入账 · ฿{amount}",
        "card_undone": "↩️ 已撤销 · ฿{amount}",
        "card_discarded": "🗑 已丢弃 · 未入账",
        "card_action_stale": "这张已处理过或已变更 · 到 pearnly.com 查看",
        "card_action_expired": "这张卡片已过期 · 请重发或到 pearnly.com 操作",
        "qr_record": "记一笔",
        "qr_query": "本月花多少",
        "qr_query_text": "本月花了多少",
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
            "You can now:\n"
            "📸 Send a photo/PDF of an invoice or receipt → auto-read & recorded\n"
            "🧾 Type 'Water 50' → auto-logged and categorized"
        ),
        "already_bound_hint": (
            "Hi {username} 👋 Here's what I can do:\n"
            "📸 Send a photo/PDF of an invoice or receipt → read, de-duplicate, record\n"
            "💡 Tip: capture the full document in good light for best accuracy\n"
            "🧾 Type 'Water 50' → auto-logged to your voucher center, categorized\n"
            "🔗 Full features at pearnly.com"
        ),
        "need_bind": (
            "👋 I'm Pearnly, your accounting automation assistant · link your account to start:\n"
            "1. Log in at https://pearnly.com\n"
            "2. Open 'Integrations → LINE Bot' for your 6-digit code\n"
            "3. Send it to me\n\n"
            "Once linked:\n"
            "📸 Send invoice photos/PDF → auto-read & recorded\n"
            "🧾 Type 'Water 50' → auto-logged and categorized"
        ),
        "image_not_bound": (
            "⚠️ Your Pearnly account isn't linked yet\n"
            "Get a 6-digit code at pearnly.com 'Integrations → LINE Bot' and send it to me to start auto-recording 📸"
        ),
        "unsupported": (
            "I can read invoices/receipts: photos / PDF / Excel / CSV / Word / TXT\n"
            "Or type an expense like 'Water 50'"
        ),
        "exp_need_amount": "How much was it? Just reply a number, e.g. '50'",
        "exp_sum_head": "📊 Recorded this month: ฿{amount} · {n} entries",
        "exp_sum_empty": "No recorded spending this month yet — send a receipt or type 'coffee 65'",
        "exp_detail_head": "📋 This month (latest {n}):",
        "exp_undo_done": "↩️ Undid your last entry · ฿{amount}",
        "exp_undo_none": "No entry to undo (only the last recorded one can be undone)",
        "exp_edit_web": "To change an amount/field, edit it at pearnly.com Purchases — accurate & audited 🧾",
        "exp_uncat": "Uncategorized",
        "exp_q_not_found": "Nothing found in your knowledge base · full Q&A at pearnly.com",
        "exp_q_source": "Source: {src}",
        "exp_ack_posted": "✅ Recorded · ฿{amount}",
        "exp_ack_confirm": "⏳ Recognized · please confirm on the card · ฿{amount}",
        "exp_ack_dup": "⚠️ Possible duplicate · ฿{amount} · please check",
        "exp_ack_inbox": "📥 Received · needs info before posting",
        "card_confirmed": "✅ Recorded · ฿{amount}",
        "card_undone": "↩️ Undone · ฿{amount}",
        "card_discarded": "🗑 Discarded · not recorded",
        "card_action_stale": "Already handled or changed · view at pearnly.com",
        "card_action_expired": "This card has expired · resend it or use pearnly.com",
        "qr_record": "Record",
        "qr_query": "This month",
        "qr_query_text": "how much this month",
    },
    "th": {
        "bind_invalid": "❌ รหัสไม่ถูกต้องหรือหมดอายุ\nกรุณารับรหัสใหม่ที่ pearnly.com",
        "bind_conflict": (
            "❌ ผูกบัญชีไม่สำเร็จ · LINE นี้อาจถูกผูกกับ Pearnly บัญชีอื่นแล้ว\n"
            "กรุณายกเลิกที่บัญชีเดิมก่อน"
        ),
        "bind_success": (
            "✅ ผูกบัญชีสำเร็จ\n\n"
            "บัญชี Pearnly: {username}\n"
            "LINE: {display_name}\n\n"
            "ตอนนี้ทำได้เลย:\n"
            "📸 ส่งรูป/PDF ใบกำกับหรือใบเสร็จ → อ่านและบันทึกอัตโนมัติ\n"
            "🧾 พิมพ์ 'ค่าน้ำ 50' → บันทึกและจัดหมวดให้อัตโนมัติ"
        ),
        "already_bound_hint": (
            "สวัสดี {username} 👋 Pearnly ช่วยคุณได้:\n"
            "📸 ส่งรูป/PDF ใบกำกับหรือใบเสร็จ → อ่าน ตรวจซ้ำ และบันทึกอัตโนมัติ\n"
            "💡 เคล็ดลับ: ถ่ายให้เห็นเต็มใบ แสงชัดเจน เพื่อความแม่นยำสูงสุด\n"
            "🧾 พิมพ์ 'ค่าน้ำ 50' → บันทึกและจัดหมวดเข้าศูนย์ใบสำคัญ\n"
            "🔗 ฟีเจอร์ทั้งหมดที่ pearnly.com"
        ),
        "need_bind": (
            "👋 Pearnly ผู้ช่วยงานบัญชีอัตโนมัติ · ผูกบัญชีก่อนเริ่มใช้งาน:\n"
            "1. เข้าสู่ระบบที่ https://pearnly.com\n"
            "2. เปิด 'การเชื่อมต่อ → LINE Bot' รับรหัส 6 หลัก\n"
            "3. ส่งรหัสมาให้เรา\n\n"
            "หลังผูกบัญชี:\n"
            "📸 ส่งรูป/PDF ใบกำกับ → อ่านและบันทึกอัตโนมัติ\n"
            "🧾 พิมพ์ 'ค่าน้ำ 50' → บันทึกและจัดหมวดอัตโนมัติ"
        ),
        "image_not_bound": (
            "⚠️ ยังไม่ได้ผูกบัญชี Pearnly\n"
            "ไปที่ pearnly.com 'การเชื่อมต่อ → LINE Bot' รับรหัส 6 หลักแล้วส่งมา เพื่อเริ่มอ่านและบันทึกอัตโนมัติ 📸"
        ),
        "unsupported": (
            "รองรับใบกำกับ/ใบเสร็จ: รูป / PDF / Excel / CSV / Word / TXT\n"
            "หรือพิมพ์บันทึกค่าใช้จ่าย เช่น 'ค่าน้ำ 50'"
        ),
        "exp_need_amount": "รายการนี้กี่บาท? พิมพ์ตัวเลขกลับมาได้เลย เช่น '50'",
        "exp_sum_head": "📊 บันทึกเดือนนี้ ฿{amount} · {n} รายการ",
        "exp_sum_empty": "เดือนนี้ยังไม่มีรายการที่บันทึก ส่งใบเสร็จหรือพิมพ์ 'ค่าน้ำ 50' ได้เลย",
        "exp_detail_head": "📋 เดือนนี้ (ล่าสุด {n} รายการ):",
        "exp_undo_done": "↩️ ยกเลิกรายการล่าสุดแล้ว · ฿{amount}",
        "exp_undo_none": "ไม่พบรายการให้ยกเลิก (ยกเลิกได้เฉพาะรายการล่าสุดที่บันทึกแล้ว)",
        "exp_edit_web": "แก้ยอด/ฟิลด์ได้ที่ pearnly.com เมนูจัดซื้อ แม่นยำและมีบันทึก 🧾",
        "exp_uncat": "ยังไม่จัดหมวด",
        "exp_q_not_found": "ไม่พบข้อมูลในคลังความรู้ · ดูถาม-ตอบเต็มที่ pearnly.com",
        "exp_q_source": "ที่มา: {src}",
        "exp_ack_posted": "✅ บันทึกแล้ว · ฿{amount}",
        "exp_ack_confirm": "⏳ อ่านแล้ว · โปรดยืนยันบนการ์ด · ฿{amount}",
        "exp_ack_dup": "⚠️ อาจซ้ำ · ฿{amount} · โปรดตรวจสอบ",
        "exp_ack_inbox": "📥 รับแล้ว · ต้องเติมข้อมูลก่อนบันทึก",
        "card_confirmed": "✅ บันทึกแล้ว · ฿{amount}",
        "card_undone": "↩️ ยกเลิกแล้ว · ฿{amount}",
        "card_discarded": "🗑 ทิ้งแล้ว · ไม่ได้บันทึก",
        "card_action_stale": "รายการนี้จัดการแล้วหรือมีการเปลี่ยนแปลง · ดูที่ pearnly.com",
        "card_action_expired": "การ์ดนี้หมดอายุแล้ว · กรุณาส่งใหม่หรือใช้งานที่ pearnly.com",
        "qr_record": "บันทึกค่าใช้จ่าย",
        "qr_query": "เดือนนี้เท่าไหร่",
        "qr_query_text": "เดือนนี้จ่ายไปเท่าไหร่",
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
            "これで使えます:\n"
            "📸 請求書・領収書の写真/PDF → 自動で読み取り・記帳\n"
            "🧾 「水道 50」と入力 → 自動で記録・仕分け"
        ),
        "already_bound_hint": (
            "こんにちは {username} 👋 Pearnly でできること:\n"
            "📸 請求書・領収書の写真/PDF → 読み取り・重複チェック・記帳\n"
            "💡 コツ: 書類全体を明るく撮ると精度が上がります\n"
            "🧾 「水道 50」と入力 → 証憑センターへ自動記録・仕分け\n"
            "🔗 全機能は pearnly.com"
        ),
        "need_bind": (
            "👋 経理自動化アシスタント Pearnly です · まずアカウント連携を:\n"
            "1. https://pearnly.com にログイン\n"
            "2. 「連携 → LINE Bot」で 6 桁コードを取得\n"
            "3. コードを送信\n\n"
            "連携後:\n"
            "📸 請求書の写真/PDF → 自動で読み取り・記帳\n"
            "🧾 「水道 50」と入力 → 自動で記録・仕分け"
        ),
        "image_not_bound": (
            "⚠️ Pearnly アカウントが未連携です\n"
            "pearnly.com「連携 → LINE Bot」で 6 桁コードを取得して送信すると、自動記帳を開始できます 📸"
        ),
        "unsupported": (
            "対応: 請求書・領収書の 写真 / PDF / Excel / CSV / Word / TXT\n"
            "または「水道 50」のように入力して記帳"
        ),
        "exp_need_amount": "いくらでしたか?数字だけ返信してください(例:50)",
        "exp_sum_head": "📊 今月の記帳 ฿{amount} · {n} 件",
        "exp_sum_empty": "今月まだ記帳がありません。領収書か「水道 50」と送ってください",
        "exp_detail_head": "📋 今月(直近 {n} 件):",
        "exp_undo_done": "↩️ 直近の記帳を取り消しました · ฿{amount}",
        "exp_undo_none": "取り消せる記帳が見つかりません(直近の記帳のみ取消可)",
        "exp_edit_web": "金額/項目の修正は pearnly.com の仕入で。正確で履歴も残ります 🧾",
        "exp_uncat": "未分類",
        "exp_q_not_found": "ナレッジに該当が見つかりません · 完全な Q&A は pearnly.com で",
        "exp_q_source": "出典:{src}",
        "exp_ack_posted": "✅ 記帳しました · ฿{amount}",
        "exp_ack_confirm": "⏳ 読取済 · カードで確認してください · ฿{amount}",
        "exp_ack_dup": "⚠️ 重複の可能性 · ฿{amount} · ご確認ください",
        "exp_ack_inbox": "📥 受領 · 記帳前に情報の補完が必要です",
        "card_confirmed": "✅ 記帳しました · ฿{amount}",
        "card_undone": "↩️ 取り消しました · ฿{amount}",
        "card_discarded": "🗑 破棄しました · 未記帳",
        "card_action_stale": "処理済みまたは変更されています · pearnly.com でご確認ください",
        "card_action_expired": "このカードは期限切れです · 再送するか pearnly.com で操作してください",
        "qr_record": "記録する",
        "qr_query": "今月いくら",
        "qr_query_text": "今月いくら使った",
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


OCR_RESULT_I18N = {
    "zh": {
        "processing": "📸 收到图片 · 正在识别...",
        "success_head": "✅ 识别完成",
        "field_vendor": "供应商",
        "field_no": "发票号",
        "field_date": "日期",
        "field_amount": "金额",
        "no_data": "(未识别出)",
        "multi_invoices": "📦 识别出 {n} 张发票(仅显示第 1 张 · 完整结果请查网页历史)",
        "err_download": "❌ 图片下载失败 · 请重发",
        "err_ocr": "❌ 识别失败 · 请换张清晰点的照片再试",
        "err_quota": "⚠️ 本月识别额度已用完 · 请等下月重置或联系管理员",
        "err_need_key": "⚠️ 请先到网站「设置 → API Key」填入您的 Gemini API Key",
        "err_plan": "⚠️ 账号暂不可用 · 请联系管理员",
        "view_on_web": "网页历史记录查看详情 👉 https://pearnly.com",
        "routed_to_purchase": "✅ 已收到票据 · 已放入「采购 · 待归类」\n到 pearnly.com 采购里确认入账 🧾",
    },
    "en": {
        "processing": "📸 Image received · recognizing...",
        "success_head": "✅ Recognition complete",
        "field_vendor": "Vendor",
        "field_no": "Invoice No",
        "field_date": "Date",
        "field_amount": "Amount",
        "no_data": "(not detected)",
        "multi_invoices": "📦 {n} invoices detected (showing #1 only · see web history for all)",
        "err_download": "❌ Image download failed · please resend",
        "err_ocr": "❌ Recognition failed · try a clearer photo",
        "err_quota": "⚠️ Monthly quota exhausted · please wait for reset or contact admin",
        "err_need_key": "⚠️ Please set your Gemini API Key at 'Settings → API Key' on the website",
        "err_plan": "⚠️ Account unavailable · please contact admin",
        "view_on_web": "View details in web history 👉 https://pearnly.com",
        "routed_to_purchase": "✅ Receipt received · added to Purchases · To-sort\nConfirm & post it under Purchases at pearnly.com 🧾",
    },
    "th": {
        "processing": "📸 รับรูปแล้ว · กำลังอ่าน...",
        "success_head": "✅ อ่านเสร็จแล้ว",
        "field_vendor": "ผู้ขาย",
        "field_no": "เลขที่ใบกำกับ",
        "field_date": "วันที่",
        "field_amount": "ยอดเงิน",
        "no_data": "(ไม่พบ)",
        "multi_invoices": "📦 พบ {n} ใบ (แสดงเฉพาะใบแรก · ดูทั้งหมดในเว็บ)",
        "err_download": "❌ ดาวน์โหลดรูปไม่สำเร็จ · กรุณาส่งใหม่",
        "err_ocr": "❌ อ่านไม่สำเร็จ · ลองถ่ายให้ชัดขึ้น",
        "err_quota": "⚠️ โควต้าเดือนนี้หมดแล้ว · กรุณารอเดือนหน้าหรือติดต่อผู้ดูแล",
        "err_need_key": "⚠️ กรุณาตั้งค่า Gemini API Key ที่ 'การตั้งค่า → API Key' บนเว็บก่อน",
        "err_plan": "⚠️ บัญชีไม่พร้อมใช้งาน · กรุณาติดต่อผู้ดูแล",
        "view_on_web": "ดูรายละเอียดบนเว็บ 👉 https://pearnly.com",
        "routed_to_purchase": "✅ รับใบเสร็จแล้ว · เข้า「จัดซื้อ · รอจัดประเภท」\nยืนยันและบันทึกที่เมนูจัดซื้อ pearnly.com 🧾",
    },
    "ja": {
        "processing": "📸 画像を受信 · 認識中...",
        "success_head": "✅ 認識完了",
        "field_vendor": "取引先",
        "field_no": "請求書番号",
        "field_date": "日付",
        "field_amount": "金額",
        "no_data": "(検出されず)",
        "multi_invoices": "📦 {n} 枚検出(1 枚目のみ表示 · 全件は Web で確認)",
        "err_download": "❌ 画像ダウンロード失敗 · 再送信してください",
        "err_ocr": "❌ 認識失敗 · より鮮明な写真でお試しください",
        "err_quota": "⚠️ 月間枠を使い切りました · リセットまたは管理者にお問い合わせください",
        "err_need_key": "⚠️ Web の「設定 → API Key」で Gemini API Key を設定してください",
        "err_plan": "⚠️ アカウント利用不可 · 管理者にお問い合わせください",
        "view_on_web": "Web で履歴を確認 👉 https://pearnly.com",
        "routed_to_purchase": "✅ 領収書を受信 · 「仕入 · 未分類」に追加\npearnly.com の仕入で確認・登録してください 🧾",
    },
}


def t_ocr(lang: Optional[str], key: str, **kwargs) -> str:
    """OCR 场景文案"""
    if lang not in OCR_RESULT_I18N:
        lang = DEFAULT_LANG
    tmpl = OCR_RESULT_I18N[lang].get(key) or OCR_RESULT_I18N[DEFAULT_LANG].get(key) or key
    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl
