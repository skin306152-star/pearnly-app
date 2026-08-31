# -*- coding: utf-8 -*-
"""DMS LINE 菜单卡：四个入口行卡。

布局照泰方认可的 ChatGPT mockup:标题区 + 三张整行可点的行卡(编号圆徽+图标+标题
两行说明+箭头)。从 cards.py 拆出保 500 行硬门;文案/动作名仍以 cards 为单一来源。
"""

from __future__ import annotations

from typing import Any, Dict

from services.line_dms.cards import (
    ACT_MENU_BOOKING,
    ACT_MENU_CUSTOMER,
    TXT_MENU_D1,
    TXT_MENU_D2,
    TXT_MENU_D3,
    TXT_MENU_D4,
    TXT_MENU_ITEM1,
    TXT_MENU_ITEM2,
    TXT_MENU_ITEM3,
    TXT_MENU_ITEM4,
    TXT_MENU_HINT,
    TXT_MENU_PICK,
    TXT_MENU_PICK_SUB,
    TXT_MENU_TITLE,
    _data,
)
from services.line_dms.rich_menu import (
    credentials_desktop_url,
    credentials_external_url,
    portal_desktop_url,
    portal_external_url,
)

# ── 菜单层(波2) ──────────────────────────────────────────────────────────
# 图标托管在自家 static(LINE Flex 的图片必须是公网 https URL);?v 随图变更 bump。
_MENU_ICON_BASE = "https://pearnly.com/static/dms/line-icons"


def menu_icon_disc(icon: str, soft: str, size: str, img: str) -> Dict[str, Any]:
    return {
        "type": "box",
        "layout": "vertical",
        "width": size,
        "height": size,
        "cornerRadius": "999px",
        "backgroundColor": soft,
        "justifyContent": "center",
        "alignItems": "center",
        "contents": [{"type": "image", "url": f"{_MENU_ICON_BASE}/{icon}.png?v=1", "size": img}],
    }


# 行卡配色主题(accent 编号/箭头 · soft 图标圆底 · border 卡边)。
THEME_BLUE = {"accent": "#2f6bff", "soft": "#eaf0ff", "border": "#dfe7ff"}
THEME_PINK = {"accent": "#f25c6e", "soft": "#fdecef", "border": "#f9d9de"}
THEME_PURPLE = {"accent": "#7656d6", "soft": "#f0ebff", "border": "#e5dcff"}
THEME_GREEN = {"accent": "#198c6a", "soft": "#e8f7f1", "border": "#d3eee4"}


def menu_item(
    num: str,
    icon: str,
    theme: Dict[str, str],
    title: str,
    desc: str,
    action: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """整行可点的菜单项：编号圆徽、图标、标题说明和箭头。"""
    accent = theme["accent"]
    row = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "margin": "md",
        "cornerRadius": "14px",
        "borderColor": theme["border"],
        "borderWidth": "1px",
        "paddingAll": "14px",
        "alignItems": "center",
        "contents": [
            menu_icon_disc(icon, theme["soft"], "46px", "26px"),
            {
                "type": "text",
                "text": num,
                "size": "xxl",
                "weight": "bold",
                "color": accent,
                "flex": 0,
                "gravity": "center",
            },
            {
                "type": "box",
                "layout": "vertical",
                "flex": 1,
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "size": "sm",
                        "weight": "bold",
                        "color": "#1b1b2b",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": desc,
                        "size": "xxs",
                        "color": "#8a8a8a",
                        "wrap": True,
                        "margin": "xs",
                    },
                ],
            },
        ],
    }
    if action:
        row["action"] = action
        row["contents"].append(
            {
                "type": "text",
                "text": "›",
                "size": "xl",
                "color": accent,
                "flex": 0,
                "gravity": "center",
            }
        )
    return row


def menu_card() -> Dict[str, Any]:
    """入口菜单(照泰方认可的 mockup):标题区 + 四张整行可点的行卡。"""
    head = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "alignItems": "center",
        "contents": [
            menu_icon_disc("menu-head", "#eaf0ff", "40px", "22px"),
            {
                "type": "box",
                "layout": "vertical",
                "flex": 1,
                "contents": [
                    {
                        "type": "text",
                        "text": TXT_MENU_PICK,
                        "size": "sm",
                        "weight": "bold",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": TXT_MENU_PICK_SUB,
                        "size": "xxs",
                        "color": "#8a8a8a",
                        "wrap": True,
                        "margin": "xs",
                    },
                ],
            },
        ],
    }
    body = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "16px",
        "contents": [
            head,
            {"type": "separator", "margin": "lg", "color": "#eeeef4"},
            menu_item(
                "1",
                "menu-1",
                THEME_BLUE,
                TXT_MENU_ITEM1,
                TXT_MENU_D1,
                {"type": "postback", "data": _data(ACT_MENU_CUSTOMER)},
            ),
            menu_item(
                "2",
                "menu-2",
                THEME_PINK,
                TXT_MENU_ITEM2,
                TXT_MENU_D2,
                {"type": "postback", "data": _data(ACT_MENU_BOOKING)},
            ),
            menu_item(
                "3",
                "menu-3",
                THEME_PURPLE,
                TXT_MENU_ITEM3,
                TXT_MENU_D3,
                {
                    "type": "uri",
                    "label": TXT_MENU_ITEM3,
                    "uri": portal_external_url(),
                    "altUri": {"desktop": portal_desktop_url()},
                },
            ),
            menu_item(
                "4",
                "menu-4",
                THEME_GREEN,
                TXT_MENU_ITEM4,
                TXT_MENU_D4,
                {
                    "type": "uri",
                    "label": TXT_MENU_ITEM4,
                    "uri": credentials_external_url(),
                    "altUri": {"desktop": credentials_desktop_url()},
                },
            ),
            {
                "type": "text",
                "text": TXT_MENU_HINT,
                "size": "xxs",
                "color": "#aaaaaa",
                "align": "center",
                "wrap": True,
                "margin": "lg",
            },
        ],
    }
    return {"type": "flex", "altText": TXT_MENU_TITLE, "contents": {"type": "bubble", "body": body}}
