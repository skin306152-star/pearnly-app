"""WeKan-issued members use ordinary Pearnly employee accounts and passwords.

Only the trusted WeKan service calls this module, after native member-management
authorization. Board roles are deliberately absent from every Pearnly write.
"""

from __future__ import annotations

from fastapi import HTTPException
from psycopg2.errors import UniqueViolation

from core import db
from core.auth import hash_password
from core.route_helpers import _check_password_strength
from services.auth.account_provision import find_login_user, resolve_account_identifier
from services.authz.resolver import create_membership
from services.work_bridge.config import remote_username


def create_member(*, actor_id, request_id, account, email, password, display_name) -> dict:
    ident = resolve_account_identifier(account)
    email_ident = resolve_account_identifier(email) if email else None
    if email_ident and not email_ident["is_email"]:
        raise HTTPException(422, "work.email_invalid")
    if password:
        error = _check_password_strength(password)
        if error:
            raise HTTPException(422, error)
    else:
        import secrets

        password = secrets.token_urlsafe(32)
    pw_hash = hash_password(password)
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT u.tenant_id::text, u.company_name FROM users u "
                "JOIN tenants t ON t.id = u.tenant_id "
                "WHERE u.id = %s AND u.is_active = TRUE AND t.status = 'active' "
                "AND (u.expires_at IS NULL OR u.expires_at > now()) "
                "AND NOT EXISTS (SELECT 1 FROM memberships m WHERE m.user_id = u.id "
                "AND m.status <> 'active') FOR SHARE OF u, t",
                (actor_id,),
            )
            actor = cur.fetchone()
            if not actor:
                raise HTTPException(403, "work.actor_unavailable")
            tenant_id = actor["tenant_id"]
            # Serialize retries and concurrent creation of the same login identifier.
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (ident["lookup_key"],)
            )
            cur.execute(
                "SELECT user_id::text, account, email FROM work_bridge_member_requests "
                "WHERE tenant_id = %s AND request_id = %s AND actor_id = %s",
                (tenant_id, request_id, actor_id),
            )
            previous = cur.fetchone()
            if previous:
                if previous["account"] != ident["username"] or previous["email"] != email:
                    raise HTTPException(409, "work.request_conflict")
                return {"user_id": previous["user_id"], "tenant_id": tenant_id}
            if find_login_user(cur, ident["lookup_key"]) or (
                email_ident and find_login_user(cur, email_ident["lookup_key"])
            ):
                # Existing users are invited by identity; never merge or change their password.
                raise HTTPException(409, "work.account_exists")
            cur.execute(
                "INSERT INTO users (username, email, email_normalized, password_hash, "
                "plan, is_active, is_super_admin, tenant_id, role, company_name, invited_by, full_name) "
                "VALUES (%s, %s, %s, %s, 'credits', TRUE, FALSE, %s, 'member', %s, %s, %s) "
                "RETURNING id::text",
                (
                    ident["username"],
                    (email_ident or ident)["email"],
                    (email_ident or ident)["email_norm"],
                    pw_hash,
                    tenant_id,
                    actor.get("company_name"),
                    actor_id,
                    display_name or ident["username"],
                ),
            )
            user_id = cur.fetchone()["id"]
            if not create_membership(
                cur,
                user_id=user_id,
                tenant_id=tenant_id,
                role_key="accountant",
                granted_by=actor_id,
                allow_owner=False,
            ):
                raise HTTPException(503, "work.membership_unavailable")
            cur.execute(
                "INSERT INTO work_bridge_member_requests "
                "(tenant_id, request_id, actor_id, user_id, account, email) VALUES (%s,%s,%s,%s,%s,%s)",
                (tenant_id, request_id, actor_id, user_id, ident["username"], email),
            )
            return {"user_id": user_id, "tenant_id": tenant_id}
    except UniqueViolation:
        raise HTTPException(409, "work.account_exists") from None


def lookup(account: str) -> dict:
    ident = resolve_account_identifier(account)
    with db.get_cursor() as cur:
        row = find_login_user(cur, ident["lookup_key"])
        if not row:
            raise HTTPException(404, "work.account_not_found")
        cur.execute(
            "SELECT full_name, email FROM users WHERE id = %s AND is_active "
            "AND (expires_at IS NULL OR expires_at > now())",
            (row["id"],),
        )
        profile = cur.fetchone()
        if not profile:
            raise HTTPException(403, "work.account_unavailable")
        return {
            "user_id": row["id"],
            "tenant_id": row["tenant_id"],
            "account": row["username"],
            "username": remote_username(row["id"]),
            "display_name": profile["full_name"] or row["username"],
            "email": profile["email"],
            "is_platform_admin": bool(row["is_super_admin"]),
        }


def enroll(actor_id: str, user_id: str) -> dict:
    """Deliver Pearnly's existing password setup flow for a native WeKan invitation."""
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT r.user_id FROM work_bridge_member_requests r "
            "JOIN users actor ON actor.id = r.actor_id "
            "JOIN users member ON member.id = r.user_id "
            "JOIN tenants t ON t.id = r.tenant_id "
            "WHERE r.actor_id = %s AND r.user_id = %s AND actor.is_active "
            "AND member.is_active AND member.tenant_id = r.tenant_id "
            "AND actor.tenant_id = r.tenant_id AND t.status = 'active' "
            "AND (actor.expires_at IS NULL OR actor.expires_at > now()) "
            "AND (member.expires_at IS NULL OR member.expires_at > now()) "
            "AND NOT EXISTS (SELECT 1 FROM memberships m "
            "WHERE m.user_id IN (actor.id, member.id) AND m.status <> 'active')",
            (actor_id, user_id),
        )
        if not cur.fetchone():
            raise HTTPException(403, "work.invitation_not_allowed")
    from routes.auth_password_routes import send_reset_link_for_employee

    result = send_reset_link_for_employee(user_id, actor_username="WeKan")
    if not result.get("ok"):
        raise HTTPException(503, "work.invitation_delivery_failed")
    return {"ok": True}
