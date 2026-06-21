# -*- coding: utf-8 -*-
"""LINE 绑定/解绑文案(四语)+ 带 Quick Reply 按钮的消息构建器。

line_i18n 已满 500,绑定相关文案独立到此。用户可见文案的唯一源(走模板,不让 LLM 自由发)。
按钮统一用 Quick Reply:连接/换码/状态/客服 → URI 打开官网(LINE 内置浏览器经 openExternalBrowser
自动弹外部浏览器,与 Rich Menu 官网按钮一致)。解绑确认的 postback 按钮见 line 端解绑流程。
"""

from __future__ import annotations

from typing import Dict, List, Optional

DEFAULT_LANG = "th"  # 主市场泰国兜底
CONNECT_URL = "https://pearnly.com?openExternalBrowser=1"
_QR_LABEL_MAX = 20  # LINE Quick Reply label 硬上限

_COPY: Dict[str, Dict[str, str]] = {
    "need_bind": {
        "th": (
            "กรุณาเชื่อมต่อบัญชี Pearnly ก่อน\n"
            "หลังจากเชื่อมต่อแล้ว คุณจะสามารถถ่ายบิล บันทึกบัญชี ค้นหาข้อมูล "
            "และตรวจสอบรายการได้จาก LINE ทันที"
        ),
        "en": (
            "Please connect your Pearnly account first.\n"
            "After connecting, you can upload receipts, record entries, check accounting data, "
            "and review records directly in LINE."
        ),
        "zh": (
            "还需要先连接 Pearnly 账号。\n连接后,你就可以直接在 LINE 里拍票、记账、查账和复核记录。"
        ),
        "ja": (
            "まず Pearnly アカウントを連携してください。\n"
            "連携後、このLINEでレシート送信、記帳、会計データ確認、記録の確認ができます。"
        ),
    },
    "image_not_bound": {
        "th": (
            "ได้รับรูปภาพแล้ว แต่ยังไม่สามารถบันทึกบัญชีให้ได้\n"
            "กรุณาเชื่อมต่อบัญชี Pearnly ก่อน จากนั้นส่งบิลอีกครั้ง "
            "ฉันจะช่วยอ่านข้อมูลและจัดเป็นรายการบัญชีให้ตรวจสอบ"
        ),
        "en": (
            "I received the image, but I can't record it yet.\n"
            "Please connect your Pearnly account first. After connecting, send the receipt again "
            "and I'll help recognize and prepare it as an accounting record."
        ),
        "zh": (
            "我收到图片了,但还不能帮你记账。\n"
            "请先连接 Pearnly 账号,连接后再发送票据,我会帮你识别并整理成记账记录。"
        ),
        "ja": (
            "画像を受け取りましたが、まだ記帳できません。\n"
            "先に Pearnly アカウントを連携してください。連携後にもう一度レシートを送ると、"
            "内容を読み取り、記帳データとして整理します。"
        ),
    },
    "bind_success": {
        "th": (
            "เชื่อมต่อสำเร็จแล้ว\n"
            "ตอนนี้คุณสามารถถ่ายบิล ส่งใบเสร็จ หรือพิมพ์ข้อความสั้น ๆ เพื่อบันทึกบัญชีได้ใน LINE ทันที\n\n"
            "ลองส่งข้อความ เช่น:\n“ค่าน้ำ 50”\n“กาแฟ 65”\n“วันนี้ขายของ 1200”"
        ),
        "en": (
            "Connected successfully.\n"
            "You can now upload receipts, send documents, or type a simple message to record "
            "entries directly in LINE.\n\n"
            "Try sending:\n“Water bill 50”\n“Coffee 65”\n“Sales today 1200”"
        ),
        "zh": (
            "绑定成功。\n"
            "现在你可以直接在 LINE 里拍票、发收据或输入一句话记账。\n\n"
            "试试发送:\n“ค่าน้ำ 50”\n“咖啡 65”\n“วันนี้ขายของ 1200”"
        ),
        "ja": (
            "連携が完了しました。\n"
            "これでLINEからレシート送信、書類アップロード、短い文章での記帳ができます。\n\n"
            "試しに送信してみてください:\n「水道代 50」\n「コーヒー 65」\n「今日の売上 1200」"
        ),
    },
    "bind_invalid": {
        "th": (
            "ลิงก์เชื่อมต่อนี้ไม่สามารถใช้งานได้แล้ว\nกรุณาขอลิงก์ใหม่ แล้วลองเชื่อมต่ออีกครั้ง"
        ),
        "en": (
            "This connection link is no longer valid.\nPlease get a new connection link and try again."
        ),
        "zh": ("这个绑定链接已失效。\n请重新获取绑定链接,再完成连接。"),
        "ja": (
            "この連携リンクは無効になっています。\n新しい連携リンクを取得して、もう一度お試しください。"
        ),
    },
    "bind_conflict": {
        "th": (
            "บัญชี LINE นี้เชื่อมต่อกับบัญชี Pearnly อื่นอยู่แล้ว\n"
            "เพื่อความปลอดภัยของข้อมูลบัญชี LINE หนึ่งบัญชีสามารถเชื่อมต่อกับบัญชี Pearnly "
            "ได้เพียงหนึ่งบัญชีในเวลาเดียวกัน\n\n"
            "หากต้องการเปลี่ยนบัญชี กรุณายกเลิกการเชื่อมต่อจากบัญชีเดิมก่อน แล้วจึงเชื่อมต่อใหม่"
        ),
        "en": (
            "This LINE account is already connected to another Pearnly account.\n"
            "To protect accounting data, one LINE account can only be connected to one Pearnly "
            "account at a time.\n\n"
            "To switch accounts, please disconnect it from the current account first, then connect again."
        ),
        "zh": (
            "这个 LINE 已连接到另一个 Pearnly 账号。\n"
            "为了保护账务数据安全,一个 LINE 账号同一时间只能连接一个 Pearnly 账号。\n\n"
            "如需更换,请先在原账号中解绑,再重新绑定。"
        ),
        "ja": (
            "このLINEアカウントは、すでに別の Pearnly アカウントに連携されています。\n"
            "会計データを保護するため、1つのLINEアカウントは同時に1つの Pearnly アカウントのみ連携できます。\n\n"
            "アカウントを切り替える場合は、現在のアカウントで連携を解除してから、再度連携してください。"
        ),
    },
}

# Quick Reply 按钮文字(≤20 字符·LINE 硬限)。"connection status" 由原文 "View connection status"(22)缩短。
_BTN: Dict[str, Dict[str, str]] = {
    "connect": {
        "th": "เชื่อมต่อ Pearnly",
        "en": "Connect Pearnly",
        "zh": "连接 Pearnly",
        "ja": "Pearnly と連携",
    },
    "retry": {
        "th": "ขอลิงก์ใหม่",
        "en": "Get a new link",
        "zh": "重新获取绑定链接",
        "ja": "新しいリンクを取得",
    },
    "status": {
        "th": "สถานะการเชื่อมต่อ",
        "en": "Connection status",
        "zh": "查看绑定状态",
        "ja": "連携状態を確認",
    },
    "support": {
        "th": "ติดต่อเจ้าหน้าที่",
        "en": "Contact support",
        "zh": "联系客服",
        "ja": "サポートに連絡",
    },
}


def t_bind(lang: Optional[str], key: str) -> str:
    table = _COPY.get(key) or {}
    return table.get(lang or "") or table.get(DEFAULT_LANG) or ""


def _label(lang: Optional[str], btn_key: str) -> str:
    table = _BTN.get(btn_key) or {}
    return (table.get(lang or "") or table.get(DEFAULT_LANG) or "")[:_QR_LABEL_MAX]


def _qr_uri(lang: Optional[str], btn_key: str, url: str = CONNECT_URL) -> dict:
    return {"type": "action", "action": {"type": "uri", "label": _label(lang, btn_key), "uri": url}}


def _msg(text: str, items: Optional[List[dict]] = None) -> dict:
    m: dict = {"type": "text", "text": text}
    if items:
        m["quickReply"] = {"items": items}
    return m


def need_bind_msg(lang: Optional[str]) -> dict:
    return _msg(t_bind(lang, "need_bind"), [_qr_uri(lang, "connect")])


def image_not_bound_msg(lang: Optional[str]) -> dict:
    return _msg(t_bind(lang, "image_not_bound"), [_qr_uri(lang, "connect")])


def bind_invalid_msg(lang: Optional[str]) -> dict:
    return _msg(t_bind(lang, "bind_invalid"), [_qr_uri(lang, "retry")])


def bind_conflict_msg(lang: Optional[str]) -> dict:
    return _msg(t_bind(lang, "bind_conflict"), [_qr_uri(lang, "status"), _qr_uri(lang, "support")])


def bind_success_msg(lang: Optional[str]) -> dict:
    return _msg(t_bind(lang, "bind_success"))
