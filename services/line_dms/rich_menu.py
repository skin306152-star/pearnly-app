# -*- coding: utf-8 -*-
"""DMS LINE OA 的独立 Rich Menu(每个 OA 一套,按 channel key 隔离)。"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Optional, Tuple

from services.line_platform import channels
from services.line_platform import client as line_client

logger = logging.getLogger(__name__)

MENU_NAME = "pearnly-dms-basic-v3-liff"
QUERY_MENU_NAME = "pearnly-dms-query-v3-liff"
_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "static",
    "brand",
    "line-richmenu-dms-v1-2500x1686.png",
)
_W, _H = 2500, 1686
_ROW_H = 843
_COL_X = (0, _W // 3, 2 * _W // 3, _W)


def _area(col: int, action: dict, *, row: int = 0) -> dict:
    return {
        "bounds": {
            "x": _COL_X[col],
            "y": row * _ROW_H,
            "width": _COL_X[col + 1] - _COL_X[col],
            "height": _ROW_H,
        },
        "action": action,
    }


def _entry_url(mode: str, *, external: bool, channel: str = "dms") -> str:
    liff_id = channels.liff_id(channel)
    if liff_id:
        params = {mode: "dms", "channel": channels.normalize(channel)}
        if external:
            params["openExternalBrowser"] = "1"
        query = urllib.parse.urlencode(params)
        return f"https://pearnly.com/home/dms-booking?{query}"
    return "https://pearnly.com/dms"


def portal_external_url(channel: str = "dms") -> str:
    """Open menu 3 in the system browser before LIFF authentication starts."""
    return _entry_url("portal", external=True, channel=channel)


def portal_desktop_url(channel: str = "dms") -> str:
    """Desktop LINE already opens URI actions in the default browser."""
    return _entry_url("portal", external=False, channel=channel)


def credentials_liff_url(channel: str = "dms") -> str:
    """Open only the mobile credential editor inside LINE; portal stays external."""
    liff_id = channels.liff_id(channel)
    if liff_id:
        query = urllib.parse.urlencode(
            {"credentials": "dms", "channel": channels.normalize(channel)}
        )
        return f"https://liff.line.me/{liff_id}/dms-booking?{query}"
    return "https://pearnly.com/dms"


def credentials_desktop_url(channel: str = "dms") -> str:
    """Open menu 4 directly in the macOS or Windows default browser."""
    return _entry_url("credentials", external=False, channel=channel)


def build_payload(can_query: bool = False, channel: str = "dms") -> dict:
    payload = {
        "size": {"width": _W, "height": _H},
        "selected": False,
        "name": channels.menu_name(QUERY_MENU_NAME if can_query else MENU_NAME, channel),
        "chatBarText": "เมนู DMS",
        "areas": [
            _area(
                0,
                {
                    "type": "postback",
                    "data": "action=menu_customer",
                    "displayText": "สร้างลูกค้า",
                },
            ),
            _area(
                1,
                {
                    "type": "postback",
                    "data": "action=menu_booking",
                    "displayText": "สร้างการจองรถ",
                },
            ),
            _area(
                2,
                {"type": "uri", "label": "เข้าสู่ DMS", "uri": portal_external_url(channel)},
            ),
            _area(
                0,
                {
                    "type": "uri",
                    "label": "เปลี่ยนรหัสผ่าน",
                    "uri": credentials_liff_url(channel),
                },
                row=1,
            ),
            _area(
                1,
                {
                    "type": "postback",
                    "data": "action=menu_query",
                    "displayText": "ค้นหาข้อมูล",
                },
                row=1,
            ),
        ],
    }

    if not can_query:
        payload["areas"] = payload["areas"][:4]
        for index, area in enumerate(payload["areas"]):
            area["bounds"] = {
                "x": (index % 2) * 1250,
                "y": (index // 2) * _ROW_H,
                "width": 1250,
                "height": _ROW_H,
            }
    return payload


def menu_names(channel: str = "dms") -> Tuple[str, str]:
    """(basic, query) menu names for one OA; other OAs are suffixed to avoid collisions."""
    return (
        channels.menu_name(MENU_NAME, channel),
        channels.menu_name(QUERY_MENU_NAME, channel),
    )


def _list_menus(channel: str = "dms") -> list:
    token = line_client._get_channel_token(channel)
    if not token:
        return []
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/richmenu/list",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")).get("richmenus", [])
    except Exception as exc:  # noqa: BLE001
        logger.error("LINE listRichMenu(%s) failed: %s", channel, exc)
        return []


def _delete_menu(rich_menu_id: str, channel: str = "dms") -> bool:
    token = line_client._get_channel_token(channel)
    if not token or not rich_menu_id:
        return False
    req = urllib.request.Request(
        f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as exc:  # noqa: BLE001
        logger.error("LINE deleteRichMenu(%s) failed: %s", channel, exc)
        return False


def _upload_image(
    rich_menu_id: str, image: bytes, content_type: str = "image/png", channel: str = "dms"
) -> bool:
    token = line_client._get_channel_token(channel)
    if not token or not rich_menu_id or not image:
        return False
    req = urllib.request.Request(
        f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
        data=image,
        headers={"Content-Type": content_type, "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except Exception as exc:  # noqa: BLE001
        logger.error("LINE uploadRichMenuImage(%s) failed: %s", channel, exc)
        return False


def _set_default(rich_menu_id: str, channel: str = "dms") -> bool:
    token = line_client._get_channel_token(channel)
    if not token or not rich_menu_id:
        return False
    req = urllib.request.Request(
        f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as exc:  # noqa: BLE001
        logger.error("LINE setDefaultRichMenu(%s) failed: %s", channel, exc)
        return False


def setup_default_menu(image_path: str = None, channel: str = "dms") -> Optional[str]:
    """Publish both variants; the global default never includes privileged queries."""
    menus = {}
    for allowed, path in (
        (False, image_path or _IMAGE_PATH.replace("v1-", "basic-v2-")),
        (True, _IMAGE_PATH),
    ):
        try:
            with open(path, "rb") as image_file:
                image = image_file.read()
        except OSError:
            logger.exception("DMS Rich Menu image unavailable")
            return None
        menu_id = line_client.create_rich_menu(build_payload(allowed, channel), channel=channel)
        if not menu_id:
            return None
        if not _upload_image(menu_id, image, channel=channel):
            _delete_menu(menu_id, channel)
            return None
        menus[allowed] = menu_id
    if not _set_default(menus[False], channel):
        return None
    # Existing linked menus remain until reconciliation; never delete another run's menu.
    logger.info("DMS permission menus published channel=%s", channel)
    return menus[False]
