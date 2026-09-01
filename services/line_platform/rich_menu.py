"""Shared LINE Rich Menu publication helpers."""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from services.line_platform import client as line_client

logger = logging.getLogger(__name__)


def _request(
    channel: str,
    url: str,
    method: str,
    *,
    data: bytes | None = None,
    content_type: str | None = None,
) -> bytes | None:
    token = line_client._get_channel_token(channel)
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    except Exception:
        logger.exception("LINE Rich Menu request failed: channel=%s method=%s", channel, method)
        return None


def list_menus(channel: str) -> list[dict[str, Any]]:
    body = _request(channel, "https://api.line.me/v2/bot/richmenu/list", "GET")
    if body is None:
        return []
    try:
        return json.loads(body.decode("utf-8")).get("richmenus", [])
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.exception("LINE Rich Menu list response was not JSON: channel=%s", channel)
        return []


def delete_menu(channel: str, rich_menu_id: str) -> bool:
    if not rich_menu_id:
        return False
    return (
        _request(
            channel,
            f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}",
            "DELETE",
        )
        is not None
    )


def upload_image(
    channel: str,
    rich_menu_id: str,
    image: bytes,
    content_type: str = "image/png",
) -> bool:
    if not rich_menu_id or not image:
        return False
    return (
        _request(
            channel,
            f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
            "POST",
            data=image,
            content_type=content_type,
        )
        is not None
    )


def set_default(channel: str, rich_menu_id: str) -> bool:
    if not rich_menu_id:
        return False
    return (
        _request(
            channel,
            f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
            "POST",
        )
        is not None
    )


def replace_default(
    channel: str,
    menu_name: str,
    payload: dict[str, Any],
    image: bytes,
    content_type: str = "image/png",
) -> str | None:
    """Publish first, then remove superseded menus with the same product name."""
    old_ids = [
        str(menu.get("richMenuId") or "")
        for menu in list_menus(channel)
        if menu.get("name") == menu_name
    ]
    rich_menu_id = line_client.create_rich_menu(payload, channel=channel)
    if not rich_menu_id:
        return None
    if not upload_image(channel, rich_menu_id, image, content_type) or not set_default(
        channel, rich_menu_id
    ):
        delete_menu(channel, rich_menu_id)
        return None
    for old_id in old_ids:
        if old_id and old_id != rich_menu_id:
            delete_menu(channel, old_id)
    return rich_menu_id


__all__ = ["delete_menu", "list_menus", "replace_default", "set_default", "upload_image"]
