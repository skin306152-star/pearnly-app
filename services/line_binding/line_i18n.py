# -*- coding: utf-8 -*-
"""LINE Bot 多语言文案字典 + 取词器(zh/en/th/ja · 纯数据叶子)。"""

from typing import Optional

LINE_I18N = {
    "zh": {
        "welcome": (
            "👋 欢迎使用 Pearnly!\n\n"
            "请先到网站绑定账号:\n"
            "1. 登录 https://pearnly.com\n"
            "2. 打开「自动化 → LINE Bot」\n"
            "3. 把那里显示的 6 位数字发给我\n\n"
            "绑定完成后 · 把发票照片发给我 · 我帮你自动识别 ✨"
        ),
        "bind_invalid": "❌ 绑定码无效或已过期。\n请回网站重新获取。",
        "bind_conflict": (
            "❌ 绑定失败 · 此 LINE 账号可能已绑到其他 Pearnly 用户。\n" "请先在原账号解绑再试。"
        ),
        "bind_success": (
            "✅ 绑定成功!\n\n"
            "Pearnly 账号:{username}\n"
            "LINE:{display_name}\n\n"
            "接下来把发票照片发给我 · 自动识别入账 📸\n"
            "(图片识别功能即将上线)"
        ),
        "already_bound_hint": (
            "Hi {username} · 已绑定。\n" "把发票照片发给我 · 即可自动识别(功能即将上线)。"
        ),
        "need_bind": (
            "👋 请先绑定账号:\n"
            "1. 登录 Pearnly 网站\n"
            "2. 打开「自动化 → LINE Bot」\n"
            "3. 把 6 位数字绑定码发给我"
        ),
        "image_not_bound": (
            "⚠️ 您还没绑定 Pearnly 账号。\n"
            "请到网站「自动化 → LINE Bot」获取绑定码 · 发给我即可。"
        ),
        "image_soon": "📷 收到图片 · 图片识别功能即将上线 · 敬请期待!",
        "unsupported": "支持文字(绑定码)以及发票文件:PDF / 图片 / Excel / CSV / Word / TXT。",
    },
    "en": {
        "welcome": (
            "👋 Welcome to Pearnly!\n\n"
            "Please bind your account first:\n"
            "1. Log in at https://pearnly.com\n"
            "2. Open 'Automation → LINE Bot'\n"
            "3. Send me the 6-digit code shown there\n\n"
            "Once bound, send invoice photos to me and I'll recognize them automatically ✨"
        ),
        "bind_invalid": "❌ Invalid or expired code.\nPlease get a new one from the website.",
        "bind_conflict": (
            "❌ Binding failed · this LINE account may already be bound to another Pearnly user.\n"
            "Please unbind from the original account first."
        ),
        "bind_success": (
            "✅ Bound successfully!\n\n"
            "Pearnly account: {username}\n"
            "LINE: {display_name}\n\n"
            "Now send me invoice photos · I'll auto-recognize and file them 📸\n"
            "(Image recognition coming soon)"
        ),
        "already_bound_hint": (
            "Hi {username} · already bound.\n"
            "Send me invoice photos for auto-recognition (coming soon)."
        ),
        "need_bind": (
            "👋 Please bind first:\n"
            "1. Log in to Pearnly website\n"
            "2. Open 'Automation → LINE Bot'\n"
            "3. Send me the 6-digit binding code"
        ),
        "image_not_bound": (
            "⚠️ You haven't bound a Pearnly account yet.\n"
            "Go to 'Automation → LINE Bot' on the website to get a binding code."
        ),
        "image_soon": "📷 Image received · recognition feature coming soon!",
        "unsupported": "Send text binding codes or invoice files: PDF / images / Excel / CSV / Word / TXT.",
    },
    "th": {
        "welcome": (
            "👋 ยินดีต้อนรับสู่ Pearnly!\n\n"
            "กรุณาผูกบัญชีก่อน:\n"
            "1. เข้าสู่ระบบที่ https://pearnly.com\n"
            "2. เปิด 'ระบบอัตโนมัติ → LINE Bot'\n"
            "3. ส่งรหัส 6 หลักที่แสดงไว้มาให้เรา\n\n"
            "หลังผูกบัญชี · ส่งรูปใบกำกับมา · จะอ่านให้อัตโนมัติ ✨"
        ),
        "bind_invalid": "❌ รหัสไม่ถูกต้องหรือหมดอายุ\nกรุณารับรหัสใหม่จากเว็บไซต์",
        "bind_conflict": (
            "❌ ผูกบัญชีไม่สำเร็จ · LINE นี้อาจถูกผูกกับ Pearnly บัญชีอื่นแล้ว\n"
            "กรุณายกเลิกที่บัญชีเดิมก่อน"
        ),
        "bind_success": (
            "✅ ผูกบัญชีสำเร็จ!\n\n"
            "บัญชี Pearnly: {username}\n"
            "LINE: {display_name}\n\n"
            "ส่งรูปใบกำกับมาได้เลย · จะอ่านและบันทึกอัตโนมัติ 📸\n"
            "(ฟีเจอร์อ่านรูปกำลังมา)"
        ),
        "already_bound_hint": (
            "สวัสดี {username} · ผูกบัญชีเรียบร้อย\n"
            "ส่งรูปใบกำกับมา · จะอ่านให้อัตโนมัติ (กำลังมา)"
        ),
        "need_bind": (
            "👋 กรุณาผูกบัญชีก่อน:\n"
            "1. เข้าสู่เว็บ Pearnly\n"
            "2. เปิด 'ระบบอัตโนมัติ → LINE Bot'\n"
            "3. ส่งรหัส 6 หลักมาให้เรา"
        ),
        "image_not_bound": (
            "⚠️ ยังไม่ได้ผูกบัญชี Pearnly\n"
            "ไปที่ 'ระบบอัตโนมัติ → LINE Bot' บนเว็บไซต์เพื่อรับรหัสผูกบัญชี"
        ),
        "image_soon": "📷 รับรูปแล้ว · ฟีเจอร์อ่านรูปกำลังมา · โปรดรอ!",
        "unsupported": "รองรับรหัสผูกบัญชีและไฟล์ใบกำกับ: PDF / รูปภาพ / Excel / CSV / Word / TXT",
    },
    "ja": {
        "welcome": (
            "👋 Pearnly へようこそ!\n\n"
            "まずアカウントを紐付けてください:\n"
            "1. https://pearnly.com にログイン\n"
            "2. 「自動化 → LINE Bot」を開く\n"
            "3. そこに表示される 6 桁の数字を送信\n\n"
            "紐付け完了後 · 請求書の写真を送ると自動認識します ✨"
        ),
        "bind_invalid": "❌ コードが無効または期限切れです。\nウェブサイトから新しいコードを取得してください。",
        "bind_conflict": (
            "❌ 紐付け失敗 · この LINE は別の Pearnly アカウントに紐付け済みの可能性があります。\n"
            "元のアカウントで先に解除してください。"
        ),
        "bind_success": (
            "✅ 紐付け成功!\n\n"
            "Pearnly アカウント: {username}\n"
            "LINE: {display_name}\n\n"
            "請求書の写真を送ってください · 自動で認識して記録します 📸\n"
            "(画像認識は近日公開)"
        ),
        "already_bound_hint": (
            "こんにちは {username} · 紐付け済みです。\n"
            "請求書の写真を送ると自動認識します(近日公開)。"
        ),
        "need_bind": (
            "👋 まず紐付けしてください:\n"
            "1. Pearnly サイトにログイン\n"
            "2. 「自動化 → LINE Bot」を開く\n"
            "3. 6 桁のコードを送信"
        ),
        "image_not_bound": (
            "⚠️ Pearnly アカウントがまだ紐付けされていません。\n"
            "サイトの「自動化 → LINE Bot」でコードを取得してください。"
        ),
        "image_soon": "📷 画像を受信しました · 画像認識機能は近日公開!",
        "unsupported": "紐付けコードと請求書ファイル(PDF / 画像 / Excel / CSV / Word / TXT)に対応しています。",
    },
}


def t_line(lang: Optional[str], key: str, **kwargs) -> str:
    """
    取 LINE 场景文案。
    lang:zh/en/th/ja · 其他/None 默认用 zh
    key:文案 key
    kwargs:格式化变量(如 username / display_name)
    """
    if lang not in LINE_I18N:
        lang = "zh"
    tmpl = LINE_I18N[lang].get(key) or LINE_I18N["zh"].get(key) or key
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
        lang = "zh"
    tmpl = OCR_RESULT_I18N[lang].get(key) or OCR_RESULT_I18N["zh"].get(key) or key
    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl
