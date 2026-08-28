# -*- coding: utf-8 -*-
"""DMS LINE OA 的独立 Rich Menu。"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Optional

from services.line_binding import line_client

logger = logging.getLogger(__name__)

MENU_NAME = "pearnly-dms-v1"
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


def portal_liff_url() -> str:
    """返回公开 LIFF 入口；没有 LIFF 配置时退回普通 DMS 登录。"""
    liff_id = (os.environ.get("LINE_DMS_LIFF_ID") or "").strip() or (
        os.environ.get("LINE_LIFF_ID") or ""
    ).strip()
    if liff_id:
        query = urllib.parse.urlencode({"portal": "dms"})
        return f"https://liff.line.me/{liff_id}?{query}"
    return "https://pearnly.com/dms"


def credentials_liff_url() -> str:
    """Open the self-service credential editor in the same DMS LIFF app."""
    liff_id = (os.environ.get("LINE_DMS_LIFF_ID") or "").strip() or (
        os.environ.get("LINE_LIFF_ID") or ""
    ).strip()
    if liff_id:
        query = urllib.parse.urlencode({"credentials": "dms"})
        return f"https://liff.line.me/{liff_id}?{query}"
    return "https://pearnly.com/dms"


def build_payload() -> dict:
    return {
        "size": {"width": _W, "height": _H},
        "selected": False,
        "name": MENU_NAME,
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
                {"type": "uri", "label": "เข้าสู่ DMS", "uri": portal_liff_url()},
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
        ],
    }


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
    """安全替换 DMS 默认菜单；新菜单生效前不删除旧菜单。"""
    path = image_path or _IMAGE_PATH
    try:
        with open(path, "rb") as image_file:
            image = image_file.read()
    except OSError as exc:
        logger.error("DMS Rich Menu image read failed: %s", exc)
        return None

    old_ids = [menu.get("richMenuId") for menu in _list_menus() if menu.get("name") == MENU_NAME]
    rich_menu_id = line_client.create_rich_menu(build_payload(), channel="dms")
    if not rich_menu_id:
        return None
    mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    if not _upload_image(rich_menu_id, image, mime) or not _set_default(rich_menu_id):
        _delete_menu(rich_menu_id)
        return None

    for old_id in old_ids:
        if old_id and old_id != rich_menu_id:
            _delete_menu(old_id)
    logger.info("DMS Rich Menu published: %s", rich_menu_id)
    return rich_menu_id
