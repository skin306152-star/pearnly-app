# -*- coding: utf-8 -*-
"""User preference storage backed by the users table."""

import logging
from typing import Optional

from core import db

logger = logging.getLogger(__name__)


def get_user_dup_check_enabled(user_id: str) -> bool:
    """Return the duplicate-invoice check preference. Defaults to enabled."""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT dup_check_enabled FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return True
            value = row.get("dup_check_enabled")
            return True if value is None else bool(value)
    except Exception:
        return True


def set_user_dup_check_enabled(user_id: str, enabled: bool) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET dup_check_enabled = %s WHERE id = %s",
                (bool(enabled), user_id),
            )
        return True
    except Exception as exc:
        logger.error("set_user_dup_check_enabled failed: %s", exc)
        return False


def set_user_gemini_key(user_id: str, api_key: Optional[str]) -> bool:
    value = (api_key or "").strip() or None
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET gemini_api_key = %s WHERE id = %s", (value, user_id))
        return True
    except Exception as exc:
        logger.error("set_user_gemini_key failed: %s", exc)
        return False


def get_user_gemini_key(user_id: str) -> Optional[str]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT gemini_api_key FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row and row.get("gemini_api_key"):
                return row["gemini_api_key"]
    except Exception as exc:
        logger.warning("get_user_gemini_key failed: %s", exc)
    return None


def get_user_gemini_key_masked(user_id: str) -> dict:
    key = get_user_gemini_key(user_id)
    if not key:
        return {"has_key": False, "preview": ""}
    if len(key) <= 8:
        preview = "*" * len(key)
    else:
        preview = f"{key[:4]}...{key[-4:]}"
    return {"has_key": True, "preview": preview}


def update_user_preferred_lang(user_id: str, lang: str) -> bool:
    if lang not in ("zh", "en", "th", "ja"):
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET preferred_lang = %s WHERE id = %s",
                (lang, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as exc:
        logger.error("update_user_preferred_lang failed: %s", exc)
        return False
