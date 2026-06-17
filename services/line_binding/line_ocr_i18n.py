# -*- coding: utf-8 -*-
"""LINE OCR 场景文案 + 取词器(zh/en/th/ja · 从 line_i18n 抽出 · 保其 <500)。

t_ocr 仍由 line_i18n re-export,line_client.t_ocr 契约不变。
"""

from typing import Optional

DEFAULT_LANG = "th"  # 主市场泰国 · 与 line_i18n 一致

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
        "not_receipt": "这张看起来不是发票/收据/采购单据 · 请发送完整票据照片或 PDF",
        "err_quota": "⚠️ 本月识别额度已用完 · 请等下月重置或联系管理员",
        "err_need_key": "⚠️ 请先到网站「设置 → API Key」填入您的 Gemini API Key",
        "err_plan": "⚠️ 账号暂不可用 · 请联系管理员",
        "view_on_web": "网页历史记录查看详情 👉 https://pearnly.com",
        "routed_to_purchase": "✅ 已收到票据 · 已放入「采购 · 草稿」\n到 pearnly.com 采购里确认入账 🧾",
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
        "not_receipt": "This doesn't look like an invoice, receipt, or purchase document. Please send the full receipt/photo or PDF.",
        "err_quota": "⚠️ Monthly quota exhausted · please wait for reset or contact admin",
        "err_need_key": "⚠️ Please set your Gemini API Key at 'Settings → API Key' on the website",
        "err_plan": "⚠️ Account unavailable · please contact admin",
        "view_on_web": "View details in web history 👉 https://pearnly.com",
        "routed_to_purchase": "✅ Receipt received · added to Purchases · Draft\nConfirm & post it under Purchases at pearnly.com 🧾",
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
        "not_receipt": "รูปนี้ดูไม่ใช่ใบกำกับ/ใบเสร็จ/เอกสารซื้อ กรุณาส่งรูปใบเสร็จเต็มใบหรือ PDF",
        "err_quota": "⚠️ โควต้าเดือนนี้หมดแล้ว · กรุณารอเดือนหน้าหรือติดต่อผู้ดูแล",
        "err_need_key": "⚠️ กรุณาตั้งค่า Gemini API Key ที่ 'การตั้งค่า → API Key' บนเว็บก่อน",
        "err_plan": "⚠️ บัญชีไม่พร้อมใช้งาน · กรุณาติดต่อผู้ดูแล",
        "view_on_web": "ดูรายละเอียดบนเว็บ 👉 https://pearnly.com",
        "routed_to_purchase": "✅ รับใบเสร็จแล้ว · เข้า「จัดซื้อ · ฉบับร่าง」\nยืนยันและบันทึกที่เมนูจัดซื้อ pearnly.com 🧾",
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
        "not_receipt": "請求書・領収書・仕入書類ではないようです。書類全体の写真または PDF を送ってください。",
        "err_quota": "⚠️ 月間枠を使い切りました · リセットまたは管理者にお問い合わせください",
        "err_need_key": "⚠️ Web の「設定 → API Key」で Gemini API Key を設定してください",
        "err_plan": "⚠️ アカウント利用不可 · 管理者にお問い合わせください",
        "view_on_web": "Web で履歴を確認 👉 https://pearnly.com",
        "routed_to_purchase": "✅ 領収書を受信 · 「仕入 · 下書き」に追加\npearnly.com の仕入で確認・登録してください 🧾",
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
