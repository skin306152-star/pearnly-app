"""Fresh owner authorization and signed access to the native work service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

import httpx
from fastapi import HTTPException

from core import db
from services.work_bridge.config import remote_username, service


def actor(identity: dict) -> dict:
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT u.id::text AS user_id, u.username, u.full_name, u.email, "
            "m.tenant_id::text, r.key AS role_key FROM memberships m "
            "JOIN users u ON u.id=m.user_id JOIN roles r ON r.id=m.role_id "
            "JOIN tenants t ON t.id=m.tenant_id "
            "JOIN cowork_line_identities i ON i.membership_id=m.id "
            "WHERE m.id=%s AND m.tenant_id=%s AND m.user_id=%s "
            "AND i.line_user_id=%s AND i.revoked_at IS NULL "
            "AND m.status='active' AND u.is_active=TRUE "
            "AND t.status='active' AND (u.expires_at IS NULL OR u.expires_at>now())",
            (
                identity["membership_id"],
                identity["tenant_id"],
                identity["user_id"],
                identity["line_user_id"],
            ),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(403, "work.owner_required")
    return {
        "user_id": row["user_id"],
        "tenant_id": row["tenant_id"],
        "username": remote_username(row["user_id"]),
        "display_name": row.get("full_name") or row["username"],
        "email": row.get("email"),
        "is_platform_admin": False,
        "work_role": "owner" if row["role_key"] == "owner" else "employee",
        "work_readonly": row["role_key"] == "viewer",
        "line_binding": {
            k: identity[k] for k in ("membership_id", "tenant_id", "user_id", "line_user_id")
        },
    }


def owner(identity: dict) -> dict:
    current = actor(identity)
    if current["work_role"] != "owner":
        raise HTTPException(403, "work.owner_required")
    return current


def file_url(identity, board, card, file):
    target = service()
    current = actor(identity)
    path = f"/_pearnly/line/file/{board}/{card}/{file}"
    envelope = base64.urlsafe_b64encode(
        json.dumps(
            {
                "identity": {
                    "user_id": current["user_id"],
                    "tenant_id": current["tenant_id"],
                    "is_platform_admin": False,
                    "work_role": current["work_role"],
                    "line_binding": {k: identity[k] for k in ("membership_id", "line_user_id")},
                },
                "expires": int(time.time()) + 300,
                "method": "GET",
                "path": path,
                "body": hashlib.sha256(b"").hexdigest(),
            },
            separators=(",", ":"),
        ).encode()
    ).decode()
    signature = hmac.new(target.secret.encode(), envelope.encode(), hashlib.sha256).hexdigest()
    return target.url + path + "?ticket=" + envelope + "&signature=" + signature


def request(identity, method, path, body=None, *, operation=""):
    current = actor(identity)
    target = service()
    raw = json.dumps(body, ensure_ascii=False).encode() if body is not None else b""
    allowed_lists = []
    allowed_sources = []
    if current["work_role"] == "employee" and method != "GET":
        from services.cowork_line.work_store import board_mapping

        parts = path.split("/")
        board = parts[4] if parts[3] == "attachments" else (parts[5] if len(parts) > 5 else "")
        if not board:
            raise HTTPException(403, "work.employee_action")
        mapping = board_mapping(identity, board)
        allowed_sources = [
            mapping[key] for key in ("pending", "doing", "blocked", "review") if mapping.get(key)
        ]
        allowed_lists = [mapping[key] for key in ("doing", "blocked", "review") if mapping.get(key)]
    envelope = base64.urlsafe_b64encode(
        json.dumps(
            {
                "identity": current,
                "allowed_lists": allowed_lists,
                "allowed_sources": allowed_sources,
                "expires": int(time.time()) + 60,
                "method": method,
                "path": path,
                "operation": operation,
                "body": hashlib.sha256(raw).hexdigest(),
            },
            separators=(",", ":"),
        ).encode()
    ).decode()
    signature = hmac.new(target.secret.encode(), envelope.encode(), hashlib.sha256).hexdigest()
    with httpx.Client(timeout=25, follow_redirects=False) as client:
        response = client.request(
            method,
            target.url + path,
            content=raw,
            headers={
                "Content-Type": "application/json",
                "X-Pearnly-Line": envelope,
                "X-Pearnly-Line-Signature": signature,
            },
        )
    if response.status_code >= 400:
        raise HTTPException(response.status_code, "work.remote_failed")
    data = response.json()
    if isinstance(data, dict) and (data.get("error") or data.get("errorType")):
        raise HTTPException(409, "work.remote_failed")
    return data


def snapshot(identity, board=""):
    return request(identity, "GET", "/_pearnly/line/context" + ("/" + board if board else ""))


def team(identity):
    owner(identity)
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT u.id::text AS user_id, u.username, u.full_name, u.email "
            "FROM memberships m JOIN users u ON u.id=m.user_id "
            "WHERE m.tenant_id=%s AND m.status='active' AND u.is_active=TRUE "
            "AND (u.expires_at IS NULL OR u.expires_at>now()) ORDER BY u.username LIMIT 201",
            (identity["tenant_id"],),
        )
        rows = cur.fetchall()
    if len(rows) > 200:
        raise HTTPException(422, "work.limit")
    return [
        {
            "user_id": row["user_id"],
            "tenant_id": identity["tenant_id"],
            "username": remote_username(row["user_id"]),
            "display_name": row.get("full_name") or row["username"],
            "email": row.get("email"),
            "is_platform_admin": False,
        }
        for row in rows
    ]


def mutate(identity, method, path, body, operation):
    return request(identity, method, "/_pearnly/line" + path, body, operation=operation)
