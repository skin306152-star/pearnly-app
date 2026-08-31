"""Membership-keyed Cowork LINE identity and one-time binding codes."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg2 import errors

from core import db

DEFAULT_BIND_CODE_TTL_MINUTES = 10


class CoworkLineIdentityError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _active_membership(cur, *, user_id: str, tenant_id: str) -> dict[str, str]:
    cur.execute(
        """
        SELECT m.id, m.user_id, m.tenant_id
        FROM memberships m
        JOIN users u ON u.id = m.user_id
        WHERE m.user_id = %s
          AND m.tenant_id = %s
          AND m.status = 'active'
          AND u.is_active = TRUE
        FOR SHARE OF m, u
        """,
        (user_id, tenant_id),
    )
    row = cur.fetchone()
    if not row:
        raise CoworkLineIdentityError("membership_inactive")
    return {
        "membership_id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "tenant_id": str(row["tenant_id"]),
    }


def issue_binding_code(
    *, user_id: str, tenant_id: str, ttl_minutes: int = DEFAULT_BIND_CODE_TTL_MINUTES
) -> dict[str, str]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    with db.get_cursor(commit=True) as cur:
        membership = _active_membership(cur, user_id=user_id, tenant_id=tenant_id)
        cur.execute(
            """
            UPDATE cowork_line_connect_tokens
            SET used_at = NOW()
            WHERE membership_id = %s AND used_at IS NULL
            """,
            (membership["membership_id"],),
        )
        for _ in range(20):
            code = f"{secrets.randbelow(900000) + 100000}"
            cur.execute(
                """
                INSERT INTO cowork_line_connect_tokens
                    (membership_id, tenant_id, token_hash, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (token_hash) DO NOTHING
                RETURNING expires_at
                """,
                (
                    membership["membership_id"],
                    membership["tenant_id"],
                    _token_hash(code),
                    expires_at,
                ),
            )
            if cur.fetchone():
                return {"code": code, "expires_at": expires_at.isoformat()}
    raise CoworkLineIdentityError("code_unavailable")


def bind_identity_with_code(
    *,
    code: str,
    line_user_id: str,
    display_name: str | None = None,
    picture_url: str | None = None,
) -> dict[str, str] | None:
    code = (code or "").strip()
    line_user_id = (line_user_id or "").strip()
    if len(code) != 6 or not code.isdigit() or not line_user_id:
        return None
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                SELECT t.id, t.membership_id, m.tenant_id, m.user_id, t.expires_at
                FROM cowork_line_connect_tokens t
                JOIN memberships m ON m.id = t.membership_id
                JOIN users u ON u.id = m.user_id
                WHERE t.token_hash = %s
                  AND t.used_at IS NULL
                  AND t.tenant_id = m.tenant_id
                  AND m.status = 'active'
                  AND u.is_active = TRUE
                FOR UPDATE OF t, m, u
                """,
                (_token_hash(code),),
            )
            row = cur.fetchone()
            if not row:
                return None
            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                cur.execute(
                    "UPDATE cowork_line_connect_tokens SET used_at = NOW() WHERE id = %s",
                    (row["id"],),
                )
                return None
            membership = {
                "membership_id": str(row["membership_id"]),
                "tenant_id": str(row["tenant_id"]),
                "user_id": str(row["user_id"]),
            }
            _bind_identity_row(
                cur,
                membership=membership,
                line_user_id=line_user_id,
                display_name=display_name,
                picture_url=picture_url,
                friendship_ready=True,
            )
            cur.execute(
                "UPDATE cowork_line_connect_tokens SET used_at = NOW() WHERE id = %s",
                (row["id"],),
            )
            return membership
    except errors.UniqueViolation:
        raise CoworkLineIdentityError("line_conflict") from None


def _bind_identity_row(
    cur,
    *,
    membership: dict[str, str],
    line_user_id: str,
    display_name: str | None,
    picture_url: str | None,
    friendship_ready: bool,
) -> None:
    cur.execute(
        """
        SELECT membership_id, revoked_at
        FROM cowork_line_identities
        WHERE line_user_id = %s
        FOR UPDATE
        """,
        (line_user_id,),
    )
    owner = cur.fetchone()
    if owner and str(owner["membership_id"]) != membership["membership_id"]:
        if owner["revoked_at"] is None:
            raise CoworkLineIdentityError("line_conflict")
        cur.execute(
            "DELETE FROM cowork_line_identities "
            "WHERE line_user_id = %s AND revoked_at IS NOT NULL",
            (line_user_id,),
        )
    cur.execute(
        """
        INSERT INTO cowork_line_identities
            (membership_id, tenant_id, user_id, line_user_id, display_name,
             picture_url, friendship_ready, friendship_checked_at,
             connected_at, last_seen_at, revoked_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW(), NULL)
        ON CONFLICT (membership_id) DO UPDATE SET
            tenant_id = EXCLUDED.tenant_id,
            user_id = EXCLUDED.user_id,
            line_user_id = EXCLUDED.line_user_id,
            display_name = EXCLUDED.display_name,
            picture_url = EXCLUDED.picture_url,
            friendship_ready = EXCLUDED.friendship_ready,
            friendship_checked_at = NOW(),
            connected_at = NOW(),
            last_seen_at = NOW(),
            revoked_at = NULL
        """,
        (
            membership["membership_id"],
            membership["tenant_id"],
            membership["user_id"],
            line_user_id,
            display_name,
            picture_url,
            friendship_ready,
        ),
    )


def bind_identity(
    *,
    membership_id: str,
    tenant_id: str,
    user_id: str,
    line_user_id: str,
    display_name: str | None = None,
    picture_url: str | None = None,
    friendship_ready: bool = False,
) -> dict[str, Any]:
    if not line_user_id or not line_user_id.strip():
        raise CoworkLineIdentityError("invalid_line_user")
    line_user_id = line_user_id.strip()
    try:
        with db.get_cursor(commit=True) as cur:
            membership = _active_membership(cur, user_id=user_id, tenant_id=tenant_id)
            if membership["membership_id"] != str(membership_id):
                raise CoworkLineIdentityError("membership_inactive")
            _bind_identity_row(
                cur,
                membership=membership,
                line_user_id=line_user_id,
                display_name=display_name,
                picture_url=picture_url,
                friendship_ready=friendship_ready,
            )
    except errors.UniqueViolation:
        raise CoworkLineIdentityError("line_conflict") from None
    return {"success": True, "conflict": False, "code": None}


def get_identity_status(*, user_id: str, tenant_id: str) -> dict[str, Any]:
    with db.get_cursor() as cur:
        membership = _active_membership(cur, user_id=user_id, tenant_id=tenant_id)
        cur.execute(
            """
            SELECT display_name, connected_at, friendship_ready, friendship_checked_at
            FROM cowork_line_identities
            WHERE membership_id = %s AND revoked_at IS NULL
            """,
            (membership["membership_id"],),
        )
        row = cur.fetchone()
    if not row:
        return {
            "connected": False,
            "display_name": None,
            "connected_at": None,
            "friendship_ready": False,
            "friendship_checked_at": None,
        }
    timestamp = row["connected_at"]
    connected_at = timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp
    checked = row.get("friendship_checked_at")
    friendship_checked_at = checked.isoformat() if hasattr(checked, "isoformat") else checked
    return {
        "connected": True,
        "display_name": row["display_name"],
        "connected_at": connected_at,
        "friendship_ready": bool(row.get("friendship_ready")),
        "friendship_checked_at": friendship_checked_at,
    }


def unbind_identity(*, user_id: str, tenant_id: str) -> bool:
    with db.get_cursor(commit=True) as cur:
        membership = _active_membership(cur, user_id=user_id, tenant_id=tenant_id)
        cur.execute(
            """
            UPDATE cowork_line_identities
            SET revoked_at = NOW()
            WHERE membership_id = %s AND revoked_at IS NULL
            """,
            (membership["membership_id"],),
        )
        disconnected = cur.rowcount > 0
        cur.execute(
            """
            UPDATE cowork_line_connect_tokens
            SET used_at = NOW()
            WHERE membership_id = %s AND used_at IS NULL
            """,
            (membership["membership_id"],),
        )
    return disconnected


def resolve_active_identity(line_user_id: str) -> dict[str, str] | None:
    if not line_user_id:
        return None
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            SELECT i.membership_id, i.tenant_id, i.user_id
            FROM cowork_line_identities i
            JOIN memberships m ON m.id = i.membership_id
            JOIN users u ON u.id = i.user_id
            WHERE i.line_user_id = %s
              AND i.revoked_at IS NULL
              AND m.status = 'active'
              AND u.is_active = TRUE
            """,
            (line_user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            """
            UPDATE cowork_line_identities
            SET last_seen_at = NOW()
            WHERE membership_id = %s
            """,
            (row["membership_id"],),
        )
    return {
        "membership_id": str(row["membership_id"]),
        "tenant_id": str(row["tenant_id"]),
        "user_id": str(row["user_id"]),
        "line_user_id": line_user_id,
    }
