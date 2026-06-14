# -*- coding: utf-8 -*-
"""LINE 进项整合 glue(Flex 标签 / 取链接回复 / 灰度开关 · 阶段三)。

把纯构建(line_flex/line_commands/line_postback)接成可用:按语言出 Flex 标签、取链接命令
回复文案。Flex-on-OCR 走 LINE_FLEX_INTAKE 灰度(默认关 → OCR 主路径仍回纯文字不变),开
则发 Flex 卡 + [确认入采购][记为费用][修改 LIFF]。标签 4 语内联(LINE 域,不进 home.js i18n)。
"""

from __future__ import annotations

import os

from services.line_binding import line_commands, line_flex

# Flex 卡 4 语标签(LINE 专用·与 home.js i18n 分离)。
_LABELS = {
    "zh": {
        "head": "识别完成 · 请核对",
        "vendor": "卖家",
        "no": "票号",
        "date": "日期",
        "amount": "金额",
        "confirm": "确认入采购",
        "expense": "记为费用",
        "edit": "修改",
        "review_mark": "(请核对)",
    },
    "th": {
        "head": "อ่านสำเร็จ · โปรดตรวจ",
        "vendor": "ผู้ขาย",
        "no": "เลขที่",
        "date": "วันที่",
        "amount": "จำนวนเงิน",
        "confirm": "บันทึกเป็นซื้อ",
        "expense": "บันทึกเป็นค่าใช้จ่าย",
        "edit": "แก้ไข",
        "review_mark": "(โปรดตรวจ)",
    },
    "en": {
        "head": "Scanned · please review",
        "vendor": "Seller",
        "no": "Invoice No.",
        "date": "Date",
        "amount": "Amount",
        "confirm": "Add to purchases",
        "expense": "Log as expense",
        "edit": "Edit",
        "review_mark": "(review)",
    },
    "ja": {
        "head": "読取完了 · ご確認ください",
        "vendor": "売り手",
        "no": "請求番号",
        "date": "日付",
        "amount": "金額",
        "confirm": "仕入に登録",
        "expense": "経費に登録",
        "edit": "編集",
        "review_mark": "(要確認)",
    },
}

# 取链接命令回复(命中但暂无链接时引导去网页连 Google/导出)。
_LINK_REPLY = {
    "zh": "在网页「集成中心」连接 Google 后,这里可一键取回 Drive/Sheet 链接:{url}",
    "th": "เชื่อม Google ที่หน้าเว็บ「ศูนย์เชื่อมต่อ」ก่อน แล้วขอลิงก์ Drive/Sheet ได้ที่นี่: {url}",
    "en": "Connect Google in the web Integrations page, then get your Drive/Sheet link here: {url}",
    "ja": "Web「連携センター」でGoogleを接続後、Drive/Sheetリンクをここで取得できます: {url}",
}


def ocr_labels(lang: str) -> dict:
    return _LABELS.get((lang or "zh").lower(), _LABELS["zh"])


def is_flex_enabled() -> bool:
    """Flex-on-OCR 灰度(默认关 · OCR 主路径不变)。"""
    return os.environ.get("LINE_FLEX_INTAKE", "").strip().lower() in ("1", "true", "yes", "on")


def build_ocr_flex(
    *, lang: str, fields: dict, field_confidence: dict, doc_id: str, liff_url: str = ""
) -> dict:
    """OCR 字段 + 置信 → Flex message dict(按语言注入标签)。"""
    return line_flex.ocr_result_flex(
        fields=fields,
        field_confidence=field_confidence or {},
        doc_id=doc_id,
        labels=ocr_labels(lang),
        liff_url=liff_url,
    )


def parse_link_command(text: str):
    """文字 → 取链接命令(drive_link/sheet_link/None)· 透传 line_commands。"""
    return line_commands.parse_link_command(text)


def link_reply(cmd: str, lang: str, *, web_url: str) -> str:
    """取链接命令 → 回复文案(引导网页取链接·真链接由网页/导出给)。"""
    tmpl = _LINK_REPLY.get((lang or "zh").lower(), _LINK_REPLY["zh"])
    return tmpl.format(url=web_url)


# 卡按钮处理后的回执(4 语)。
_ACK = {
    "purchase": {
        "zh": "已入采购 · 可在网页录入屏继续完善",
        "th": "บันทึกเป็นซื้อแล้ว",
        "en": "Added to purchases",
        "ja": "仕入に登録しました",
    },
    "expense": {
        "zh": "已记为费用",
        "th": "บันทึกเป็นค่าใช้จ่ายแล้ว",
        "en": "Logged as expense",
        "ja": "経費に登録しました",
    },
}


def ack_reply(action: str, lang: str) -> str:
    """卡回调处理回执文案(action=purchase|expense)。"""
    by_lang = _ACK.get(action) or _ACK["expense"]
    return by_lang.get((lang or "zh").lower(), by_lang["zh"])


# Rich Menu 6 格(2500×843 · 3 列 2 行)· 入口:拍票/取Drive/取Sheet/费用汇总/打开网页/帮助。
_RM_CELLS = [
    {"key": "shoot", "action": {"type": "message", "text": "拍进项票"}},
    {"key": "drive", "action": {"type": "message", "text": "ขอ link drive"}},
    {"key": "sheet", "action": {"type": "message", "text": "ขอ google sheet"}},
    {"key": "expense", "action": {"type": "message", "text": "เมนู"}},
    {"key": "web", "action": {"type": "uri", "uri": ""}},  # 运行时填 LIFF/网页 URL
    {"key": "help", "action": {"type": "message", "text": "help"}},
]


def rich_menu_payload(*, name: str = "pearnly-main", web_url: str = "") -> dict:
    """Rich Menu 配置 dict(纯·喂 LINE createRichMenu)。6 格各映射一命令/URI。"""
    cw, ch = 833, 421
    areas = []
    for i, cell in enumerate(_RM_CELLS):
        col, rown = i % 3, i // 3
        action = dict(cell["action"])
        if action.get("type") == "uri":
            action["uri"] = web_url or "https://pearnly.com/home"
        areas.append(
            {
                "bounds": {"x": col * cw, "y": rown * ch, "width": cw, "height": ch},
                "action": action,
            }
        )
    return {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": name,
        "chatBarText": "Pearnly",
        "areas": areas,
    }
