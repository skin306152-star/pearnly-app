"""Atomic, browser-bound handoffs and fresh validation of the parent COWORK session."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException

from core import db
from services.work_bridge.config import remote_username, service


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def issue(user: dict, claims: dict, browser_state: str) -> dict:
    target = service()
    tenant_id = str(user.get("tenant_id") or "") or None
    if not claims.get("jti") or claims.get("sub") != str(user["id"]):
        raise HTTPException(401, "auth.invalid_token")
    session = secrets.token_urlsafe(32)
    ticket = secrets.token_urlsafe(32)
    expiry = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc)
    with db.get_cursor(commit=True) as cur:
        # Bounded opportunistic expiry cleanup; no per-instance background job.
        cur.execute(
            "DELETE FROM work_bridge_tickets WHERE ticket_hash IN "
            "(SELECT ticket_hash FROM work_bridge_tickets WHERE expires_at < now() LIMIT 100)"
        )
        cur.execute(
            "DELETE FROM work_bridge_sessions WHERE session_hash IN "
            "(SELECT session_hash FROM work_bridge_sessions WHERE expires_at < now() LIMIT 100)"
        )
        cur.execute(
            "INSERT INTO work_bridge_sessions "
            "(session_hash, tenant_id, user_id, parent_jti, parent_iat, expires_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (digest(session), tenant_id, user["id"], claims["jti"], claims["iat"], expiry),
        )
        cur.execute(
            "INSERT INTO work_bridge_tickets "
            "(ticket_hash, tenant_id, session_hash, browser_state, expires_at) "
            "VALUES (%s, %s, %s, %s, now() + interval '60 seconds')",
            (digest(ticket), tenant_id, digest(session), browser_state),
        )
    # Only the trusted service receives the opaque handle after a successful consume.
    return {"ticket": ticket, "consume_url": target.url + "/_pearnly/consume"}


def consume(ticket: str, browser_state: str) -> dict:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM work_bridge_tickets WHERE ticket_hash = %s "
            "AND browser_state = %s AND expires_at > now() RETURNING session_hash",
            (digest(ticket), browser_state),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(401, "work.ticket_invalid")
    identity = validate(row["session_hash"])
    return {**identity, "session": row["session_hash"]}


def validate(session_hash: str) -> dict:
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT s.user_id::text, s.tenant_id::text, s.parent_jti, s.parent_iat, s.expires_at, "
            "u.username, u.full_name, u.email, u.is_active, u.is_super_admin, u.active_jti, "
            "u.password_changed_at, "
            "u.expires_at AS account_expires_at, u.tenant_id::text AS home_tenant_id, "
            "COALESCE(u.active_tenant_id, u.tenant_id)::text AS active_tenant_id, "
            "COALESCE(t.status, 'active') AS tenant_status, m.status AS member_status "
            "FROM work_bridge_sessions s JOIN users u ON u.id = s.user_id "
            "LEFT JOIN tenants t ON t.id = s.tenant_id "
            "LEFT JOIN memberships m ON m.user_id = u.id AND m.tenant_id = s.tenant_id "
            "WHERE s.session_hash = %s "
            "AND s.revoked_at IS NULL AND s.expires_at > now()",
            (session_hash,),
        )
        row = cur.fetchone()
    if not row or not identity_valid(row):
        raise HTTPException(401, "work.session_expired")
    return {
        "user_id": row["user_id"],
        "username": remote_username(row["user_id"]),
        "display_name": row.get("full_name") or row["username"],
        "email": row.get("email"),
        "tenant_id": row["tenant_id"],
        "is_platform_admin": bool(row.get("is_super_admin")),
        "expires_at": row["expires_at"].isoformat(),
    }


def identity_valid(row: dict) -> bool:
    now = datetime.now(timezone.utc)
    changed = row.get("password_changed_at")
    return bool(
        row.get("is_active")
        and row.get("active_jti")
        and row["active_jti"] == row["parent_jti"]
        and row["active_tenant_id"] == row["tenant_id"]
        and row.get("tenant_status") == "active"
        and row.get("member_status") in (None, "active")
        and (not changed or int(changed.timestamp()) <= row["parent_iat"])
        and (not row.get("account_expires_at") or row["account_expires_at"] > now)
    )


def revoke(session_hash: str) -> None:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE work_bridge_sessions SET revoked_at = now() " "WHERE session_hash = %s",
            (session_hash,),
        )
