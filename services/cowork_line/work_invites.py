"""Same-tenant employee invitations and explicit account-to-LINE binding."""

import os
import hashlib
import hmac
import json
from urllib.parse import urlencode

from fastapi import HTTPException
from psycopg2 import errors

from core import db
from services.cowork_line import identity_store
from services.line_platform.liff import verify_id_token
from services.work_bridge import accounts, line_owner


def url(mode="connect", board=""):
    query = urlencode({"flow": "cowork-connect", "draft": mode, "board": board})
    liff = os.getenv("LINE_COWORK_LIFF_ID") or os.getenv("LINE_LIFF_ID")
    if not liff:
        return "https://pearnly.com/liff/cowork-connect?" + query
    return f"https://liff.line.me/{liff}/?{query}"


def claims(token):
    value = verify_id_token(token, "LINE_COWORK_LIFF_ID")
    if not value or not value.get("sub"):
        raise HTTPException(401, "work.line_identity_required")
    return value


def connect(user_id, tenant_id, token):
    profile = claims(token)
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT u.id FROM users u JOIN tenants t ON t.id=u.tenant_id WHERE u.id=%s AND t.id=%s AND t.status='active' AND u.is_active=TRUE AND (u.expires_at IS NULL OR u.expires_at>now()) FOR SHARE OF u,t",
                (user_id, tenant_id),
            )
            if not cur.fetchone():
                raise HTTPException(403, "cowork_line.membership_inactive")
            membership = identity_store._active_membership(
                cur, user_id=user_id, tenant_id=tenant_id
            )
            cur.execute(
                "SELECT id FROM memberships WHERE id=%s FOR UPDATE", (membership["membership_id"],)
            )
            cur.execute(
                "SELECT line_user_id FROM cowork_line_identities WHERE membership_id=%s AND revoked_at IS NULL FOR UPDATE",
                (membership["membership_id"],),
            )
            previous = cur.fetchone()
            if previous and previous["line_user_id"] != profile["sub"]:
                raise HTTPException(409, "cowork_line.already_connected")
            identity_store._bind_identity_row(
                cur,
                membership=membership,
                line_user_id=profile["sub"],
                display_name=profile.get("name"),
                picture_url=profile.get("picture"),
                friendship_ready=False,
            )
    except errors.UniqueViolation:
        raise HTTPException(409, "cowork_line.line_conflict") from None
    return {
        "connected": True,
        "bot_friend_url": os.getenv("LINE_BOT_FRIEND_URL") or "https://line.me/R/ti/p/@pearnly",
    }


def invite(token, request_id, account, password, display_name, board):
    profile = claims(token)
    identity = identity_store.resolve_active_identity(profile["sub"])
    if not identity:
        raise HTTPException(403, "work.owner_required")
    current = line_owner.owner(identity)
    line_owner.snapshot(identity, board)
    # The existing provisioner derives the tenant from users, so verify that
    # it agrees with the active LINE membership before any account is created.
    with db.get_cursor() as cur:
        cur.execute("SELECT tenant_id::text FROM users WHERE id=%s", (current["user_id"],))
        if cur.fetchone()["tenant_id"] != current["tenant_id"]:
            raise HTTPException(403, "work.tenant_mismatch")
    fingerprint = hmac.new(
        line_owner.service().secret.encode(),
        json.dumps([account, password, display_name, board]).encode(),
        hashlib.sha256,
    ).hexdigest()[:24]
    operation = request_id + "-" + fingerprint
    created = accounts.create_member(
        actor_id=current["user_id"],
        request_id=operation,
        account=account,
        email=None,
        password=password,
        display_name=display_name,
    )
    member = next(x for x in line_owner.team(identity) if x["user_id"] == created["user_id"])
    line_owner.request(
        identity,
        "POST",
        f"/_pearnly/line/member/{board}",
        {"member": member},
        operation=operation + "-member",
    )
    return {"account": account, "connect_url": url(), "user_id": created["user_id"]}


def connect_message():
    return {
        "type": "text",
        "text": "เชื่อมต่อบัญชีพนักงานด้วยบัญชีและรหัสผ่านที่ได้รับจากผู้เชิญครับ",
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {"type": "uri", "label": "เชื่อมต่อบัญชี", "uri": url()},
                }
            ]
        },
    }
