"""LINE friendship lifecycle for Cowork identities and sessions."""

from __future__ import annotations

import asyncio

from core import db
from services.cowork_line import session_store


def set_session(identity: dict, state: str, payload: dict, ttl_minutes: int = 30) -> None:
    session_store.set_session(
        tenant_id=identity["tenant_id"],
        line_user_id=identity["line_user_id"],
        state=state,
        payload=payload,
        ttl_minutes=ttl_minutes,
    )


def revoke_by_line_user(line_user_id: str) -> dict[str, str] | None:
    line_user_id = str(line_user_id or "").strip()
    if not line_user_id:
        return None
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            SELECT membership_id, tenant_id, user_id
            FROM cowork_line_identities
            WHERE line_user_id = %s AND revoked_at IS NULL
            FOR UPDATE
            """,
            (line_user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            """
            UPDATE cowork_line_identities
            SET revoked_at = NOW(),
                friendship_ready = FALSE,
                friendship_checked_at = NOW()
            WHERE membership_id = %s AND revoked_at IS NULL
            """,
            (row["membership_id"],),
        )
        cur.execute(
            """
            UPDATE cowork_line_connect_tokens
            SET used_at = NOW()
            WHERE membership_id = %s AND used_at IS NULL
            """,
            (row["membership_id"],),
        )
    return {
        "membership_id": str(row["membership_id"]),
        "tenant_id": str(row["tenant_id"]),
        "user_id": str(row["user_id"]),
    }


async def disconnect_if_unfollow(event_type: str, line_user_id: str) -> bool:
    if event_type != "unfollow":
        return False
    revoked = await asyncio.to_thread(revoke_by_line_user, line_user_id)
    if revoked:
        await asyncio.to_thread(
            session_store.clear_session,
            tenant_id=revoked["tenant_id"],
            line_user_id=line_user_id,
        )
    return True
