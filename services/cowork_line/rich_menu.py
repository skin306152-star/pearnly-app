"""Cowork LINE six-cell Rich Menu with one active workflow entry."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import urllib.request
from typing import Any

from services.cowork_line.menu_cards import ACTION_ERP_START
from services.line_binding import line_client

logger = logging.getLogger(__name__)

MENU_NAME = "pearnly-cowork-v1"
IMAGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "static"
    / "brand"
    / "line-richmenu-cowork-v1-2500x1686.png"
)
WIDTH, HEIGHT = 2500, 1686
ROW_HEIGHT = 843
COLUMN_EDGES = (0, 833, 1666, 2500)
CHANNEL = "default"


def build_payload() -> dict[str, Any]:
    return {
        "size": {"width": WIDTH, "height": HEIGHT},
        "selected": False,
        "name": MENU_NAME,
        "chatBarText": "เมนู Cowork",
        "areas": [
            {
                "bounds": {
                    "x": COLUMN_EDGES[0],
                    "y": 0,
                    "width": COLUMN_EDGES[1] - COLUMN_EDGES[0],
                    "height": ROW_HEIGHT,
                },
                "action": {
                    "type": "postback",
                    "data": f"action={ACTION_ERP_START}",
                    "displayText": "ส่งเอกสารเข้า ERP",
                },
            }
        ],
    }


def _token() -> str:
    return line_client._get_channel_token(CHANNEL)


def _list_menus() -> list[dict[str, Any]]:
    token = _token()
    if not token:
        return []
    request = urllib.request.Request(
        "https://api.line.me/v2/bot/richmenu/list",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8")).get("richmenus", [])
    except Exception:
        logger.exception("Could not list Cowork LINE Rich Menus")
        return []


def _delete_menu(rich_menu_id: str) -> bool:
    token = _token()
    if not token or not rich_menu_id:
        return False
    request = urllib.request.Request(
        f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status == 200
    except Exception:
        logger.exception("Could not delete Cowork LINE Rich Menu")
        return False


def _upload_image(rich_menu_id: str, image: bytes) -> bool:
    token = _token()
    if not token or not rich_menu_id or not image:
        return False
    request = urllib.request.Request(
        f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
        data=image,
        headers={"Content-Type": "image/png", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status == 200
    except Exception:
        logger.exception("Could not upload Cowork LINE Rich Menu image")
        return False


def _set_default(rich_menu_id: str) -> bool:
    token = _token()
    if not token or not rich_menu_id:
        return False
    request = urllib.request.Request(
        f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status == 200
    except Exception:
        logger.exception("Could not set Cowork LINE Rich Menu as default")
        return False


def setup_default_menu(image_path: str | Path | None = None) -> str | None:
    path = Path(image_path) if image_path else IMAGE_PATH
    try:
        image = path.read_bytes()
    except OSError:
        logger.exception("Could not read Cowork LINE Rich Menu image")
        return None
    old_ids = [
        str(menu.get("richMenuId") or "") for menu in _list_menus() if menu.get("name") == MENU_NAME
    ]
    rich_menu_id = line_client.create_rich_menu(build_payload(), channel=CHANNEL)
    if not rich_menu_id:
        return None
    if not _upload_image(rich_menu_id, image) or not _set_default(rich_menu_id):
        _delete_menu(rich_menu_id)
        return None
    for old_id in old_ids:
        if old_id and old_id != rich_menu_id:
            _delete_menu(old_id)
    return rich_menu_id
