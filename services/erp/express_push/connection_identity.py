"""Safe Companion-facing identity for one Express endpoint."""

from __future__ import annotations

import logging
from typing import Any, Dict

from core import db

logger = logging.getLogger(__name__)


def connection_identity(endpoint: Dict[str, Any]) -> Dict[str, str]:
    user = db.find_user_by_id(str(endpoint.get("user_id") or "")) or {}
    account = str(user.get("username") or user.get("email") or "").strip()
    return {
        "endpoint_id": str(endpoint.get("id") or ""),
        "endpoint_name": str(endpoint.get("name") or "Express").strip() or "Express",
        "pearnly_account": account,
    }


def endpoint_connection_identity(endpoint_id: str) -> Dict[str, str]:
    endpoint = _read_endpoint(endpoint_id) or {"id": endpoint_id, "name": "Express"}
    return connection_identity(endpoint)


def _read_endpoint(endpoint_id: str):
    if not endpoint_id:
        return None
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, user_id
                FROM erp_endpoints
                WHERE id = %s AND adapter = 'express'
                LIMIT 1
                """,
                (endpoint_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as exc:
        logger.error("get Express connection identity failed: %s", exc)
        return None


__all__ = ["connection_identity", "endpoint_connection_identity"]
