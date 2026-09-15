"""Reconcile LINE's per-user menu with the current binding and query permission.

Rich menus are per OA, so every read/write here resolves the binding's ``channel_key`` and uses
that OA's access token and menu names. A task that only carries a LINE user id (legacy queued
work) falls back to the legacy OA.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from services.line_dms import binding_guard, query_access, rich_menu, store
from services.line_platform import channels
from services.line_platform import client as line_client

logger = logging.getLogger(__name__)


def _request(method: str, path: str, channel: str):
    token = line_client._get_channel_token(channel)
    if not token:
        raise RuntimeError("dms_menu_channel_unavailable")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/" + path,
        headers={"Authorization": f"Bearer {token}"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        if method == "GET" and exc.code == 404:
            return {}
        raise RuntimeError(f"dms_menu_http_{exc.code}") from None


def _allowed(line_user_id: str, channel: str) -> bool:
    binding = store.get_binding_by_line_user(line_user_id, channel)
    return bool(binding and binding_guard.current(binding) and query_access.can_query(binding))


def sync(line_user_id: str, channel_key: str = "") -> None:
    """Read current permission at execution, never use queued permission snapshots."""
    if not line_user_id:
        return
    channel = channels.resolve(channel_key)
    if channel is None:
        raise RuntimeError("dms_menu_channel_unknown")
    basic_name, query_name = rich_menu.menu_names(channel)
    menus = {m.get("name"): m.get("richMenuId") for m in rich_menu._list_menus(channel)}
    basic, query = menus.get(basic_name), menus.get(query_name)
    if not basic or not query:
        raise RuntimeError("dms_permission_menus_not_published")
    path = "user/" + urllib.parse.quote(line_user_id, safe="") + "/richmenu"
    for _ in range(3):
        allowed = _allowed(line_user_id, channel)
        wanted = query if allowed else basic
        existing = _request("GET", path, channel).get("richMenuId")
        if existing != wanted:
            _request("POST", path + "/" + urllib.parse.quote(wanted, safe=""), channel)
        if allowed == _allowed(line_user_id, channel):
            return
    raise RuntimeError("dms_menu_permission_changed_during_sync")


def request_sync(line_user_id: str, channel_key: str = "") -> None:
    from services.cloud_tasks import dispatch

    if not line_user_id:
        return
    channel = channels.resolve(channel_key)
    if channel is None:
        logger.error("DMS menu sync skipped: unknown channel_key")
        return
    try:
        if dispatch.enabled():
            dispatch.enqueue("dms.menu_sync", line_user_id, channel)
        else:
            sync(line_user_id, channel)
    except Exception:
        logger.exception("DMS menu reconciliation pending")


def sync_user(user_id: str) -> None:
    binding = store.get_binding_by_user(str(user_id))
    if binding:
        request_sync(binding["line_user_id"], binding.get("channel_key") or "")


def reconcile() -> None:
    """Periodic repair complements immediate bind/permission-change deliveries."""
    from core import db

    after_line, after_channel = "", ""
    while True:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT line_user_id, channel_key FROM line_dms_bindings "
                "WHERE (line_user_id, channel_key) > (%s, %s) "
                "ORDER BY line_user_id, channel_key LIMIT 100",
                (after_line, after_channel),
            )
            rows = cur.fetchall()
        for row in rows:
            request_sync(row["line_user_id"], row.get("channel_key") or "")
        if len(rows) < 100:
            return
        after_line = rows[-1]["line_user_id"]
        after_channel = rows[-1].get("channel_key") or ""
