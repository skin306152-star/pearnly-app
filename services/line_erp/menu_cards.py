"""Dedicated LINE ERP navigation card."""

from __future__ import annotations

from urllib.parse import urlencode

from services.line_dms.menu_cards import THEME_GREEN, THEME_PURPLE, menu_icon_disc


def _menu_tile(
    num: str,
    icon: str,
    title: str,
    description: str,
    action: str,
    theme: dict[str, str],
) -> dict:
    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "height": "124px",
        "paddingAll": "12px",
        "cornerRadius": "14px",
        "borderWidth": "1px",
        "borderColor": theme["border"],
        "backgroundColor": "#FFFFFF",
        "action": {
            "type": "postback",
            "data": urlencode({"a": action}),
            "displayText": title,
        },
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    menu_icon_disc(icon, theme["soft"], "38px", "22px"),
                    {"type": "filler"},
                    {
                        "type": "text",
                        "text": num,
                        "size": "lg",
                        "weight": "bold",
                        "color": theme["accent"],
                        "flex": 0,
                    },
                ],
            },
            {"type": "text", "text": title, "size": "sm", "weight": "bold", "margin": "sm"},
            {
                "type": "text",
                "text": description,
                "size": "xxs",
                "color": "#8A8A8A",
                "wrap": True,
                "margin": "xs",
            },
        ],
    }


def _placeholder() -> dict:
    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "height": "124px",
        "paddingAll": "12px",
        "cornerRadius": "14px",
        "borderWidth": "1px",
        "borderColor": "#EEEEF4",
        "backgroundColor": "#F8F8FA",
        "contents": [{"type": "filler"}],
    }


def _grid(modes: tuple[str, ...]) -> dict:
    allowed = set(modes or ())
    cells = [
        (
            _menu_tile(
                "1",
                "erp-purchase",
                "ซื้อ",
                "บันทึกเอกสารซื้อและเพิ่มสินค้าเข้าสต๊อก",
                "mode:purchase",
                THEME_GREEN,
            )
            if "purchase" in allowed
            else _placeholder()
        ),
        (
            _menu_tile(
                "2",
                "erp-sales",
                "ขาย",
                "บันทึกเอกสารขายและตัดสินค้าออกจากสต๊อก",
                "mode:sales",
                THEME_PURPLE,
            )
            if "sales" in allowed
            else _placeholder()
        ),
        *(_placeholder() for _ in range(4)),
    ]
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "margin": "lg",
        "contents": [
            {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": cells[0:2]},
            {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": cells[2:4]},
            {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": cells[4:6]},
        ],
    }


def menu_card(modes=("purchase", "sales")) -> dict:
    """Render navigation independently; target readiness runs after mode selection."""
    return {
        "type": "flex",
        "altText": "เลือกประเภทเอกสาร ERP",
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
                    _grid(tuple(modes or ())),
                    {
                        "type": "text",
                        "text": "พิมพ์ เมนู เพื่อเลือกใหม่ได้ตลอดเวลา",
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


__all__ = ["menu_card"]
