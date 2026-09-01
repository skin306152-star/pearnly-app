"""Dedicated LINE ERP navigation card."""

from __future__ import annotations

from urllib.parse import urlencode

from services.line_dms.menu_cards import (
    THEME_GREEN,
    THEME_PURPLE,
    menu_icon_disc,
    menu_item,
)


def _action(mode: str, title: str) -> dict:
    return {
        "type": "postback",
        "data": urlencode({"a": f"mode:{mode}"}),
        "displayText": title,
    }


def _entry(
    num: str,
    icon: str,
    title: str,
    description: str,
    mode: str,
    theme: dict[str, str],
    allowed: set[str],
) -> dict | None:
    if mode not in allowed:
        return None
    return menu_item(
        num,
        icon,
        theme,
        title,
        description,
        _action(mode, title),
    )


def menu_card(modes=("purchase", "sales")) -> dict:
    """Render the two available workflows as full-width rows."""
    allowed = set(modes or ())
    entries = [
        _entry(
            "1",
            "erp-purchase",
            "ซื้อ",
            "บันทึกเอกสารซื้อและเพิ่มสินค้าเข้าสต๊อก",
            "purchase",
            THEME_GREEN,
            allowed,
        ),
        _entry(
            "2",
            "erp-sales",
            "ขาย",
            "บันทึกเอกสารขายและตัดสินค้าออกจากสต๊อก",
            "sales",
            THEME_PURPLE,
            allowed,
        ),
    ]
    body = [
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
                            "text": "เลือกประเภทเอกสาร ERP",
                            "weight": "bold",
                            "size": "lg",
                            "wrap": True,
                        },
                        {
                            "type": "text",
                            "text": "เลือกรายการก่อนส่งรูปภาพหรือ PDF",
                            "size": "xxs",
                            "color": "#8A8A8A",
                            "wrap": True,
                            "margin": "xs",
                        },
                    ],
                },
            ],
        },
        {"type": "separator", "margin": "lg", "color": "#EEEEF4"},
        *(entry for entry in entries if entry),
        {
            "type": "text",
            "text": "พิมพ์ เมนู เพื่อเลือกใหม่ได้ตลอดเวลา",
            "size": "xxs",
            "color": "#AAAAAA",
            "align": "center",
            "wrap": True,
            "margin": "lg",
        },
    ]
    return {
        "type": "flex",
        "altText": "เลือกประเภทเอกสาร ERP",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": body,
            },
        },
    }


__all__ = ["menu_card"]
