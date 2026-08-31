"""Localized six-cell entry menu for Cowork LINE."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

ACTION_ERP_START = "cowork_erp_start"

_COPY = {
    "th": {
        "alt": "เมนู Pearnly Cowork",
        "title": "Pearnly Cowork",
        "subtitle": "เลือกเมนูเพื่อเริ่มต้น",
        "start": "ส่งเอกสารเข้า ERP",
        "start_desc": "อัปโหลด ตรวจสอบ และเลือกปลายทาง",
        "soon": "เร็ว ๆ นี้",
        "display": "ส่งเอกสารเข้า ERP",
    },
    "en": {
        "alt": "Pearnly Cowork menu",
        "title": "Pearnly Cowork",
        "subtitle": "Choose a menu to get started",
        "start": "Send document to ERP",
        "start_desc": "Upload, review, and choose a destination",
        "soon": "Coming soon",
        "display": "Send document to ERP",
    },
    "zh": {
        "alt": "Pearnly Cowork 菜单",
        "title": "Pearnly Cowork",
        "subtitle": "请选择一个功能开始",
        "start": "上传单据到 ERP",
        "start_desc": "上传、核对并选择推送目标",
        "soon": "即将开放",
        "display": "上传单据到 ERP",
    },
    "ja": {
        "alt": "Pearnly Cowork メニュー",
        "title": "Pearnly Cowork",
        "subtitle": "メニューを選択してください",
        "start": "書類を ERP に送信",
        "start_desc": "アップロード、確認、送信先の選択",
        "soon": "近日公開",
        "display": "書類を ERP に送信",
    },
}


def _language(lang: str) -> str:
    value = (lang or "th").lower()
    for supported in _COPY:
        if value.startswith(supported):
            return supported
    return "th"


def _cell(number: int, *, active: bool, copy: dict[str, str]) -> dict[str, Any]:
    cell: dict[str, Any] = {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "paddingAll": "12px",
        "cornerRadius": "14px",
        "backgroundColor": "#EEF3FF" if active else "#F2F1F5",
        "borderWidth": "1px",
        "borderColor": "#CAD8FF" if active else "#E1DFE7",
        "contents": [
            {
                "type": "text",
                "text": f"{number:02d}",
                "size": "xs",
                "weight": "bold",
                "color": "#2F6BFF" if active else "#A39DAD",
            },
            {
                "type": "text",
                "text": copy["start"] if active else copy["soon"],
                "size": "sm",
                "weight": "bold",
                "color": "#202033" if active else "#837D8D",
                "wrap": True,
                "margin": "md",
            },
            {
                "type": "text",
                "text": copy["start_desc"] if active else copy["soon"],
                "size": "xxs",
                "color": "#666477" if active else "#AAA5B1",
                "wrap": True,
                "margin": "sm",
            },
        ],
    }
    if active:
        cell["action"] = {
            "type": "postback",
            "data": urlencode({"action": ACTION_ERP_START}),
            "displayText": copy["display"],
        }
    return cell


def menu_card(lang: str = "th") -> dict[str, Any]:
    copy = _COPY[_language(lang)]
    cells = [_cell(index, active=index == 1, copy=copy) for index in range(1, 7)]
    rows = [
        {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": cells[offset : offset + 3],
        }
        for offset in (0, 3)
    ]
    return {
        "type": "flex",
        "altText": copy["alt"],
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": copy["title"], "size": "lg", "weight": "bold"},
                    {
                        "type": "text",
                        "text": copy["subtitle"],
                        "size": "xs",
                        "color": "#777486",
                        "margin": "xs",
                    },
                    {"type": "separator", "color": "#ECEAF0", "margin": "lg"},
                    {**rows[0], "margin": "lg"},
                    {**rows[1], "margin": "sm"},
                ],
            },
        },
    }
