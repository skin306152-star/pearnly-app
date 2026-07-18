# -*- coding: utf-8 -*-
"""DMS LINE 菜单卡(波2):入口菜单 + 建档后的继续订车卡。

布局照泰方认可的 ChatGPT mockup:标题区 + 两张整行可点的行卡(编号圆徽+图标+标题
两行说明+箭头)。从 cards.py 拆出保 500 行硬门;文案/动作名仍以 cards 为单一来源。
"""

from __future__ import annotations

from typing import Any, Dict

from services.line_dms.cards import (
    ACT_CONTINUE_BOOKING,
    ACT_MENU_BOOKING,
    ACT_MENU_CUSTOMER,
    BTN_CONTINUE_BOOKING,
    TXT_CONTINUE_HINT,
    TXT_CONTINUE_SAME,
    TXT_CONTINUE_SAVED,
    TXT_MENU_D1,
    TXT_MENU_D2,
    TXT_MENU_ITEM1,
    TXT_MENU_ITEM2,
    TXT_MENU_HINT,
    TXT_MENU_PICK,
    TXT_MENU_PICK_SUB,
    TXT_MENU_TITLE,
    _btn,
    _data,
)

# ── 菜单层(波2) ──────────────────────────────────────────────────────────
# 图标托管在自家 static(LINE Flex 的图片必须是公网 https URL);?v 随图变更 bump。
_MENU_ICON_BASE = "https://pearnly.com/static/dms/line-icons"


def _menu_icon_disc(icon: str, soft: str, size: str, img: str) -> Dict[str, Any]:
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


def _menu_item(
    num: str, icon: str, accent: str, soft: str, border: str, title: str, desc: str, action: str
) -> Dict[str, Any]:
    """整行可点的菜单项(postback 无 nonce):编号圆徽 + 图标 + 标题两行说明 + 箭头。"""
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "margin": "md",
        "cornerRadius": "14px",
        "borderColor": border,
        "borderWidth": "1px",
        "paddingAll": "14px",
        "alignItems": "center",
        "action": {"type": "postback", "data": action},
        "contents": [
            _menu_icon_disc(icon, soft, "46px", "26px"),
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
            {
                "type": "text",
                "text": "›",
                "size": "xl",
                "color": accent,
                "flex": 0,
                "gravity": "center",
            },
        ],
    }


def menu_card() -> Dict[str, Any]:
    """入口菜单(照泰方认可的 mockup):标题区 + 两张整行可点的行卡。点旧卡安全。"""
    head = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "alignItems": "center",
        "contents": [
            _menu_icon_disc("menu-head", "#eaf0ff", "40px", "22px"),
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
            _menu_item(
                "1",
                "menu-1",
                "#2f6bff",
                "#eaf0ff",
                "#dfe7ff",
                TXT_MENU_ITEM1,
                TXT_MENU_D1,
                _data(ACT_MENU_CUSTOMER),
            ),
            _menu_item(
                "2",
                "menu-2",
                "#f25c6e",
                "#fdecef",
                "#f9d9de",
                TXT_MENU_ITEM2,
                TXT_MENU_D2,
                _data(ACT_MENU_BOOKING),
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


def continue_booking_card(customer_id: str, same_data: bool = False) -> Dict[str, Any]:
    """建档落定(customer 模式)后问是否继续订车:cid 绑进 postback,继续时校验防串档。"""
    intro = TXT_CONTINUE_SAME if same_data else TXT_CONTINUE_SAVED
    return {
        "type": "flex",
        "altText": BTN_CONTINUE_BOOKING,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": intro, "size": "sm", "wrap": True},
                    {
                        "type": "text",
                        "text": TXT_CONTINUE_HINT,
                        "size": "xs",
                        "color": "#8a8a8a",
                        "wrap": True,
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    _btn(
                        BTN_CONTINUE_BOOKING,
                        _data(ACT_CONTINUE_BOOKING, cid=str(customer_id or "")),
                        "primary",
                    )
                ],
            },
        },
    }
