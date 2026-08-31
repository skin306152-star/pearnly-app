"""Tenant-scoped conversation state for the Cowork LINE intake flow."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from core import db

DEFAULT_TTL_MINUTES = 30
PROCESSING_TTL_MINUTES = 15


def _expires_at(ttl_minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=int(ttl_minutes))


def _session(row: Any) -> dict[str, Any] | None:
    if not row:
        return None
    payload = row.get("payload") or {}
    if not isinstance(payload, dict):
        payload = json.loads(payload)
    return {
        "state": str(row["state"]),
        "payload": payload,
        "expires_at": row.get("expires_at"),
    }


def get_session(*, tenant_id: str, line_user_id: str) -> dict[str, Any] | None:
    with db.get_cursor_rls(str(tenant_id)) as cur:
        cur.execute(
            """
            SELECT state, payload, expires_at
            FROM cowork_line_sessions
            WHERE tenant_id = %s
              AND line_user_id = %s
              AND expires_at > NOW()
            """,
            (str(tenant_id), str(line_user_id)),
        )
        return _session(cur.fetchone())


def set_session(
    *,
    tenant_id: str,
    line_user_id: str,
    state: str,
    payload: dict[str, Any] | None = None,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
) -> dict[str, Any] | None:
    expires_at = _expires_at(ttl_minutes)
    with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
        cur.execute(
            """
            INSERT INTO cowork_line_sessions
                (tenant_id, line_user_id, state, payload, expires_at)
            VALUES (%s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (tenant_id, line_user_id) DO UPDATE SET
                state = EXCLUDED.state,
                payload = EXCLUDED.payload,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            RETURNING state, payload, expires_at
            """,
            (
                str(tenant_id),
                str(line_user_id),
                str(state),
                json.dumps(payload or {}, ensure_ascii=False),
                expires_at,
            ),
        )
        return _session(cur.fetchone())


def claim_processing(
    *,
    tenant_id: str,
    line_user_id: str,
    message_id: str,
    expected_state: str = "receiving",
    ttl_minutes: int = PROCESSING_TTL_MINUTES,
) -> dict[str, Any] | None:
    """Atomically reserve one OCR run without replacing existing payload keys."""
    expires_at = _expires_at(ttl_minutes)
    with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
        cur.execute(
            """
            UPDATE cowork_line_sessions
            SET state = 'ocr_processing',
                payload = jsonb_set(
                    payload,
                    '{message_id}',
                    to_jsonb(%s::text),
                    TRUE
                ),
                expires_at = %s,
                updated_at = NOW()
            WHERE tenant_id = %s
              AND line_user_id = %s
              AND state = %s
              AND expires_at > NOW()
            RETURNING state, payload, expires_at
            """,
            (
                str(message_id),
                expires_at,
                str(tenant_id),
                str(line_user_id),
                str(expected_state),
            ),
        )
        return _session(cur.fetchone())


def clear_session(*, tenant_id: str, line_user_id: str) -> bool:
    with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
        cur.execute(
            """
            DELETE FROM cowork_line_sessions
            WHERE tenant_id = %s AND line_user_id = %s
            """,
            (str(tenant_id), str(line_user_id)),
        )
        return cur.rowcount == 1
