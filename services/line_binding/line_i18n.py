# -*- coding: utf-8 -*-
"""LINE Bot 多语言文案字典 + 取词器(zh/en/th/ja · 纯数据叶子)。"""

from typing import Optional

LINE_I18N = {
    "zh": {
        "welcome": (
            "👋 欢迎使用 Pearnly\n"
            "智能记账助手 · 为泰国会计事务所与中小企业打造\n\n"
            "开始前先绑定账号:\n"
            "1. 登录 https://pearnly.com\n"
            "2. 打开「自动化 → LINE Bot」\n"
            "3. 把 6 位绑定码发给我\n\n"
            "绑定后,把发票/收据拍照发来,几秒自动识别入账 📸"
        ),
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
            "🧾 发一句「ค่าน้ำ 50」→ 自动记一笔并分类\n"
            "💬 需要人工 → 回复「人工」"
        ),
        "already_bound_hint": (
            "Hi {username} 👋 我能帮你:\n"
            "📸 发发票/收据照片或 PDF → 自动识别、查重、入账\n"
            "🧾 发一句「ค่าน้ำ 50」→ 自动记一笔并归类到凭证中心\n"
            "💬 需要人工 → 回复「人工」\n"
            "🔗 完整功能在 pearnly.com"
        ),
        "need_bind": (
            "👋 我是 Pearnly 智能记账助手 · 先绑定账号即可开始:\n"
            "1. 登录 https://pearnly.com\n"
            "2.「自动化 → LINE Bot」拿 6 位码\n"
            "3. 发给我\n\n"
            "绑定后能做:\n"
            "📸 发发票照片/PDF 自动识别入账\n"
            "🧾 发一句「ค่าน้ำ 50」自动记账分类"
        ),
        "image_not_bound": (
            "⚠️ 你还没绑定 Pearnly 账号\n"
            "到 pearnly.com「自动化 → LINE Bot」拿 6 位绑定码发给我,即可开始自动识别入账 📸"
        ),
        "image_soon": "📷 收到图片 · 处理中...",
        "unsupported": (
            "我能识别发票/收据:图片 / PDF / Excel / CSV / Word / TXT\n"
            "也可发一句文字记账,如「ค่าน้ำ 50」\n"
            "需要人工 → 回复「人工」"
        ),
        "agent_ack": "🙋 正在为你转接人工 · 我们的团队会尽快回复(周一–周五 9:00–18:00)",
    },
    "en": {
        "welcome": (
            "👋 Welcome to Pearnly\n"
            "The smart bookkeeping assistant for accounting firms & SMEs in Thailand\n\n"
            "Let's get you set up:\n"
            "1. Log in at https://pearnly.com\n"
            "2. Open 'Automation → LINE Bot'\n"
            "3. Send me the 6-digit code\n\n"
            "Once linked, just snap a photo of any invoice/receipt — I'll read and record it in seconds 📸"
        ),
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
            "🧾 Type 'Water 50' → auto-logged and categorized\n"
            "💬 Need a human → type 'agent'"
        ),
        "already_bound_hint": (
            "Hi {username} 👋 Here's what I can do:\n"
            "📸 Send a photo/PDF of an invoice or receipt → read, de-duplicate, record\n"
            "🧾 Type 'Water 50' → auto-logged to your voucher center, categorized\n"
            "💬 Need a human → type 'agent'\n"
            "🔗 Full features at pearnly.com"
        ),
        "need_bind": (
            "👋 I'm Pearnly, your smart bookkeeping assistant · link your account to start:\n"
            "1. Log in at https://pearnly.com\n"
            "2. Open 'Automation → LINE Bot' for your 6-digit code\n"
            "3. Send it to me\n\n"
            "Once linked:\n"
            "📸 Send invoice photos/PDF → auto-read & recorded\n"
            "🧾 Type 'Water 50' → auto-logged and categorized"
        ),
        "image_not_bound": (
            "⚠️ Your Pearnly account isn't linked yet\n"
            "Get a 6-digit code at pearnly.com 'Automation → LINE Bot' and send it to me to start auto-recording 📸"
        ),
        "image_soon": "📷 Image received · processing...",
        "unsupported": (
            "I can read invoices/receipts: photos / PDF / Excel / CSV / Word / TXT\n"
            "Or type an expense like 'Water 50'\n"
            "Need a human → type 'agent'"
        ),
        "agent_ack": "🙋 Connecting you to our team · we'll reply shortly (Mon–Fri 9:00–18:00)",
    },
    "th": {
        "welcome": (
            "👋 ยินดีต้อนรับสู่ Pearnly\n"
            "ผู้ช่วยบัญชีอัจฉริยะ สำหรับสำนักงานบัญชีและ SME ในไทย\n\n"
            "เริ่มต้นด้วยการผูกบัญชี:\n"
            "1. เข้าสู่ระบบที่ https://pearnly.com\n"
            "2. เปิด 'ระบบอัตโนมัติ → LINE Bot'\n"
            "3. ส่งรหัส 6 หลักมาให้เรา\n\n"
            "หลังผูกบัญชี ถ่ายรูปใบกำกับ/ใบเสร็จส่งมาได้เลย ระบบจะอ่านและบันทึกให้อัตโนมัติภายในไม่กี่วินาที 📸"
        ),
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
            "🧾 พิมพ์ 'ค่าน้ำ 50' → บันทึกและจัดหมวดให้อัตโนมัติ\n"
            "💬 ต้องการเจ้าหน้าที่ → พิมพ์ 'เจ้าหน้าที่'"
        ),
        "already_bound_hint": (
            "สวัสดี {username} 👋 Pearnly ช่วยคุณได้:\n"
            "📸 ส่งรูป/PDF ใบกำกับหรือใบเสร็จ → อ่าน ตรวจซ้ำ และบันทึกอัตโนมัติ\n"
            "🧾 พิมพ์ 'ค่าน้ำ 50' → บันทึกและจัดหมวดเข้าศูนย์ใบสำคัญ\n"
            "💬 ต้องการเจ้าหน้าที่ → พิมพ์ 'เจ้าหน้าที่'\n"
            "🔗 ฟีเจอร์ทั้งหมดที่ pearnly.com"
        ),
        "need_bind": (
            "👋 Pearnly ผู้ช่วยบัญชีอัจฉริยะ · ผูกบัญชีก่อนเริ่มใช้งาน:\n"
            "1. เข้าสู่ระบบที่ https://pearnly.com\n"
            "2. เปิด 'ระบบอัตโนมัติ → LINE Bot' รับรหัส 6 หลัก\n"
            "3. ส่งรหัสมาให้เรา\n\n"
            "หลังผูกบัญชี:\n"
            "📸 ส่งรูป/PDF ใบกำกับ → อ่านและบันทึกอัตโนมัติ\n"
            "🧾 พิมพ์ 'ค่าน้ำ 50' → บันทึกและจัดหมวดอัตโนมัติ"
        ),
        "image_not_bound": (
            "⚠️ ยังไม่ได้ผูกบัญชี Pearnly\n"
            "ไปที่ pearnly.com 'ระบบอัตโนมัติ → LINE Bot' รับรหัส 6 หลักแล้วส่งมา เพื่อเริ่มอ่านและบันทึกอัตโนมัติ 📸"
        ),
        "image_soon": "📷 รับรูปแล้ว · กำลังประมวลผล...",
        "unsupported": (
            "รองรับใบกำกับ/ใบเสร็จ: รูป / PDF / Excel / CSV / Word / TXT\n"
            "หรือพิมพ์บันทึกค่าใช้จ่าย เช่น 'ค่าน้ำ 50'\n"
            "ต้องการเจ้าหน้าที่ → พิมพ์ 'เจ้าหน้าที่'"
        ),
        "agent_ack": "🙋 กำลังโอนสายให้เจ้าหน้าที่ · ทีมงานจะตอบกลับโดยเร็ว (จันทร์–ศุกร์ 9:00–18:00)",
    },
    "ja": {
        "welcome": (
            "👋 Pearnly へようこそ\n"
            "会計事務所・SME 向けのスマート経理アシスタントです\n\n"
            "まずはアカウント連携を:\n"
            "1. https://pearnly.com にログイン\n"
            "2. 「自動化 → LINE Bot」を開く\n"
            "3. 6 桁のコードを送信\n\n"
            "連携後は、請求書・領収書を撮って送るだけ。数秒で読み取り・記帳します 📸"
        ),
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
            "🧾 「水道 50」と入力 → 自動で記録・仕分け\n"
            "💬 オペレーター希望 → 「オペレーター」と入力"
        ),
        "already_bound_hint": (
            "こんにちは {username} 👋 Pearnly でできること:\n"
            "📸 請求書・領収書の写真/PDF → 読み取り・重複チェック・記帳\n"
            "🧾 「水道 50」と入力 → 証憑センターへ自動記録・仕分け\n"
            "💬 オペレーター希望 → 「オペレーター」と入力\n"
            "🔗 全機能は pearnly.com"
        ),
        "need_bind": (
            "👋 スマート経理アシスタント Pearnly です · まずアカウント連携を:\n"
            "1. https://pearnly.com にログイン\n"
            "2. 「自動化 → LINE Bot」で 6 桁コードを取得\n"
            "3. コードを送信\n\n"
            "連携後:\n"
            "📸 請求書の写真/PDF → 自動で読み取り・記帳\n"
            "🧾 「水道 50」と入力 → 自動で記録・仕分け"
        ),
        "image_not_bound": (
            "⚠️ Pearnly アカウントが未連携です\n"
            "pearnly.com「自動化 → LINE Bot」で 6 桁コードを取得して送信すると、自動記帳を開始できます 📸"
        ),
        "image_soon": "📷 画像を受信 · 処理中...",
        "unsupported": (
            "対応: 請求書・領収書の 写真 / PDF / Excel / CSV / Word / TXT\n"
            "または「水道 50」のように入力して記帳\n"
            "オペレーター希望 → 「オペレーター」と入力"
        ),
        "agent_ack": "🙋 オペレーターにおつなぎします · 担当者より順次ご返信します(月–金 9:00–18:00)",
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
        lang = "th"
    tmpl = LINE_I18N[lang].get(key) or LINE_I18N["th"].get(key) or key
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
    },
}


def t_ocr(lang: Optional[str], key: str, **kwargs) -> str:
    """OCR 场景文案"""
    if lang not in OCR_RESULT_I18N:
        lang = "th"
    tmpl = OCR_RESULT_I18N[lang].get(key) or OCR_RESULT_I18N["th"].get(key) or key
    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl
