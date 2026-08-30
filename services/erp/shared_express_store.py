# -*- coding: utf-8 -*-
"""Read-only data access and safe status projection for shared Express endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, Request

from core import db
from services.authz.resolver import resolve
from services.erp.shared_express_schema import enable_shared_express_select

logger = logging.getLogger(__name__)

_ONLINE_SECONDS = 180
_VIEW_PERMISSION = "erp.endpoint.view"


def _hidden() -> HTTPException:
    return HTTPException(404, detail="authz.not_found")


def _unavailable() -> HTTPException:
    return HTTPException(503, detail="erp.shared_endpoint_unavailable")


def _row_value(row: Any, key: str):
    if hasattr(row, "get"):
        return row.get(key)
    return None


def _requested_workspace(request: Request) -> tuple[bool, int | None]:
    headers = getattr(request, "headers", None)
    raw = headers.get("X-Workspace-Client-Id") if headers is not None else None
    if raw is None:
        return False, None
    try:
        workspace_id = int(str(raw).strip())
    except (TypeError, ValueError):
        raise _hidden()
    if workspace_id <= 0:
        raise _hidden()
    return True, workspace_id


def _resolve_active_workspace(cur, request: Request, tenant_id: str) -> int:
    explicit, workspace_id = _requested_workspace(request)
    if explicit:
        cur.execute(
            "SELECT id FROM workspace_clients "
            "WHERE tenant_id = %s AND id = %s AND is_active = TRUE LIMIT 1",
            (tenant_id, workspace_id),
        )
    else:
        cur.execute(
            "SELECT id FROM workspace_clients "
            "WHERE tenant_id = %s AND is_active = TRUE "
            "ORDER BY created_at ASC, id ASC LIMIT 1",
            (tenant_id,),
        )
    row = cur.fetchone()
    if not row or _row_value(row, "id") is None:
        raise _hidden()
    return int(_row_value(row, "id"))


def fetch_visible_endpoint_rows(
    cur,
    *,
    actor_id: str,
    tenant_id: str,
    workspace_client_id: int,
) -> List[Dict[str, Any]]:
    """Merge actor legacy rows with this workspace's active shared Express row."""
    cur.execute(
        """
        SELECT id, name, adapter, config, is_default, auto_push, enabled,
               last_used_at, last_status, success_count, failure_count,
               created_at, updated_at, user_id, tenant_id,
               workspace_client_id, shared_scope
        FROM erp_endpoints
        WHERE (
            user_id = %s
            AND binding_generation = 0
            AND (tenant_id IS NULL OR tenant_id = %s)
            AND (workspace_client_id IS NULL OR workspace_client_id = %s)
        ) OR (
            tenant_id = %s
            AND workspace_client_id = %s
            AND adapter = 'express'
            AND enabled = TRUE
            AND shared_scope = TRUE
        )
        ORDER BY is_default DESC, created_at ASC
        """,
        (
            actor_id,
            tenant_id,
            workspace_client_id,
            tenant_id,
            workspace_client_id,
        ),
    )
    return [dict(row) for row in cur.fetchall()]


def list_visible_endpoints(
    request: Request, user: dict
) -> Tuple[List[Dict[str, Any]], datetime, bool]:
    """Read the shared view inside one tenant/user/workspace-bound transaction."""
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    if not tenant_id or not actor_id:
        raise _hidden()
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id) as cur:
            workspace_id = _resolve_active_workspace(cur, request, tenant_id)
            authz = resolve(user, cur=cur)
            if authz.membership_id is None:
                raise _hidden()
            if not authz.has(_VIEW_PERMISSION):
                raise HTTPException(403, detail="authz.forbidden")
            if not authz.allows_workspace(workspace_id):
                raise _hidden()

            cur.execute(
                "SELECT set_config('app.current_workspace_id', %s, true)",
                (str(workspace_id),),
            )
            if not enable_shared_express_select(cur, tenant_id, workspace_id):
                raise _unavailable()

            cur.execute("SELECT clock_timestamp() AS server_now")
            now_row = cur.fetchone()
            server_now = _parse_time(_row_value(now_row, "server_now"))
            if server_now is None:
                raise _unavailable()
            rows = fetch_visible_endpoint_rows(
                cur,
                actor_id=actor_id,
                tenant_id=tenant_id,
                workspace_client_id=workspace_id,
            )
            may_manage = authz.role_key == "owner" and authz.has("erp.endpoint.manage")
            return rows, server_now, may_manage
    except HTTPException:
        raise
    except Exception:
        logger.exception("shared Express endpoint read failed")
        raise _unavailable()


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _config_text(config: dict, key: str, limit: int) -> str:
    value = config.get(key)
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _connection_state(endpoint: Dict[str, Any], server_now: datetime) -> str:
    if endpoint.get("enabled") is not True:
        return "disabled"
    if str(endpoint.get("adapter") or "").strip().lower() != "express":
        return "online"

    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    if not config.get("agent_token_hash"):
        return "unpaired"
    raw_seen = config.get("agent_last_seen_at")
    if raw_seen in (None, ""):
        return "pairing"
    seen = _parse_time(raw_seen)
    now = _parse_time(server_now)
    if seen is None or now is None:
        return "needs_attention"
    if not _config_text(config, "account_set", 120):
        return "needs_attention"
    return "online" if (now - seen).total_seconds() < _ONLINE_SECONDS else "offline"


def safe_endpoint_dto(endpoint: Dict[str, Any], server_now: datetime) -> Dict[str, Any]:
    """Project the employee-safe allowlist; raw config never crosses this boundary."""
    config = endpoint.get("config") if isinstance(endpoint.get("config"), dict) else {}
    label = _config_text(config, "account_set_label", 120) or _config_text(
        config, "account_set", 120
    )
    seen = _parse_time(config.get("agent_last_seen_at"))
    version = _config_text(config, "companion_version", 40) or None
    return {
        "id": str(endpoint.get("id") or ""),
        "name": str(endpoint.get("name") or "")[:80],
        "adapter": str(endpoint.get("adapter") or "").strip().lower(),
        "enabled": endpoint.get("enabled") is True,
        "shared_scope": endpoint.get("shared_scope") is True,
        "account_set": label or None,
        "connection_state": _connection_state(endpoint, server_now),
        "last_seen_at": seen.isoformat() if seen is not None else None,
        "agent_version": version,
    }


__all__ = [
    "fetch_visible_endpoint_rows",
    "list_visible_endpoints",
    "safe_endpoint_dto",
]
