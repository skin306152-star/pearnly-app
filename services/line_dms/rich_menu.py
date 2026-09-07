# -*- coding: utf-8 -*-
"""DMS LINE OA 的独立 Rich Menu。"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Optional

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


def _entry_url(mode: str, *, external: bool) -> str:
    liff_id = (os.environ.get("LINE_DMS_LIFF_ID") or "").strip() or (
        os.environ.get("LINE_LIFF_ID") or ""
    ).strip()
    if liff_id:
        params = {mode: "dms"}
        if external:
            params["openExternalBrowser"] = "1"
        query = urllib.parse.urlencode(params)
        return f"https://pearnly.com/home/dms-booking?{query}"
    return "https://pearnly.com/dms"


def portal_external_url() -> str:
    """Open menu 3 in the system browser before LIFF authentication starts."""
    return _entry_url("portal", external=True)


def portal_desktop_url() -> str:
    """Desktop LINE already opens URI actions in the default browser."""
    return _entry_url("portal", external=False)


def credentials_liff_url() -> str:
    """Open only the mobile credential editor inside LINE; portal stays external."""
    liff_id = (os.environ.get("LINE_DMS_LIFF_ID") or "").strip() or (
        os.environ.get("LINE_LIFF_ID") or ""
    ).strip()
    if liff_id:
        return f"https://liff.line.me/{liff_id}/dms-booking?credentials=dms"
    return "https://pearnly.com/dms"


def credentials_desktop_url() -> str:
    """Open menu 4 directly in the macOS or Windows default browser."""
    return _entry_url("credentials", external=False)


def build_payload(can_query: bool = False) -> dict:
    payload = {
        "size": {"width": _W, "height": _H},
        "selected": False,
        "name": QUERY_MENU_NAME if can_query else MENU_NAME,
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
                {"type": "uri", "label": "เข้าสู่ DMS", "uri": portal_external_url()},
            ),
            _area(
                0,
                {
                    "type": "uri",
                    "label": "เปลี่ยนรหัสผ่าน",
                    "uri": credentials_liff_url(),
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


def _list_menus() -> list:
    token = line_client._get_channel_token("dms")
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
        logger.error("LINE listRichMenu(dms) failed: %s", exc)
        return []


def _delete_menu(rich_menu_id: str) -> bool:
    token = line_client._get_channel_token("dms")
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
        logger.error("LINE deleteRichMenu(dms) failed: %s", exc)
        return False


def _upload_image(rich_menu_id: str, image: bytes, content_type: str = "image/png") -> bool:
    token = line_client._get_channel_token("dms")
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
        logger.error("LINE uploadRichMenuImage(dms) failed: %s", exc)
        return False


def _set_default(rich_menu_id: str) -> bool:
    token = line_client._get_channel_token("dms")
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
        logger.error("LINE setDefaultRichMenu(dms) failed: %s", exc)
        return False


def setup_default_menu(image_path: str = None) -> Optional[str]:
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
        menu_id = line_client.create_rich_menu(build_payload(allowed), channel="dms")
        if not menu_id:
            return None
        if not _upload_image(menu_id, image):
            _delete_menu(menu_id)
            return None
        menus[allowed] = menu_id
    if not _set_default(menus[False]):
        return None
    # Existing linked menus remain until reconciliation; never delete another run's menu.
    logger.info("DMS permission menus published")
    return menus[False]
