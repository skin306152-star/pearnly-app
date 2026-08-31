"""Localized six-cell entry menu for Cowork LINE."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from services.line_dms.menu_cards import (
    THEME_BLUE,
    menu_icon_disc,
    menu_item,
)

ACTION_ERP_START = "cowork_erp_start"

_COPY = {
    "th": {
        "alt": "เมนู Pearnly Cowork",
        "title": "Pearnly Cowork",
        "subtitle": "เลือกเมนูเพื่อเริ่มต้น",
        "start": "ส่งเอกสารเข้า ERP",
        "start_desc": "อัปโหลด ตรวจสอบ และเลือกปลายทาง",
        "soon": "เร็ว ๆ นี้",
        "soon_desc": "ฟังก์ชันนี้กำลังเตรียมเปิดให้ใช้งาน",
        "hint": "พิมพ์ เมนู เพื่อเรียกเมนูนี้ได้ตลอดเวลา",
        "display": "ส่งเอกสารเข้า ERP",
    },
    "en": {
        "alt": "Pearnly Cowork menu",
        "title": "Pearnly Cowork",
        "subtitle": "Choose a menu to get started",
        "start": "Send document to ERP",
        "start_desc": "Upload, review, and choose a destination",
        "soon": "Coming soon",
        "soon_desc": "This function is being prepared",
        "hint": "Type Menu to open this menu at any time",
        "display": "Send document to ERP",
    },
    "zh": {
        "alt": "Pearnly Cowork 菜单",
        "title": "Pearnly Cowork",
        "subtitle": "请选择一个功能开始",
        "start": "上传单据到 ERP",
        "start_desc": "上传、核对并选择推送目标",
        "soon": "即将开放",
        "soon_desc": "该功能正在准备中",
        "hint": "随时输入“菜单”即可重新打开",
        "display": "上传单据到 ERP",
    },
    "ja": {
        "alt": "Pearnly Cowork メニュー",
        "title": "Pearnly Cowork",
        "subtitle": "メニューを選択してください",
        "start": "書類を ERP に送信",
        "start_desc": "アップロード、確認、送信先の選択",
        "soon": "近日公開",
        "soon_desc": "この機能は準備中です",
        "hint": "「メニュー」と入力するといつでも再表示できます",
        "display": "書類を ERP に送信",
    },
}


def _language(lang: str) -> str:
    value = (lang or "th").lower()
    for supported in _COPY:
        if value.startswith(supported):
            return supported
    return "th"


_THEME_MUTED = {"accent": "#A39DAD", "soft": "#F2F1F5", "border": "#E1DFE7"}


def menu_card(lang: str = "th") -> dict[str, Any]:
    copy = _COPY[_language(lang)]
    action = {
        "type": "postback",
        "data": urlencode({"action": ACTION_ERP_START}),
        "displayText": copy["display"],
    }
    rows = [
        menu_item(
            "1",
            "menu-3",
            THEME_BLUE,
            copy["start"],
            copy["start_desc"],
            action,
        )
    ]
    rows.extend(
        menu_item(
            str(index),
            "menu-head",
            _THEME_MUTED,
            copy["soon"],
            copy["soon_desc"],
            None,
        )
        for index in range(2, 7)
    )
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
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "md",
                        "alignItems": "center",
                        "contents": [
                            menu_icon_disc("menu-head", "#EAF0FF", "40px", "22px"),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 1,
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": copy["title"],
                                        "size": "sm",
                                        "weight": "bold",
                                        "wrap": True,
                                    },
                                    {
                                        "type": "text",
                                        "text": copy["subtitle"],
                                        "size": "xxs",
                                        "color": "#8A8A8A",
                                        "wrap": True,
                                        "margin": "xs",
                                    },
                                ],
                            },
                        ],
                    },
                    {"type": "separator", "color": "#ECEAF0", "margin": "lg"},
                    *rows,
                    {
                        "type": "text",
                        "text": copy["hint"],
                        "size": "xxs",
                        "color": "#AAAAAA",
                        "align": "center",
                        "wrap": True,
                        "margin": "lg",
                    },
                ],
            },
        },
    }
